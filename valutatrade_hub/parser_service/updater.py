import logging
from typing import Dict, Optional, Tuple
import datetime

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient
)
from valutatrade_hub.parser_service.storage import StorageManager


class RatesUpdater:
    """Координатор обновления курсов валют."""
    
    def __init__(
        self,
        config: Optional[ParserConfig] = None,
        storage: Optional[StorageManager] = None
    ):
        """
        Инициализация обновлятеля курсов.
        
        Args:
            config: конфигурация парсера (если None, загружается из настроек)
            storage: менеджер хранилища (если None, создается новый)
        """
        self.config = config or ParserConfig.from_settings()
        self.storage = storage or StorageManager(
            rates_file_path=self.config.RATES_FILE_PATH,
            history_file_path=self.config.HISTORY_FILE_PATH
        )
        
        # Инициализируем клиентов API
        self.clients = {
            "coingecko": CoinGeckoClient(self.config),
            "exchangerate": ExchangeRateApiClient(self.config)
        }
        
        # Настраиваем логирование
        self.logger = logging.getLogger(__name__)
    
    def run_update(self, sources: Optional[list] = None) -> Dict[str, int]:
        """Запустить обновление курсов из указанных источников.
        
        Args:
            sources: список источников для обновления 
                     (если None, обновляются все доступные)
                     допустимые значения: ["coingecko", "exchangerate"]
                     
        Returns:
            Словарь с результатами обновления по каждому источнику:
                {"coingecko": количество_курсов, "exchangerate": количество_курсов}
        """
        if sources is None:
            sources = list(self.clients.keys())
        
        self.logger.info("Starting rates update from sources: %s", sources)
        
        results = {}
        all_rates = {}
        
        # Проходим по каждому указанному источнику
        for source_name in sources:
            if source_name not in self.clients:
                self.logger.warning("Unknown source: %s, skipping", source_name)
                continue
            
            client = self.clients[source_name]
            
            try:
                self.logger.info("Fetching rates from %s...", source_name)
                
                # Получаем курсы от клиента
                rates = client.fetch_rates()
                results[source_name] = len(rates)
                
                # Добавляем к общим курсам
                all_rates.update(rates)
                
                # Сохраняем в историю
                self.storage.save_to_history(rates, source_name.capitalize())
                
                self.logger.info(
                    "Successfully fetched %d rates from %s",
                    len(rates),
                    source_name
                )
                
            except ApiRequestError as e:
                self.logger.error(
                    "Failed to fetch rates from %s: %s",
                    source_name,
                    str(e)
                )
                results[source_name] = 0
            except Exception as e:
                self.logger.exception(
                    "Unexpected error while fetching from %s: %s",
                    source_name,
                    str(e)
                )
                results[source_name] = 0
        
        # Если есть какие-то курсы, сохраняем их как актуальные
        if all_rates:
            # Определяем основной источник для подписи
            main_source = "Multiple Sources"
            if len(sources) == 1:
                main_source = sources[0].capitalize()
            
            self.storage.save_rates(all_rates, main_source)
            
            self.logger.info(
                "Update completed. Total rates updated: %d from %d source(s)",
                len(all_rates),
                sum(1 for v in results.values() if v > 0)
            )
        else:
            self.logger.warning("No rates were updated from any source")
        
        return results
    
    def get_update_summary(self) -> Dict[str, any]:
        """Получить сводку о последнем обновлении.
        
        Returns:
            Словарь со сводкой об обновлении
        """
        rates_data = self.storage.load_rates()
        
        return {
            "last_refresh": rates_data.get("last_refresh"),
            "total_pairs": len(rates_data.get("pairs", {})),
            "sources_used": list(set(
                pair_data.get("source", "Unknown")
                for pair_data in rates_data.get("pairs", {}).values()
            ))
        }
    
    def check_freshness(self) -> Tuple[bool, Optional[str]]:
        """Проверка свежести данных в кэше.
        
        Returns:
            Кортеж (is_fresh, message)
            - is_fresh: True если данные свежие
            - message: сообщение о состоянии данных
        """
        rates_data = self.storage.load_rates()
        last_refresh = rates_data.get("last_refresh")
        
        if not last_refresh:
            return False, "Данные отсутствуют в кэше"
        
        try:
            # Парсим время последнего обновления
            # Убираем 'Z' и добавляем '+00:00' для правильного парсинга
            if last_refresh.endswith('Z'):
                last_refresh = last_refresh[:-1] + '+00:00'
            
            last_update = datetime.datetime.fromisoformat(last_refresh)
            now = datetime.datetime.now(datetime.timezone.utc)
            
            # Вычисляем разницу в секундах
            delta_seconds = (now - last_update).total_seconds()
            
            if delta_seconds > self.config.rates_ttl_seconds:
                return False, (
                    f"Данные устарели ({int(delta_seconds/60)} мин назад). "
                    f"TTL: {self.config.rates_ttl_seconds} сек"
                )
            else:
                return True, (
                    f"Данные свежие ({int(delta_seconds)} сек назад). "
                    f"TTL: {self.config.rates_ttl_seconds} сек"
                )
                
        except Exception as e:
            self.logger.error("Error parsing timestamp %s: %s", last_refresh, e)
            return False, f"Ошибка формата времени: {last_refresh}"
