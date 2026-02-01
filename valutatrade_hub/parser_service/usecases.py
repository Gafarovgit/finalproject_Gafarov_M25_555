# valutatrade_hub/parser_service/usecases.py
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from valutatrade_hub.core.exceptions import ApiRequestError, CurrencyNotFoundError
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.parser_service.storage import StorageManager
from valutatrade_hub.core.currencies import get_currency


class ParserUseCases:
    """Сценарии использования парсер-сервиса."""
    
    def __init__(self):
        """Инициализация сценариев использования."""
        self.config = ParserConfig.from_settings()
        self.storage = StorageManager(
            rates_file_path=self.config.RATES_FILE_PATH,
            history_file_path=self.config.HISTORY_FILE_PATH
        )
        self.updater = RatesUpdater(config=self.config, storage=self.storage)
        self.logger = logging.getLogger(__name__)
    
    def update_rates(self, source: Optional[str] = None) -> Dict[str, any]:
        """Обновить курсы валют.
        
        Args:
            source: источник для обновления (coingecko, exchangerate или None для всех)
            
        Returns:
            Словарь с результатами обновления
            
        Raises:
            ApiRequestError: при ошибке обращения к API
        """
        self.logger.info("Starting rates update%s", f" from {source}" if source else "")
        
        sources = [source] if source else None
        results = self.updater.run_update(sources)
        
        summary = self.updater.get_update_summary()
        
        return {
            "success": sum(results.values()) > 0,
            "results": results,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def show_rates(
        self,
        currency: Optional[str] = None,
        top: Optional[int] = None,
        base: str = "USD"
    ) -> Dict[str, any]:
        """Показать курсы валют с возможностью фильтрации.
        
        Args:
            currency: код валюты для фильтрации
            top: количество топовых криптовалют по курсу
            base: базовая валюта для отображения
            
        Returns:
            Словарь с отфильтрованными курсами и метаданными
        """
        rates = self.storage.get_latest_rates()
        
        if not rates:
            return {
                "rates": {},
                "last_refresh": None,
                "message": "Кэш курсов пуст. Выполните 'update-rates' для загрузки данных.",
                "total": 0,
                "base_currency": base.upper()
            }
        
        # Фильтруем по валюте, если указана
        filtered_rates = {}
        if currency:
            # Проверяем существование валюты
            try:
                get_currency(currency.upper())
            except CurrencyNotFoundError:
                raise CurrencyNotFoundError(currency.upper())
            
            # Ищем все пары с этой валютой
            for pair, data in rates.items():
                from_curr, to_curr = pair.split("_")
                if from_curr == currency.upper() or to_curr == currency.upper():
                    filtered_rates[pair] = data
        else:
            filtered_rates = rates
        
        # Сортируем курсы (по коду валюты или по значению курса)
        sorted_items = sorted(
            filtered_rates.items(),
            key=lambda x: x[1]["rate"],
            reverse=True  # Самые дорогие сверху
        )
        
        # Ограничиваем по top, если указан
        if top and top > 0:
            sorted_items = sorted_items[:top]
        
        # Форматируем для вывода
        formatted_rates = {}
        for pair, data in sorted_items:
            formatted_rates[pair] = {
                "rate": data["rate"],
                "updated_at": data["updated_at"],
                "source": data["source"],
                "formatted_rate": f"{data['rate']:,.4f}"
            }
        
        return {
            "rates": formatted_rates,
            "total": len(formatted_rates),
            "last_refresh": self.storage.load_rates().get("last_refresh"),
            "base_currency": base.upper()
        }
    
    def get_rate(self, from_currency: str, to_currency: str) -> Dict[str, any]:
        """Получить курс для конкретной пары валют.
        
        Args:
            from_currency: исходная валюта
            to_currency: целевая валюта
            
        Returns:
            Словарь с данными курса
            
        Raises:
            CurrencyNotFoundError: если валюта не найдена
        """
        # Проверяем существование валют
        get_currency(from_currency.upper())
        get_currency(to_currency.upper())
        
        pair = f"{from_currency.upper()}_{to_currency.upper()}"
        rate_data = self.storage.get_rate(pair)
        
        if not rate_data:
            # Пробуем обратную пару
            reverse_pair = f"{to_currency.upper()}_{from_currency.upper()}"
            reverse_data = self.storage.get_rate(reverse_pair)
            
            if reverse_data:
                # Вычисляем обратный курс
                rate_data = {
                    "rate": 1 / reverse_data["rate"],
                    "updated_at": reverse_data["updated_at"],
                    "source": reverse_data["source"],
                    "is_inverse": True
                }
        
        if not rate_data:
            raise ApiRequestError(
                f"Курс {pair} не найден в кэше. "
                f"Попробуйте выполнить 'update-rates' для загрузки данных."
            )
        
        # Проверяем свежесть данных простым способом
        is_fresh = True
        try:
            if rate_data["updated_at"]:
                # Простая проверка: если дата старше 10 минут, считаем устаревшей
                updated_str = rate_data["updated_at"]
                if updated_str.endswith('Z'):
                    updated_str = updated_str[:-1] + '+00:00'
                
                last_update = datetime.fromisoformat(updated_str)
                now = datetime.now(datetime.timezone.utc)
                delta_seconds = (now - last_update).total_seconds()
                
                if delta_seconds > 600:  # 10 минут
                    is_fresh = False
        except Exception:
            # Если не удалось проверить, считаем данные свежими
            pass
        
        return {
            "pair": pair,
            "rate": rate_data["rate"],
            "updated_at": rate_data["updated_at"],
            "source": rate_data.get("source", "Unknown"),
            "inverse_rate": 1 / rate_data["rate"] if rate_data["rate"] != 0 else 0,
            "is_fresh": is_fresh
        }
