import requests
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API-клиентов."""
    
    def __init__(self, config: ParserConfig):
        self.config = config
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы валют от API.
        
        Returns:
            Словарь с парами валют и курсами, например: {"BTC_USD": 59337.21}
        
        Raises:
            ApiRequestError: при ошибке запроса к API
        """
        pass
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполнить HTTP-запрос с обработкой ошибок.
        
        Args:
            url: URL для запроса
            params: параметры запроса
            
        Returns:
            Ответ API в виде словаря
            
        Raises:
            ApiRequestError: при ошибке сети или неверном статус-коде
        """
        try:
            response = requests.get(
                url, 
                params=params, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise ApiRequestError(f"Таймаут запроса к {url}")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError(f"Ошибка подключения к {url}")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                raise ApiRequestError("Превышен лимит запросов к API")
            elif response.status_code == 401:
                raise ApiRequestError("Неверный API-ключ")
            else:
                raise ApiRequestError(f"HTTP ошибка {response.status_code}: {str(e)}")
        except Exception as e:
            raise ApiRequestError(f"Неизвестная ошибка: {str(e)}")


class CoinGeckoClient(BaseApiClient):
    """Клиент для работы с CoinGecko API."""
    
    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы криптовалют к USD."""
        # Формируем список ID криптовалют
        crypto_ids = [
            self.config.CRYPTO_ID_MAP[currency] 
            for currency in self.config.CRYPTO_CURRENCIES
            if currency in self.config.CRYPTO_ID_MAP
        ]
        
        if not crypto_ids:
            return {}
        
        # Параметры запроса
        params = {
            "ids": ",".join(crypto_ids),
            "vs_currencies": "usd"
        }
        
        # Выполняем запрос
        data = self._make_request(self.config.COINGECKO_URL, params)
        
        # Преобразуем ответ в единый формат
        rates = {}
        for crypto_id, rates_dict in data.items():
            # Находим код валюты по ID
            currency_code = next(
                (code for code, cid in self.config.CRYPTO_ID_MAP.items() 
                 if cid == crypto_id),
                None
            )
            
            if currency_code and "usd" in rates_dict:
                pair_name = f"{currency_code}_{self.config.BASE_CURRENCY}"
                rates[pair_name] = float(rates_dict["usd"])
        
        return rates


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для работы с ExchangeRate-API."""
    
    # Мок-данные для фиатных валют (примерные курсы)
    MOCK_FIAT_RATES = {
        "EUR_USD": 1.0821,
        "GBP_USD": 1.2628,
        "JPY_USD": 0.0067,
        "CAD_USD": 0.7412,
        "AUD_USD": 0.6589,
        "CHF_USD": 1.1284,
        "CNY_USD": 0.1389,
        "RUB_USD": 0.0108,
    }
    
    def __init__(self, config: ParserConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы фиатных валют к USD."""
        try:
            # Формируем URL с API ключом
            url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
            
            # Выполняем запрос
            data = self._make_request(url)
            
            if data.get("result") != "success":
                self.logger.warning(f"ExchangeRate-API вернул ошибку: {data.get('error-type', 'unknown')}, использую мок-данные")
                return self.MOCK_FIAT_RATES
            
            # Преобразуем ответ в единый формат
            rates = {}
            base_currency = data.get("base_code", self.config.BASE_CURRENCY)
            
            for currency, rate in data.get("rates", {}).items():
                if currency in self.config.FIAT_CURRENCIES and currency != base_currency:
                    pair_name = f"{currency}_{base_currency}"
                    rates[pair_name] = float(rate)
            
            # Если получили хотя бы один курс, возвращаем их
            if rates:
                self.logger.info(f"Получено {len(rates)} курсов от ExchangeRate-API")
                return rates
            else:
                self.logger.warning("ExchangeRate-API вернул пустой список курсов, использую мок-данные")
                return self.MOCK_FIAT_RATES
                
        except Exception as e:
            self.logger.error(f"Ошибка при запросе к ExchangeRate-API: {e}, использую мок-данные")
            return self.MOCK_FIAT_RATES
