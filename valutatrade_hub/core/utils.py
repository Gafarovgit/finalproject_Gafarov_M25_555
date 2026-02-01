"""
Вспомогательные функции для валютного кошелька.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


def format_currency(amount: float, currency_code: str = "USD") -> str:
    """
    Форматирует денежную сумму с кодом валюты.
    
    Args:
        amount: Сумма для форматирования.
        currency_code: Код валюты.
        
    Returns:
        Отформатированная строка.
    """
    # Определяем символы валют (можно расширить)
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "RUB": "₽",
        "BTC": "₿",
        "ETH": "Ξ",
        "LTC": "Ł"
    }

    symbol = currency_symbols.get(currency_code, currency_code)

    # Форматируем число
    if abs(amount) >= 1000:
        formatted_amount = f"{amount:,.2f}"
    else:
        formatted_amount = f"{amount:.2f}"

    return f"{symbol}{formatted_amount}"


def validate_currency_code(currency_code: str) -> bool:
    """
    Проверяет корректность кода валюты.
    
    Args:
        currency_code: Код валюты для проверки.
        
    Returns:
        True если код корректен, иначе False.
    """
    if not isinstance(currency_code, str):
        return False

    currency_code = currency_code.strip().upper()
    return 2 <= len(currency_code) <= 5 and currency_code.isalnum()


def validate_amount(amount: float) -> bool:
    """
    Проверяет корректность суммы.
    
    Args:
        amount: Сумма для проверки.
        
    Returns:
        True если сумма корректна, иначе False.
    """
    try:
        amount_float = float(amount)
        return amount_float > 0
    except (ValueError, TypeError):
        return False


def load_json_file(filepath: str) -> Any:
    """
    Загружает данные из JSON файла.
    
    Args:
        filepath: Путь к JSON файлу.
        
    Returns:
        Данные из файла.
        
    Исключения:
        FileNotFoundError: Если файл не существует.
        json.JSONDecodeError: Если файл содержит некорректный JSON.
    """
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(filepath: str, data: Any) -> None:
    """
    Сохраняет данные в JSON файл.
    
    Args:
        filepath: Путь к JSON файлу.
        data: Данные для сохранения.
    """
    # Создаем директорию, если она не существует
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def get_exchange_rate(from_currency: str, to_currency: str, rates_data: Dict) -> Optional[float]:
    """
    Получает курс обмена между двумя валютами.
    
    Args:
        from_currency: Исходная валюта.
        to_currency: Целевая валюта.
        rates_data: Данные с курсами валют.
        
    Returns:
        Курс обмена или None, если курс не найден.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    # Прямой курс
    rate_key = f"{from_currency}_{to_currency}"
    if rate_key in rates_data:
        return rates_data[rate_key].get("rate")

    # Обратный курс
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in rates_data:
        rate = rates_data[reverse_key].get("rate")
        if rate and rate != 0:
            return 1 / rate

    # Через USD (если обе валюты имеют курс к USD)
    if from_currency != "USD" and to_currency != "USD":
        rate1_key = f"{from_currency}_USD"
        rate2_key = f"{to_currency}_USD"

        if rate1_key in rates_data and rate2_key in rates_data:
            rate1 = rates_data[rate1_key].get("rate")
            rate2 = rates_data[rate2_key].get("rate")

            if rate1 and rate2 and rate2 != 0:
                return rate1 / rate2

    return None


def calculate_portfolio_value(portfolio: 'Portfolio', rates_data: Dict, base_currency: str = "USD") -> float:
    """
    Рассчитывает общую стоимость портфеля в базовой валюте.
    
    Args:
        portfolio: Объект портфеля.
        rates_data: Данные с курсами валют.
        base_currency: Базовая валюта для расчета.
        
    Returns:
        Общая стоимость портфеля.
    """
    total_value = 0.0

    for currency_code, wallet in portfolio.wallets.items():
        if currency_code == base_currency:
            total_value += wallet.balance
        else:
            rate = get_exchange_rate(currency_code, base_currency, rates_data)
            if rate:
                total_value += wallet.balance * rate

    return total_value


def is_rate_fresh(rate_data: Dict, ttl_seconds: int = 300) -> bool:
    """
    Проверяет, актуален ли курс валюты.
    
    Args:
        rate_data: Данные курса (должны содержать ключ 'updated_at').
        ttl_seconds: Время жизни курса в секундах (по умолчанию 5 минут).
        
    Returns:
        True если курс актуален, иначе False.
    """
    if not rate_data or 'updated_at' not in rate_data:
        return False

    try:
        updated_at = datetime.fromisoformat(rate_data['updated_at'])
        time_diff = datetime.now() - updated_at
        return time_diff.total_seconds() < ttl_seconds
    except (ValueError, TypeError):
        return False


def get_supported_currencies() -> list:
    """
    Возвращает список поддерживаемых валют.
    
    Returns:
        Список кодов поддерживаемых валют.
    """
    return ["USD", "EUR", "RUB", "BTC", "ETH", "LTC"]


def generate_user_id(existing_users: list) -> int:
    """
    Генерирует новый ID пользователя.
    
    Args:
        existing_users: Список существующих пользователей.
        
    Returns:
        Новый уникальный ID.
    """
    if not existing_users:
        return 1

    max_id = max(user.get('user_id', 0) for user in existing_users)
    return max_id + 1
