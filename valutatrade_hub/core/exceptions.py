"""
Пользовательские исключения для обработки ошибок в приложении.
"""


class InsufficientFundsError(Exception):
    """Исключение при недостатке средств на кошельке."""

    def __init__(self, currency_code: str, available: float, required: float):
        """
        Инициализирует исключение недостатка средств.
        
        Аргументы:
            currency_code: Код валюты.
            available: Доступное количество.
            required: Требуемое количество.
        """
        self.currency_code = currency_code
        self.available = float(available)
        self.required = float(required)
        message = (f"Недостаточно средств: доступно {self.available:.4f} {currency_code}, "
                   f"требуется {self.required:.4f} {currency_code}")
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Исключение при неизвестной валюте."""

    def __init__(self, currency_code: str):
        """
        Инициализирует исключение неизвестной валюты.
        
        Аргументы:
            currency_code: Код неизвестной валюты.
        """
        self.currency_code = currency_code  # Добавляем сохранение атрибута
        message = f"Неизвестная валюта '{currency_code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    """Исключение при сбое внешнего API."""

    def __init__(self, reason: str = "Неизвестная ошибка"):
        """
        Инициализирует исключение ошибки API.
        
        Аргументы:
            reason: Причина ошибки.
        """
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)


class UserNotFoundError(Exception):
    """Исключение при отсутствии пользователя."""

    def __init__(self, username: str = None, user_id: int = None):
        """
        Инициализирует исключение отсутствия пользователя.
        
        Аргументы:
            username: Имя пользователя (если указано).
            user_id: ID пользователя (если указано).
        """
        self.username = username
        self.user_id = user_id
        if username:
            message = f"Пользователь '{username}' не найден"
        elif user_id:
            message = f"Пользователь с ID={user_id} не найден"
        else:
            message = "Пользователь не найден"
        super().__init__(message)


class AuthenticationError(Exception):
    """Исключение при ошибке аутентификации."""

    def __init__(self, reason: str = "Неверные учетные данные"):
        """
        Инициализирует исключение аутентификации.
        
        Аргументы:
            reason: Причина ошибки.
        """
        self.reason = reason
        super().__init__(reason)
