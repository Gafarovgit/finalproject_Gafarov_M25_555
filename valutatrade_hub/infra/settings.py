"""Singleton для загрузки и управления конфигурацией."""

import json
import os
from typing import Any, Dict, Optional


class SettingsLoader:
    """Singleton для загрузки настроек.

    Реализация через метакласс для гарантии единственного экземпляра.
    """

    _instance = None
    _initialized = False
    _config_path = None

    class _SettingsMeta(type):
        """Метакласс для реализации Singleton."""

        def __call__(cls, *args, **kwargs):
            if cls._instance is None:
                cls._instance = super().__call__(*args, **kwargs)
            return cls._instance

    def __new__(cls, *args, **kwargs):
        """Создание экземпляра через метакласс."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """Инициализация загрузчика настроек.

        Args:
            config_path: Путь к файлу конфигурации
        """
        # Если передан новый путь конфигурации, обновляем
        if config_path is not None:
            self._config_path = config_path
            self._initialized = False

        # Гарантируем инициализацию только один раз
        if self._initialized:
            return

        if self._config_path is None:
            self._config_path = config_path or "config.json"

        self._config: Dict[str, Any] = {}
        self._defaults = self._get_defaults()

        self.reload()
        self._initialized = True

    def _get_defaults(self) -> Dict[str, Any]:
        """Получение настроек по умолчанию.

        Returns:
            Словарь с настройками по умолчанию
        """
        return {
            "data_dir": "data",
            "log_dir": "logs",
            "log_file": "actions.log",
            "log_level": "INFO",
            "log_format": "text",  # или "json"
            "rates_ttl_seconds": 300,  # 5 минут
            "default_base_currency": "USD",
            "supported_currencies": ["USD", "EUR", "RUB", "BTC", "ETH"],
            "api_endpoints": {
                "rates": "https://api.exchangerate-api.com/v4/latest/",
                "crypto": "https://api.coingecko.com/api/v3/",
            },
            "max_retries": 3,
            "retry_delay": 1.0,
        }

    def reload(self):
        """Перезагрузка конфигурации из файла."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            else:
                self._config = {}
        except Exception as e:
            print(f"Ошибка при загрузке конфигурации: {e}")
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения настройки.

        Args:
            key: Ключ настройки
            default: Значение по умолчанию

        Returns:
            Значение настройки или значение по умолчанию
        """
        # Ищем в загруженной конфигурации
        value = self._config.get(key)
        if value is not None:
            return value

        # Ищем в настройках по умолчанию
        value = self._defaults.get(key)
        if value is not None:
            return value

        # Возвращаем переданное значение по умолчанию
        return default

    def set(self, key: str, value: Any, save: bool = False):
        """Установка значения настройки.

        Args:
            key: Ключ настройки
            value: Значение
            save: Сохранять ли в файл
        """
        self._config[key] = value

        if save:
            self.save()

    def save(self):
        """Сохранение конфигурации в файл."""
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении конфигурации: {e}")

    def get_data_dir(self) -> str:
        """Получение директории данных."""
        return self.get("data_dir", "data")

    def get_log_dir(self) -> str:
        """Получение директории логов."""
        return self.get("log_dir", "logs")

    def get_rates_ttl(self) -> int:
        """Получение TTL для курсов валют."""
        return self.get("rates_ttl_seconds", 300)

    def get_default_base_currency(self) -> str:
        """Получение базовой валюты по умолчанию."""
        return self.get("default_base_currency", "USD")

    def get_supported_currencies(self) -> list:
        """Получение списка поддерживаемых валют."""
        return self.get("supported_currencies", ["USD", "EUR", "RUB", "BTC", "ETH"])

    def get_api_endpoints(self) -> Dict[str, str]:
        """Получение API endpoints."""
        return self.get("api_endpoints", {})


# Создаем глобальный экземпляр настроек
settings = SettingsLoader()
