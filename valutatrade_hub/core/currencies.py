"""
Иерархия классов валют с использованием наследования и полиморфизма.
"""

from abc import ABC, abstractmethod


class Currency(ABC):
    """
    Абстрактный базовый класс для представления валюты.
    
    Атрибуты:
        name (str): Человекочитаемое имя валюты.
        code (str): Код валюты (ISO или тикер).
    """

    def __init__(self, name: str, code: str):
        """
        Инициализирует объект валюты.
        
        Аргументы:
            name: Человекочитаемое имя валюты.
            code: Код валюты (2-5 символов, верхний регистр).
            
        Исключения:
            ValueError: Если код не соответствует требованиям.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Название валюты не может быть пустым")

        if not code or not isinstance(code, str):
            raise ValueError("Код валюты не может быть пустым")

        code = code.strip().upper()
        if not 2 <= len(code) <= 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")
        if not code.isalnum():
            raise ValueError("Код валюты должен содержать только буквы и цифры")

        self._name = name
        self._code = code

    @property
    def name(self) -> str:
        """Возвращает название валюты."""
        return self._name

    @property
    def code(self) -> str:
        """Возвращает код валюты."""
        return self._code

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает строковое представление валюты для UI/логов.
        
        Возвращает:
            Строка с информацией о валюте.
        """
        pass

    def __str__(self) -> str:
        """Строковое представление объекта."""
        return self.get_display_info()

    def __repr__(self) -> str:
        """Представление объекта для отладки."""
        return f"{self.__class__.__name__}(name='{self.name}', code='{self.code}')"


class FiatCurrency(Currency):
    """
    Класс для представления фиатных (традиционных) валют.
    
    Атрибуты:
        issuing_country (str): Страна или зона эмиссии.
    """

    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализирует объект фиатной валюты.
        
        Аргументы:
            name: Название валюты.
            code: Код валюты.
            issuing_country: Страна или зона эмиссии.
        """
        super().__init__(name, code)
        self._issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        """Возвращает страну эмиссии."""
        return self._issuing_country

    def get_display_info(self) -> str:
        """
        Возвращает информацию о фиатной валюте.
        
        Возвращает:
            Строка в формате: "[FIAT] КОД — Название (Страна эмиссии)"
        """
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """
    Класс для представления криптовалют.
    
    Атрибуты:
        algorithm (str): Алгоритм консенсуса или хеширования.
        market_cap (float): Рыночная капитализация.
    """

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        """
        Инициализирует объект криптовалюты.
        
        Аргументы:
            name: Название криптовалюты.
            code: Код криптовалюты.
            algorithm: Алгоритм (например, SHA-256).
            market_cap: Рыночная капитализация (по умолчанию 0).
        """
        super().__init__(name, code)
        self._algorithm = algorithm
        self._market_cap = float(market_cap)

    @property
    def algorithm(self) -> str:
        """Возвращает алгоритм криптовалюты."""
        return self._algorithm

    @property
    def market_cap(self) -> float:
        """Возвращает рыночную капитализацию."""
        return self._market_cap

    def get_display_info(self) -> str:
        """
        Возвращает информацию о криптовалюте.
        
        Возвращает:
            Строка в формате: "[CRYPTO] КОД — Название (Алгоритм, Капитализация)"
        """
        mcap_str = f"{self.market_cap:.2e}" if self.market_cap > 1e6 else f"{self.market_cap:,.2f}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


# Реестр поддерживаемых валют
_CURRENCY_REGISTRY = {
    # Фиатные валюты
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),

    # Криптовалюты
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 372e9),
    "LTC": CryptoCurrency("Litecoin", "LTC", "Scrypt", 4.5e9),
}


def get_currency(code: str) -> Currency:
    """
    Фабричный метод для получения объекта валюты по коду.
    
    Аргументы:
        code: Код валюты (например, "USD", "BTC").
    
    Возвращает:
        Объект Currency (FiatCurrency или CryptoCurrency).
    
    Исключения:
        CurrencyNotFoundError: Если валюта с таким кодом не найдена.
    """
    from .exceptions import CurrencyNotFoundError

    code = code.strip().upper()
    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    return _CURRENCY_REGISTRY[code]


def get_all_currencies() -> dict[str, Currency]:
    """
    Возвращает словарь всех поддерживаемых валют.
    
    Возвращает:
        Словарь {код: объект_валюты}.
    """
    return _CURRENCY_REGISTRY.copy()


def is_currency_supported(code: str) -> bool:
    """
    Проверяет, поддерживается ли валюта с указанным кодом.
    
    Аргументы:
        code: Код валюты для проверки.
    
    Возвращает:
        True если валюта поддерживается, иначе False.
    """
    return code.strip().upper() in _CURRENCY_REGISTRY


def get_supported_currency_codes() -> list[str]:
    """
    Возвращает список кодов поддерживаемых валют.
    
    Возвращает:
        Список строк с кодами валют.
    """
    return list(_CURRENCY_REGISTRY.keys())
