"""Конфигурация логирования для приложения."""

import logging
import logging.handlers
import os


def setup_logging(
    log_dir: str = "logs",
    log_file: str = "actions.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    json_format: bool = False,
) -> logging.Logger:
    """Настройка логирования.

    Args:
        log_dir: Директория для логов
        log_file: Имя файла лога
        level: Уровень логирования
        max_bytes: Максимальный размер файла перед ротацией
        backup_count: Количество хранимых бекапов
        json_format: Использовать JSON формат

    Returns:
        Настроенный логгер
    """
    # Создаем директорию для логов если не существует
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Полный путь к файлу лога
    log_path = os.path.join(log_dir, log_file)

    # Создаем логгер
    logger = logging.getLogger("valutatrade")
    logger.setLevel(level)

    # Удаляем существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Создаем форматтер
    if json_format:
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"module": "%(name)s", "message": "%(message)s", '
            '"user": "%(user)s", "action": "%(action)s", '
            '"currency": "%(currency)s", "amount": "%(amount)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            '%(levelname)s %(asctime)s %(action)s user="%(user)s" '
            'currency="%(currency)s" amount="%(amount)s" '
            'rate="%(rate)s" base="%(base)s" result="%(result)s"',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    # Обработчик для файла с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Обработчик для консоли (только для отладки)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(
        logging.DEBUG if level == logging.DEBUG else logging.WARNING
    )
    logger.addHandler(console_handler)

    # Фильтр для добавления дополнительных полей
    class ContextFilter(logging.Filter):
        """Фильтр для добавления контекста в логи."""

        def filter(self, record):
            if not hasattr(record, "user"):
                record.user = "system"
            if not hasattr(record, "action"):
                record.action = "UNKNOWN"
            if not hasattr(record, "currency"):
                record.currency = "N/A"
            if not hasattr(record, "amount"):
                record.amount = "0.0"
            if not hasattr(record, "rate"):
                record.rate = "N/A"
            if not hasattr(record, "base"):
                record.base = "N/A"
            if not hasattr(record, "result"):
                record.result = "UNKNOWN"
            return True

    logger.addFilter(ContextFilter())

    return logger


def get_logger(name: str = "valutatrade") -> logging.Logger:
    """Получение логгера.

    Args:
        name: Имя логгера

    Returns:
        Логгер
    """
    return logging.getLogger(name)


# Создаем глобальный логгер
logger = setup_logging()
