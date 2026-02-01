"""Singleton для управления JSON-хранилищем."""

import json
import os
import threading
from typing import Any, Dict, List, Optional

from valutatrade_hub.infra.settings import settings


class DatabaseManager:
    """Singleton для управления базой данных (JSON файлы)."""

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        """Создание экземпляра (реализация Singleton)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализация менеджера базы данных."""
        with self._lock:
            if self._initialized:
                return

            self.data_dir = settings.get_data_dir()
            self._ensure_data_dir()

            # Пути к файлам
            self.users_file = os.path.join(self.data_dir, "users.json")
            self.portfolios_file = os.path.join(self.data_dir, "portfolios.json")
            self.rates_file = os.path.join(self.data_dir, "rates.json")

            # Кэш для данных
            self._users_cache: Optional[List[Dict]] = None
            self._portfolios_cache: Optional[List[Dict]] = None
            self._rates_cache: Optional[Dict] = None

            self._initialized = True

    def _ensure_data_dir(self):
        """Создание директории для данных если не существует."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)

    def _read_json(self, filepath: str, default: Any) -> Any:
        """Безопасное чтение JSON файла.

        Args:
            filepath: Путь к файлу
            default: Значение по умолчанию

        Returns:
            Данные из файла
        """
        if not os.path.exists(filepath):
            return default

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка при чтении файла {filepath}: {e}")
            return default

    def _write_json(self, filepath: str, data: Any):
        """Безопасная запись в JSON файл.

        Args:
            filepath: Путь к файлу
            data: Данные для записи
        """
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Создаем временный файл для атомарной записи
            temp_file = filepath + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            # Переименовываем временный файл в целевой
            os.replace(temp_file, filepath)
        except IOError as e:
            print(f"Ошибка при записи файла {filepath}: {e}")
            raise

    # Методы, которые использует usecases.py
    def load_users(self) -> List[Dict]:
        """Загрузка списка пользователей."""
        with self._lock:
            if self._users_cache is not None:
                return self._users_cache.copy()  # Возвращаем копию

            self._users_cache = self._read_json(self.users_file, [])
            return self._users_cache.copy()

    def save_users(self, users: List[Dict]):
        """Сохранение списка пользователей."""
        with self._lock:
            self._write_json(self.users_file, users)
            self._users_cache = users

    def load_portfolios(self) -> List[Dict]:
        """Загрузка списка портфелей."""
        with self._lock:
            if self._portfolios_cache is not None:
                return self._portfolios_cache.copy()

            self._portfolios_cache = self._read_json(self.portfolios_file, [])
            return self._portfolios_cache.copy()

    def save_portfolios(self, portfolios: List[Dict]):
        """Сохранение списка портфелей."""
        with self._lock:
            self._write_json(self.portfolios_file, portfolios)
            self._portfolios_cache = portfolios

    def load_rates(self) -> Dict:
        """Загрузка курсов валют."""
        with self._lock:
            if self._rates_cache is not None:
                return self._rates_cache.copy()

            self._rates_cache = self._read_json(self.rates_file, {})
            return self._rates_cache.copy()

    def save_rates(self, rates: Dict):
        """Сохранение курсов валют."""
        with self._lock:
            self._write_json(self.rates_file, rates)
            self._rates_cache = rates

    # Дополнительные методы для обратной совместимости
    def get_users(self, use_cache: bool = True) -> List[Dict]:
        """Получение списка пользователей (для обратной совместимости)."""
        return self.load_users()

    def get_portfolios(self, use_cache: bool = True) -> List[Dict]:
        """Получение списка портфелей (для обратной совместимости)."""
        return self.load_portfolios()

    def get_rates(self, use_cache: bool = True) -> Dict:
        """Получение курсов валют (для обратной совместимости)."""
        return self.load_rates()

    def clear_cache(self):
        """Очистка кэша."""
        with self._lock:
            self._users_cache = None
            self._portfolios_cache = None
            self._rates_cache = None

    def transaction(self, operation: str, data_type: str, data: Any):
        """Выполнение транзакции.

        Args:
            operation: Операция (read/write/update/delete)
            data_type: Тип данных (users/portfolios/rates)
            data: Данные

        Returns:
            Результат операции
        """
        with self._lock:
            if data_type == "users":
                if operation == "read":
                    return self.load_users()
                elif operation == "write":
                    self.save_users(data)
            elif data_type == "portfolios":
                if operation == "read":
                    return self.load_portfolios()
                elif operation == "write":
                    self.save_portfolios(data)
            elif data_type == "rates":
                if operation == "read":
                    return self.load_rates()
                elif operation == "write":
                    self.save_rates(data)

            return None


# Создаем глобальный экземпляр менеджера базы данных
db = DatabaseManager()
