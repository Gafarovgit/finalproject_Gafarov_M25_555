"""Декораторы для логирования действий."""

import functools
import time
from typing import Any, Callable, Optional

from valutatrade_hub.logging_config import get_logger


def log_action(func: Optional[Callable] = None, *, action: str = None, verbose: bool = False):
    """
    Декоратор для логирования действий.
    
    Args:
        func: Функция для декорирования (передается при использовании без скобок).
        action: Название действия (если None, используется имя функции).
        verbose: Подробное логирование с дополнительным контекстом.
        
    Returns:
        Декорированная функция.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()

            # Определяем контекст логирования
            action_name = action or func.__name__.upper()
            log_context = {
                "action": action_name,
                "user": "system",
                "currency": "N/A",
                "amount": "0.0",
                "rate": "N/A",
                "base": "USD",
                "result": "OK",
            }

            # Извлекаем информацию из аргументов
            try:
                # Пытаемся извлечь user_id из аргументов
                if args and len(args) > 0:
                    if hasattr(args[0], "user_id"):
                        log_context["user"] = str(args[0].user_id)
                    elif isinstance(args[0], int) and len(args) > 1:
                        log_context["user"] = str(args[0])

                # Пытаемся извлечь параметры из kwargs
                if "currency_code" in kwargs:
                    log_context["currency"] = kwargs["currency_code"]
                elif "currency" in kwargs:
                    log_context["currency"] = kwargs["currency"]

                if "amount" in kwargs:
                    log_context["amount"] = str(kwargs["amount"])

                if "from_currency" in kwargs and "to_currency" in kwargs:
                    log_context["currency"] = (
                        f"{kwargs['from_currency']}->{kwargs['to_currency']}"
                    )

                # Время начала выполнения
                start_time = time.time()

                # Выполняем функцию
                result = func(*args, **kwargs)

                # Время выполнения
                execution_time = time.time() - start_time

                # Добавляем время выполнения в verbose режиме
                if verbose:
                    log_context["execution_time"] = f"{execution_time:.3f}s"

                # Логируем успешное выполнение
                logger.info(f"{action_name} выполнен", extra=log_context)

                return result

            except Exception as e:
                # Логируем ошибку
                log_context["result"] = "ERROR"
                log_context["error_type"] = e.__class__.__name__
                log_context["error_message"] = str(e)

                logger.error(f"{action_name} завершился ошибкой: {e}", extra=log_context)

                # Пробрасываем исключение дальше
                raise

        return wrapper

    # Обработка вызова с аргументами и без
    if func is None:
        # Декоратор вызван с аргументами: @log_action(action="BUY", verbose=True)
        return decorator
    else:
        # Декоратор вызван без аргументов: @log_action
        return decorator(func)


def timing_decorator(func: Callable) -> Callable:
    """Декоратор для измерения времени выполнения."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        logger = get_logger()
        logger.debug(
            f"Функция {func.__name__} выполнена за {end_time - start_time:.3f} секунд",
            extra={"action": "TIMING", "function": func.__name__},
        )

        return result

    return wrapper


def retry_decorator(max_retries: int = 3, delay: float = 1.0):
    """Декоратор для повторных попыток выполнения."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    logger = get_logger()
                    logger.warning(
                        f"Попытка {attempt + 1}/{max_retries} не удалась для {func.__name__}: {e}",
                        extra={
                            "action": "RETRY",
                            "function": func.__name__,
                            "attempt": attempt + 1,
                        },
                    )

                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # Увеличиваем задержку
                    else:
                        logger.error(
                            f"Все {max_retries} попыток не удались для {func.__name__}",
                            extra={"action": "RETRY_FAILED", "function": func.__name__},
                        )
                        raise last_exception

            raise last_exception  # На всякий случай

        return wrapper

    return decorator
