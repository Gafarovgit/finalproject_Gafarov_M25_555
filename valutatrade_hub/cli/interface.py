"""Командный интерфейс приложения."""

import argparse
import sys

from prettytable import PrettyTable

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    UserNotFoundError,
)
from valutatrade_hub.core.usecases import (
    buy_currency,
    get_current_user,
    get_exchange_rate,
    get_portfolio_value,
    get_supported_currencies_list,
    login_user,
    logout_user,
    register_user,
    sell_currency,
)
from valutatrade_hub.core.utils import format_currency


def is_authenticated() -> bool:
    """Проверяет, авторизован ли пользователь."""
    return get_current_user() is not None


def register_command(args):
    """Обработка команды register."""
    if not args.username or not args.password:
        print("Ошибка: --username и --password обязательны")
        return 1

    try:
        user_id, message = register_user(args.username, args.password)
        print(message)
        print(f"Войдите: login --username {args.username} --password [ваш_пароль]")
        return 0

    except ValueError as e:
        print(f"Ошибка: {e}")
        return 1
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return 1


def login_command(args):
    """Обработка команды login."""
    if not args.username or not args.password:
        print("Ошибка: --username и --password обязательны")
        return 1

    try:
        user = login_user(args.username, args.password)
        print(f"Вы вошли как '{user.username}'")
        return 0

    except UserNotFoundError as e:
        print(f"Ошибка: {e}")
        return 1
    except AuthenticationError as e:
        print(f"Ошибка: {e}")
        return 1
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return 1


def logout_command(args):
    """Обработка команды logout."""
    if not is_authenticated():
        print("Ошибка: Вы не авторизованы")
        return 1

    logout_user()
    print("Вы вышли из системы")
    return 0


def show_portfolio_command(args):
    """Обработка команды show-portfolio."""
    if not is_authenticated():
        print("Ошибка: Сначала выполните login")
        return 1

    base_currency = args.base.upper() if args.base else "USD"

    # Валидация базовой валюты
    try:
        from valutatrade_hub.core.currencies import is_currency_supported
        if not is_currency_supported(base_currency):
            print(f"Ошибка: Неизвестная базовая валюта '{base_currency}'")
            return 1
    except ImportError:
        # Если модуль currencies не доступен, используем простую проверку
        supported = ["USD", "EUR", "RUB", "BTC", "ETH", "LTC"]
        if base_currency not in supported:
            print(f"Ошибка: Неизвестная базовая валюта '{base_currency}'")
            return 1

    current_user = get_current_user()

    try:
        portfolio_info = get_portfolio_value(current_user.user_id, base_currency)

        if not portfolio_info["wallets"]:
            print("Ваш портфель пуст")
            return 0

        # Создаем таблицу
        table = PrettyTable()
        table.field_names = ["Валюта", "Баланс", f"Стоимость ({base_currency})"]
        table.align["Валюта"] = "l"
        table.align["Баланс"] = "r"
        table.align[f"Стоимость ({base_currency})"] = "r"

        total = portfolio_info["total_value"]
        for wallet_info in portfolio_info["wallets"]:
            currency_code = wallet_info["currency_code"]
            balance = wallet_info["balance"]
            value = wallet_info["value_in_base"]

            # Форматируем баланс в зависимости от типа валюты
            if currency_code in ["BTC", "ETH", "LTC"]:
                balance_str = f"{balance:.8f}"
            else:
                balance_str = f"{balance:.2f}"

            table.add_row([currency_code, balance_str, f"{value:,.2f}"])

        print(f"Портфель пользователя '{current_user.username}' (база: {base_currency}):")
        print(table)
        print(f"\nИТОГО: {format_currency(total, base_currency)}")
        return 0

    except UserNotFoundError as e:
        print(f"Ошибка: {e}")
        return 1
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return 1


def buy_command(args):
    """Обработка команды buy."""
    if not is_authenticated():
        print("Ошибка: Сначала выполните login")
        return 1

    if not args.currency or args.amount <= 0:
        print("Ошибка: --currency обязателен и --amount должен быть положительным числом")
        return 1

    currency_code = args.currency.upper()
    amount = float(args.amount)
    current_user = get_current_user()

    try:
        cost_usd, new_balance = buy_currency(
            user_id=current_user.user_id,
            currency_code=currency_code,
            amount=amount
        )

        # Получаем курс для отображения
        try:
            rate = get_exchange_rate(currency_code, "USD")
            print(f"Покупка выполнена: {amount:.4f} {currency_code} по курсу {rate:.2f} USD/{currency_code}")
        except:
            print(f"Покупка выполнена: {amount:.4f} {currency_code}")

        print("Изменения в портфеле:")
        print(f"- {currency_code}: стало {new_balance:.4f}")
        print(f"Оценочная стоимость покупки: {cost_usd:.2f} USD")
        return 0

    except InsufficientFundsError as e:
        print(f"Ошибка: {e}")
        print("Пополните баланс USD для покупки валюты")
        return 1
    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}")
        print("Используйте команду 'get-rate --list' для просмотра поддерживаемых валют")
        return 1
    except ApiRequestError as e:
        print(f"Ошибка: {e}")
        print("Повторите попытку позже")
        return 1
    except ValueError as e:
        print(f"Ошибка: {e}")
        return 1
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return 1


def sell_command(args):
    """Обработка команды sell."""
    if not is_authenticated():
        print("Ошибка: Сначала выполните login")
        return 1

    if not args.currency or args.amount <= 0:
        print("Ошибка: --currency обязателен и --amount должен быть положительным числом")
        return 1

    currency_code = args.currency.upper()
    amount = float(args.amount)
    current_user = get_current_user()

    try:
        revenue_usd, new_balance = sell_currency(
            user_id=current_user.user_id,
            currency_code=currency_code,
            amount=amount
        )

        # Получаем курс для отображения
        try:
            rate = get_exchange_rate(currency_code, "USD")
            print(f"Продажа выполнена: {amount:.4f} {currency_code} по курсу {rate:.2f} USD/{currency_code}")
        except:
            print(f"Продажа выполнена: {amount:.4f} {currency_code}")

        print("Изменения в портфеле:")
        print(f"- {currency_code}: стало {new_balance:.4f}")
        print(f"Оценочная выручка: {revenue_usd:.2f} USD")
        return 0

    except InsufficientFundsError as e:
        print(f"Ошибка: {e}")
        return 1
    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}")
        print("Используйте команду 'get-rate --list' для просмотра поддерживаемых валют")
        return 1
    except ApiRequestError as e:
        print(f"Ошибка: {e}")
        print("Повторите попытку позже")
        return 1
    except ValueError as e:
        print(f"Ошибка: {e}")
        return 1
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return 1


def get_rate_command(args):
    """Обработка команды get-rate."""
    if args.list:
        # Показать список поддерживаемых валют
        try:
            currencies = get_supported_currencies_list()
            table = PrettyTable()
            table.field_names = ["Код", "Название", "Тип", "Информация"]
            table.align["Код"] = "l"
            table.align["Название"] = "l"
            table.align["Тип"] = "l"
            table.align["Информация"] = "l"

            for currency in currencies:
                table.add_row([
                    currency["code"],
                    currency["name"],
                    currency["type"],
                    currency["display_info"]
                ])

            print("Поддерживаемые валюты:")
            print(table)
            return 0
        except Exception as e:
            print(f"Ошибка при получении списка валют: {e}")
            return 1

    if not args.from_currency or not args.to_currency:
        print("Ошибка: --from и --to обязательны (или используйте --list)")
        return 1

    from_curr = args.from_currency.upper()
    to_curr = args.to_currency.upper()

    try:
        rate = get_exchange_rate(from_curr, to_curr)

        if rate:
            print(f"Курс {from_curr}→{to_curr}: {rate:.6f}")
            if rate != 0:
                print(f"Обратный курс {to_curr}→{from_curr}: {1/rate:.6f}")
            return 0
        else:
            print(f"Курс {from_curr}→{to_curr} недоступен")
            return 1

    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}")
        print("Используйте команду 'get-rate --list' для просмотра поддерживаемых валют")
        return 1
    except ApiRequestError as e:
        print(f"Ошибка: {e}")
        print("Повторите попытку позже")
        return 1
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return 1


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description="Валютный кошелек для торговли валютами",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # Команда register
    register_parser = subparsers.add_parser(
        "register", help="Регистрация нового пользователя"
    )
    register_parser.add_argument("--username", required=True, help="Имя пользователя")
    register_parser.add_argument("--password", required=True, help="Пароль")

    # Команда login
    login_parser = subparsers.add_parser("login", help="Вход в систему")
    login_parser.add_argument("--username", required=True, help="Имя пользователя")
    login_parser.add_argument("--password", required=True, help="Пароль")

    # Команда logout
    logout_parser = subparsers.add_parser("logout", help="Выход из системы")

    # Команда show-portfolio
    portfolio_parser = subparsers.add_parser("show-portfolio", help="Показать портфель")
    portfolio_parser.add_argument(
        "--base", help="Базовая валюта (по умолчанию USD)"
    )

    # Команда buy
    buy_parser = subparsers.add_parser("buy", help="Купить валюту")
    buy_parser.add_argument(
        "--currency", required=True, help="Код покупаемой валюты (например, BTC)"
    )
    buy_parser.add_argument(
        "--amount", type=float, required=True, help="Количество покупаемой валюты"
    )

    # Команда sell
    sell_parser = subparsers.add_parser("sell", help="Продать валюту")
    sell_parser.add_argument("--currency", required=True, help="Код продаваемой валюты")
    sell_parser.add_argument(
        "--amount", type=float, required=True, help="Количество продаваемой валюты"
    )

    # Команда get-rate
    rate_parser = subparsers.add_parser("get-rate", help="Получить курс валюты")
    rate_parser.add_argument(
        "--from", dest="from_currency", help="Исходная валюта"
    )
    rate_parser.add_argument(
        "--to", dest="to_currency", help="Целевая валюта"
    )
    rate_parser.add_argument(
        "--list", action="store_true", help="Показать список поддерживаемых валют"
    )

    # Если аргументы не переданы, показываем справку
    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args()
    except SystemExit:
        return 1

    # Выполняем команду
    if args.command == "register":
        return register_command(args)
    elif args.command == "login":
        return login_command(args)
    elif args.command == "logout":
        return logout_command(args)
    elif args.command == "show-portfolio":
        return show_portfolio_command(args)
    elif args.command == "buy":
        return buy_command(args)
    elif args.command == "sell":
        return sell_command(args)
    elif args.command == "get-rate":
        return get_rate_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
