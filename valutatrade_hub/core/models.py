"""Модели данных для валютного кошелька."""

import hashlib
import json
from datetime import datetime
from typing import Dict, Optional


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        salt: Optional[str] = None,
        registration_date: Optional[datetime] = None,
    ):
        """Инициализация пользователя.

        Args:
            user_id: Уникальный идентификатор пользователя
            username: Имя пользователя
            password: Пароль в открытом виде
            salt: Соль для хэширования (генерируется, если не указана)
            registration_date: Дата регистрации (текущая, если не указана)
        """
        self._user_id = user_id
        self.username = username  # Используем сеттер
        self._salt = salt or self._generate_salt()
        self._hashed_password = self._hash_password(password)
        self._registration_date = registration_date or datetime.now()

    @property
    def user_id(self) -> int:
        """Геттер для user_id."""
        return self._user_id

    @property
    def username(self) -> str:
        """Геттер для username."""
        return self._username

    @username.setter
    def username(self, value: str):
        """Сеттер для username с валидацией."""
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        """Геттер для хэшированного пароля."""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Геттер для соли."""
        return self._salt

    @property
    def registration_date(self) -> datetime:
        """Геттер для даты регистрации."""
        return self._registration_date

    def _generate_salt(self) -> str:
        """Генерация случайной соли."""
        import secrets

        return secrets.token_hex(8)

    def _hash_password(self, password: str) -> str:
        """Хэширование пароля с солью."""
        return hashlib.sha256((password + self._salt).encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверка пароля.

        Args:
            password: Пароль для проверки

        Returns:
            True если пароль верный, иначе False
        """
        return self._hash_password(password) == self._hashed_password

    def change_password(self, new_password: str):
        """Изменение пароля пользователя.

        Args:
            new_password: Новый пароль
        """
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(new_password)

    def get_user_info(self) -> dict:
        """Получение информации о пользователе (без пароля).

        Returns:
            Словарь с информацией о пользователе
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def to_dict(self) -> dict:
        """Сериализация пользователя в словарь для JSON.

        Returns:
            Словарь с данными пользователя
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Создание пользователя из словаря.

        Args:
            data: Словарь с данными пользователя

        Returns:
            Экземпляр класса User
        """
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            password="dummy",  # Пароль не нужен, т.к. уже хэшированный
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"]),
        )


class Wallet:
    """Класс кошелька для одной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        """Инициализация кошелька.

        Args:
            currency_code: Код валюты (например, "USD", "BTC")
            balance: Начальный баланс
        """
        self.currency_code = currency_code
        self._balance = balance

    @property
    def currency_code(self) -> str:
        """Геттер для кода валюты."""
        return self._currency_code

    @currency_code.setter
    def currency_code(self, value: str):
        """Сеттер для кода валюты с валидацией."""
        if not value or not value.strip():
            raise ValueError("Код валюты не может быть пустым")
        self._currency_code = value.strip().upper()

    @property
    def balance(self) -> float:
        """Геттер для баланса."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Сеттер для баланса с валидацией."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float):
        """Пополнение баланса.

        Args:
            amount: Сумма для пополнения
        """
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance = self._balance + amount

    def withdraw(self, amount: float) -> bool:
        """Снятие средств с кошелька.

        Args:
            amount: Сумма для снятия

        Returns:
            True если операция успешна, иначе False
        """
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            return False
        self.balance = self._balance - amount
        return True

    def get_balance_info(self) -> str:
        """Получение информации о балансе.

        Returns:
            Строка с информацией о балансе
        """
        return f"{self._currency_code}: {self._balance:.2f}"

    def to_dict(self) -> dict:
        """Сериализация кошелька в словарь для JSON.

        Returns:
            Словарь с данными кошелька
        """
        return {"currency_code": self._currency_code, "balance": self._balance}

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        """Создание кошелька из словаря.

        Args:
            data: Словарь с данными кошелька

        Returns:
            Экземпляр класса Wallet
        """
        return cls(currency_code=data["currency_code"], balance=data["balance"])


class Portfolio:
    """Класс портфеля пользователя (управление всеми кошельками)."""

    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        """Инициализация портфеля.

        Args:
            user_id: ID пользователя
            wallets: Словарь кошельков (код валюты → Wallet)
        """
        self._user_id = user_id
        self._wallets = wallets or {}

    @property
    def user_id(self) -> int:
        """Геттер для user_id."""
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Геттер для копии словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> bool:
        """Добавление новой валюты в портфель.

        Args:
            currency_code: Код валюты

        Returns:
            True если валюта добавлена, False если уже существует
        """
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            return False

        self._wallets[currency_code] = Wallet(currency_code)
        return True

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """Получение кошелька по коду валюты.

        Args:
            currency_code: Код валюты

        Returns:
            Объект Wallet или None если не найден
        """
        return self._wallets.get(currency_code.upper())

    def get_total_value(
        self, exchange_rates: Dict[str, float], base_currency: str = "USD"
    ) -> float:
        """Расчет общей стоимости портфеля в базовой валюте.

        Args:
            exchange_rates: Словарь курсов валют
            base_currency: Базовая валюта для расчета

        Returns:
            Общая стоимость портфеля
        """
        total = 0.0

        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total += wallet.balance
            else:
                rate_key = f"{currency_code}_{base_currency}"
                if rate_key in exchange_rates:
                    total += wallet.balance * exchange_rates[rate_key]
                # Если нет курса, пропускаем валюту

        return total

    def to_dict(self) -> dict:
        """Сериализация портфеля в словарь для JSON.

        Returns:
            Словарь с данными портфеля
        """
        return {
            "user_id": self._user_id,
            "wallets": {
                code: wallet.to_dict() for code, wallet in self._wallets.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        """Создание портфеля из словаря.

        Args:
            data: Словарь с данными портфеля

        Returns:
            Экземпляр класса Portfolio
        """
        wallets = {
            code: Wallet.from_dict(wallet_data)
            for code, wallet_data in data["wallets"].items()
        }
        return cls(user_id=data["user_id"], wallets=wallets)
