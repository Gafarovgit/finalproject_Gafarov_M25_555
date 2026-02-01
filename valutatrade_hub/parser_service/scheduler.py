# valutatrade_hub/parser_service/scheduler.py
import threading
import time
import logging
from typing import Optional
from datetime import datetime

from valutatrade_hub.parser_service.updater import RatesUpdater


class Scheduler:
    """Планировщик периодического обновления курсов."""
    
    def __init__(
        self, 
        updater: RatesUpdater,
        interval_minutes: int = 5,
        auto_start: bool = False
    ):
        """
        Инициализация планировщика.
        
        Args:
            updater: экземпляр RatesUpdater для обновления курсов
            interval_minutes: интервал обновления в минутах
            auto_start: запустить планировщик автоматически
        """
        self.updater = updater
        self.interval_seconds = interval_minutes * 60
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        self.logger = logging.getLogger(__name__)
        
        if auto_start:
            self.start()
    
    def _run(self) -> None:
        """Основной цикл планировщика."""
        self.logger.info(
            "Scheduler started. Update interval: %d minutes",
            self.interval_seconds // 60
        )
        
        while not self.stop_event.is_set():
            try:
                # Выполняем обновление
                self.logger.debug("Running scheduled update...")
                start_time = time.time()
                
                results = self.updater.run_update()
                
                duration = time.time() - start_time
                self.logger.info(
                    "Scheduled update completed in %.2f seconds. Results: %s",
                    duration,
                    results
                )
                
                # Записыем время следующего обновления
                next_update = datetime.fromtimestamp(
                    time.time() + self.interval_seconds
                ).strftime("%H:%M:%S")
                self.logger.debug("Next update at: %s", next_update)
                
            except Exception as e:
                self.logger.error("Error in scheduled update: %s", str(e))
            
            # Ждем указанный интервал (с проверкой остановки каждую секунду)
            for _ in range(self.interval_seconds):
                if self.stop_event.is_set():
                    break
                time.sleep(1)
        
        self.logger.info("Scheduler stopped")
    
    def start(self) -> None:
        """Запустить планировщик."""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        
        self.thread = threading.Thread(
            target=self._run,
            name="RatesUpdaterScheduler",
            daemon=True
        )
        self.thread.start()
        
        self.logger.info("Scheduler started successfully")
    
    def stop(self) -> None:
        """Остановить планировщик."""
        if not self.is_running:
            self.logger.warning("Scheduler is not running")
            return
        
        self.logger.info("Stopping scheduler...")
        self.stop_event.set()
        self.is_running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
            if self.thread.is_alive():
                self.logger.warning("Scheduler thread did not stop gracefully")
            else:
                self.logger.info("Scheduler stopped gracefully")
    
    def status(self) -> dict:
        """Получить статус планировщика.
        
        Returns:
            Словарь со статусом планировщика
        """
        return {
            "is_running": self.is_running,
            "interval_minutes": self.interval_seconds // 60,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }
    
    def change_interval(self, interval_minutes: int) -> None:
        """Изменить интервал обновления.
        
        Args:
            interval_minutes: новый интервал в минутах
        """
        if interval_minutes < 1:
            raise ValueError("Interval must be at least 1 minute")
        
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        self.interval_seconds = interval_minutes * 60
        self.logger.info("Update interval changed to %d minutes", interval_minutes)
        
        if was_running:
            self.start()
    
    def __enter__(self):
        """Контекстный менеджер для запуска планировщика."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Остановка планировщика при выходе из контекста."""
        self.stop()


class OneTimeScheduler:
    """Планировщик для однократного отложенного выполнения."""
    
    def __init__(self, updater: RatesUpdater, delay_seconds: int):
        """
        Инициализация однократного планировщика.
        
        Args:
            updater: экземпляр RatesUpdater
            delay_seconds: задержка в секундах
        """
        self.updater = updater
        self.delay_seconds = delay_seconds
        self.timer: Optional[threading.Timer] = None
        self.logger = logging.getLogger(__name__)
    
    def schedule_update(self) -> None:
        """Запланировать однократное обновление."""
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        
        self.timer = threading.Timer(self.delay_seconds, self._execute_update)
        self.timer.name = "OneTimeUpdateScheduler"
        self.timer.start()
        
        scheduled_time = datetime.fromtimestamp(
            time.time() + self.delay_seconds
        ).strftime("%H:%M:%S")
        
        self.logger.info(
            "One-time update scheduled in %d seconds (at %s)",
            self.delay_seconds,
            scheduled_time
        )
    
    def _execute_update(self) -> None:
        """Выполнить запланированное обновление."""
        try:
            self.logger.info("Executing scheduled one-time update...")
            self.updater.run_update()
        except Exception as e:
            self.logger.error("Error in scheduled update: %s", str(e))
    
    def cancel(self) -> None:
        """Отменить запланированное обновление."""
        if self.timer:
            self.timer.cancel()
            self.logger.info("Scheduled update cancelled")