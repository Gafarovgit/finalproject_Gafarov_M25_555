"""
Бизнес-логика приложения (Use Cases).
"""

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ..decorators import log_action
from ..infra.database import DatabaseManager
from ..infra.settings import SettingsLoader
from .currencies import get_all_currencies, is_currency_supported
from .exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    UserNotFoundError,
)
from .models import Portfolio, User

# Глобальные объекты синглтонов
db = DatabaseManager()
settings = SettingsLoader()

# Текущий пользователь (для сессии)
_current_user: Optional[User] = None


def register_user(username: str, password: str) -> Tuple[int, str]:
    """
    Регистрация нового пользователя.
    
    Args:
        username: Имя пользователя.
        password: Пароль.
        
    Returns:
        Кортеж (user_id, сообщение об успехе).
        
    Raises:
        ValueError: Если имя пользователя уже занято или пароль слишком короткий.
    """
    # Проверка уникальности имени пользователя
    users = db.load_users()
    for user_data in users:
        if user_data.get('username') == username:
            raise ValueError(f"Имя пользователя '{username}' уже занято")

    # Проверка пароля
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    # Генерация ID
    user_id = 1
    if users:
        max_id = max(user.get('user_id', 0) for user in users)
        user_id = max_id + 1

    # Генерация соли и хэширование пароля
    import hashlib
    import secrets
    salt = secrets.token_hex(8)
    hash_object = hashlib.sha256()
    hash_object.update(password.encode('utf-8'))
    hash_object.update(salt.encode('utf-8'))
    hashed_password = hash_object.hexdigest()

    # Создание пользователя
    user = User(
        user_id=user_id,
        username=username,
        hashed_password=hashed_password,
        salt=salt,
        registration_date=datetime.now().isoformat()
    )

    # Сохранение пользователя
    users.append(user.to_dict())
    db.save_users(users)

    # Создание пустого портфеля
    portfolio = Portfolio(user_id=user_id, wallets={})
    portfolios = db.load_portfolios()
    portfolios.append(portfolio.to_dict())
    db.save_portfolios(portfolios)

    return user_id, f"Пользователь '{username}' зарегистрирован (id={user_id})"


def login_user(username: str, password: str) -> User:
    """
    Авторизация пользователя.
    
    Args:
        username: Имя пользователя.
        password: Пароль.
        
    Returns:
        Объект User.
        
    Raises:
        UserNotFoundError: Если пользователь не найден.
        AuthenticationError: Если пароль неверный.
    """
    global _current_user

    users = db.load_users()
    user_data = None

    for user in users:
        if user.get('username') == username:
            user_data = user
            break

    if not user_data:
        raise UserNotFoundError(username=username)

    # Создание объекта User из данных
    user = User.from_dict(user_data)

    # Проверка пароля
    if not user.verify_password(password):
        raise AuthenticationError("Неверный пароль")

    _current_user = user
    return user


def get_current_user() -> Optional[User]:
    """Возвращает текущего авторизованного пользователя."""
    return _current_user


def logout_user() -> None:
    """Выход пользователя из системы."""
    global _current_user
    _current_user = None


def get_user_portfolio(user_id: int) -> Portfolio:
    """
    Получение портфеля пользователя.
    
    Args:
        user_id: ID пользователя.
        
    Returns:
        Объект Portfolio.
        
    Raises:
        UserNotFoundError: Если портфель не найден.
    """
    portfolios = db.load_portfolios()

    for portfolio_data in portfolios:
        if portfolio_data.get('user_id') == user_id:
            return Portfolio.from_dict(portfolio_data)

    raise UserNotFoundError(user_id=user_id)


def get_exchange_rate_api(from_currency: str, to_currency: str) -> Optional[float]:
    """
    Получает курс обмена из API (заглушка).
    
    Args:
        from_currency: Исходная валюта.
        to_currency: Целевая валюта.
        
    Returns:
        Курс обмена или None, если курс не найден.
    """
    # Это заглушка для API. В реальном приложении здесь будет запрос к внешнему сервису.
    # Используем фиксированные курсы для демонстрации.
    fixed_rates = {
        "EUR_USD": 1.08,
        "BTC_USD": 50000.0,
        "ETH_USD": 3000.0,
        "RUB_USD": 0.011,
        "USD_USD": 1.0,
        "LTC_USD": 150.0,
    }

    rate_key = f"{from_currency}_{to_currency}"
    return fixed_rates.get(rate_key)


def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
    """
    Получение курса обмена между валютами.
    
    Args:
        from_currency: Исходная валюта.
        to_currency: Целевая валюта.
        
    Returns:
        Курс обмена.
        
    Raises:
        CurrencyNotFoundError: Если валюта не найдена.
        ApiRequestError: Если не удалось получить курс.
    """
    # Проверяем, что валюты поддерживаются
    if not is_currency_supported(from_currency):
        raise CurrencyNotFoundError(from_currency)
    if not is_currency_supported(to_currency):
        raise CurrencyNotFoundError(to_currency)

    # Если валюты одинаковые, курс = 1
    if from_currency == to_currency:
        return 1.0

    # Получаем курсы из базы данных
    rates = db.load_rates()

    # Пытаемся найти прямой курс
    rate_key = f"{from_currency}_{to_currency}"
    if rate_key in rates:
        rate_data = rates[rate_key]
        if 'rate' in rate_data:
            # Проверяем свежесть курса
            if is_rate_fresh(rate_data, settings.get('rates_ttl', 300)):
                return rate_data['rate']

    # Пытаемся найти обратный курс
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in rates:
        rate_data = rates[reverse_key]
        if 'rate' in rate_data and rate_data['rate'] != 0:
            if is_rate_fresh(rate_data, settings.get('rates_ttl', 300)):
                return 1 / rate_data['rate']

    # Если курс устарел или не найден, пытаемся обновить из API
    try:
        rate = get_exchange_rate_api(from_currency, to_currency)
        if rate is None:
            # Пробуем получить обратный курс через API
            reverse_rate = get_exchange_rate_api(to_currency, from_currency)
            if reverse_rate is not None and reverse_rate != 0:
                rate = 1 / reverse_rate

        if rate is None:
            raise ApiRequestError(f"Курс {from_currency}→{to_currency} недоступен")

        # Сохраняем курс в базу данных
        rates[rate_key] = {
            'rate': rate,
            'updated_at': datetime.now().isoformat(),
            'source': 'API'
        }
        db.save_rates(rates)

        return rate

    except Exception as e:
        raise ApiRequestError(f"Ошибка при обращении к API: {str(e)}")


def is_rate_fresh(rate_data: Dict, ttl_seconds: int) -> bool:
    """
    Проверяет свежесть курса.
    
    Args:
        rate_data: Данные курса.
        ttl_seconds: Время жизни курса в секундах.
        
    Returns:
        True если курс свежий, иначе False.
    """
    if 'updated_at' not in rate_data:
        return False

    try:
        updated_at = datetime.fromisoformat(rate_data['updated_at'])
        time_diff = datetime.now() - updated_at
        return time_diff.total_seconds() < ttl_seconds
    except (ValueError, TypeError):
        return False


@log_action(action="BUY", verbose=True)
def buy_currency(user_id: int, currency_code: str, amount: float) -> Tuple[float, float]:
    """
    Покупка валюты.
    
    Args:
        user_id: ID пользователя.
        currency_code: Код покупаемой валюты.
        amount: Количество покупаемой валюты.
        
    Returns:
        Кортеж (стоимость покупки в USD, новый баланс валюты).
        
    Raises:
        CurrencyNotFoundError: Если валюта не найдена.
        ValueError: Если сумма некорректна.
        InsufficientFundsError: Если недостаточно USD для покупки.
    """
    if amount <= 0:
        raise ValueError("Сумма покупки должна быть положительной")

    # Проверяем, что валюта поддерживается
    if not is_currency_supported(currency_code):
        raise CurrencyNotFoundError(currency_code)

    # Получение курса
    rate = get_exchange_rate(currency_code, "USD")

    # Расчет стоимости в USD
    cost_usd = amount * rate

    # Получение портфеля
    portfolio = get_user_portfolio(user_id)

    # Проверка наличия USD
    usd_wallet = portfolio.get_wallet("USD")
    if not usd_wallet or usd_wallet.balance < cost_usd:
        available = usd_wallet.balance if usd_wallet else 0
        raise InsufficientFundsError("USD", available, cost_usd)

    # Списание USD
    usd_wallet.withdraw(cost_usd)

    # Пополнение купленной валюты
    target_wallet = portfolio.get_wallet(currency_code)
    if not target_wallet:
        portfolio.add_currency(currency_code)
        target_wallet = portfolio.get_wallet(currency_code)

    target_wallet.deposit(amount)

    # Сохранение изменений
    portfolios = db.load_portfolios()
    for i, p_data in enumerate(portfolios):
        if p_data.get('user_id') == user_id:
            portfolios[i] = portfolio.to_dict()
            break

    db.save_portfolios(portfolios)

    return cost_usd, target_wallet.balance


@log_action(action="SELL", verbose=True)
def sell_currency(user_id: int, currency_code: str, amount: float) -> Tuple[float, float]:
    """
    Продажа валюты.
    
    Args:
        user_id: ID пользователя.
        currency_code: Код продаваемой валюты.
        amount: Количество продаваемой валюты.
        
    Returns:
        Кортеж (выручка в USD, новый баланс валюты).
        
    Raises:
        CurrencyNotFoundError: Если валюта не найдена.
        ValueError: Если сумма некорректна.
        InsufficientFundsError: Если недостаточно валюты для продажи.
    """
    if amount <= 0:
        raise ValueError("Сумма продажи должна быть положительной")

    # Проверяем, что валюта поддерживается
    if not is_currency_supported(currency_code):
        raise CurrencyNotFoundError(currency_code)

    # Получение курса
    rate = get_exchange_rate(currency_code, "USD")

    # Расчет выручки в USD
    revenue_usd = amount * rate

    # Получение портфеля
    portfolio = get_user_portfolio(user_id)

    # Проверка наличия валюты
    currency_wallet = portfolio.get_wallet(currency_code)
    if not currency_wallet or currency_wallet.balance < amount:
        available = currency_wallet.balance if currency_wallet else 0
        raise InsufficientFundsError(currency_code, available, amount)

    # Списание валюты
    currency_wallet.withdraw(amount)

    # Пополнение USD
    usd_wallet = portfolio.get_wallet("USD")
    if not usd_wallet:
        portfolio.add_currency("USD")
        usd_wallet = portfolio.get_wallet("USD")

    usd_wallet.deposit(revenue_usd)

    # Сохранение изменений
    portfolios = db.load_portfolios()
    for i, p_data in enumerate(portfolios):
        if p_data.get('user_id') == user_id:
            portfolios[i] = portfolio.to_dict()
            break

    db.save_portfolios(portfolios)

    return revenue_usd, currency_wallet.balance


def get_portfolio_value(user_id: int, base_currency: str = "USD") -> Dict[str, Any]:
    """
    Получение информации о портфеле с расчетом стоимости.
    
    Args:
        user_id: ID пользователя.
        base_currency: Базовая валюта для расчета.
        
    Returns:
        Словарь с информацией о портфеле.
        
    Raises:
        UserNotFoundError: Если портфель не найден.
    """
    portfolio = get_user_portfolio(user_id)

    result = {
        "user_id": user_id,
        "total_value": 0.0,
        "base_currency": base_currency,
        "wallets": []
    }

    total_value = 0.0

    for currency_code, wallet in portfolio.wallets.items():
        if currency_code == base_currency:
            value = wallet.balance
        else:
            try:
                rate = get_exchange_rate(currency_code, base_currency)
                value = wallet.balance * rate
            except (CurrencyNotFoundError, ApiRequestError):
                # Если не можем получить курс, пропускаем эту валюту
                continue

        total_value += value

        result["wallets"].append({
            "currency_code": currency_code,
            "balance": wallet.balance,
            "value_in_base": value
        })

    result["total_value"] = total_value

    return result


def get_supported_currencies_list() -> list:
    """
    Возвращает список поддерживаемых валют.
    
    Returns:
        Список словарей с информацией о валютах.
    """
    currencies = get_all_currencies()
    result = []

    for code, currency in currencies.items():
        result.append({
            "code": code,
            "name": currency.name,
            "type": currency.__class__.__name__.replace("Currency", "").upper(),
            "display_info": currency.get_display_info()
        })

    return result
