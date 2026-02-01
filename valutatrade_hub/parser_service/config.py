import os
from dataclasses import dataclass, field
from typing import Tuple, Dict

from dotenv import load_dotenv

load_dotenv()


@dataclass
class ParserConfig:
    """Конфигурация парсер-сервиса."""
    
    # API ключи (загружаются из переменных окружения)
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    
    # Эндпоинты API
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    
    # Базовая валюта
    BASE_CURRENCY: str = "USD"
    
    # TTL кэша курсов (в секундах)
    rates_ttl_seconds: int = 300
    
    # Списки валют (используем field для списков и словарей)
    FIAT_CURRENCIES: Tuple[str, ...] = field(default=("EUR", "GBP", "RUB", "JPY", "CNY"))
    CRYPTO_CURRENCIES: Tuple[str, ...] = field(default=("BTC", "ETH", "SOL", "BNB", "ADA"))
    
    # Сопоставление кодов криптовалют с их ID в CoinGecko
    CRYPTO_ID_MAP: Dict[str, str] = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum", 
        "SOL": "solana",
        "BNB": "binancecoin",
        "ADA": "cardano",
    })
    
    # Пути к файлам данных
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"
    
    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10
    
    def validate(self) -> None:
        """Проверка валидности конфигурации."""
        if not self.EXCHANGERATE_API_KEY:
            raise ValueError(
                "EXCHANGERATE_API_KEY не установлен. "
                "Добавьте его в файл .env или переменные окружения."
            )
        
        if not all(currency in self.CRYPTO_ID_MAP 
                   for currency in self.CRYPTO_CURRENCIES):
            raise ValueError("Не все криптовалюты имеют сопоставление в CRYPTO_ID_MAP")
    
    @classmethod
    def from_settings(cls) -> "ParserConfig":
        """Создает конфигурацию из настроек приложения."""
        # Импортируем здесь, чтобы избежать циклического импорта
        try:
            from valutatrade_hub.infra.settings import SettingsLoader
            settings = SettingsLoader()
            
            return cls(
                FIAT_CURRENCIES=tuple(settings.get("parser.fiat_currencies", 
                                                  ["EUR", "GBP", "RUB", "JPY", "CNY"])),
                CRYPTO_CURRENCIES=tuple(settings.get("parser.crypto_currencies", 
                                                    ["BTC", "ETH", "SOL", "BNB", "ADA"])),
                REQUEST_TIMEOUT=settings.get("parser.request_timeout", 10),
                RATES_FILE_PATH=settings.get("data_dir", "data") + "/rates.json",
                HISTORY_FILE_PATH=settings.get("data_dir", "data") + "/exchange_rates.json",
                rates_ttl_seconds=settings.get("rates_ttl_seconds", 300),
            )
        except ImportError:
            # Если SettingsLoader не доступен, используем значения по умолчанию
            return cls()
