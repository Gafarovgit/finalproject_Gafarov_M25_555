"""Командный интерфейс приложения."""

import argparse
import json
import sys
from datetime import datetime

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
from valutatrade_hub.parser_service.usecases import ParserUseCases


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
        # Используем парсер-сервис для получения курса
        parser_usecases = ParserUseCases()
        rate_data = parser_usecases.get_rate(from_curr, to_curr)

        if args.json:
            print(json.dumps(rate_data, indent=2, ensure_ascii=False))
            return 0

        print(f"Курс {from_curr}→{to_curr}: {rate_data['rate']:.6f}")
        print(f"Обратный курс {to_curr}→{from_curr}: {rate_data['inverse_rate']:.6f}")
        print(f"Источник: {rate_data['source']}")
        print(f"Обновлено: {rate_data['updated_at']}")
        
        if not rate_data['is_fresh']:
            print("⚠️  Данные могут быть устаревшими. Используйте 'update-rates' для обновления.")
            
        return 0

    except CurrencyNotFoundError as e:
        print(f"❌ {str(e)}")
        print("Используйте команду 'get-rate --list' для просмотра поддерживаемых валют")
        return 1
    except ApiRequestError as e:
        print(f"❌ {str(e)}")
        print("Повторите попытку позже или используйте 'update-rates' для обновления данных")
        return 1
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return 1


def update_rates_command(args):
    """Обработка команды update-rates."""
    try:
        parser_usecases = ParserUseCases()
        result = parser_usecases.update_rates(args.source)
        
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        
        if result["success"]:
            print("✅ Обновление курсов выполнено успешно!")
            print("\n📊 Результаты:")
            
            table = PrettyTable()
            table.field_names = ["Источник", "Курсов получено", "Статус"]
            
            for source, count in result["results"].items():
                status = "✅ Успех" if count > 0 else "❌ Ошибка"
                table.add_row([source.capitalize(), count, status])
            
            print(table)
            print(f"\n🕒 Последнее обновление: {result['summary'].get('last_refresh', 'Неизвестно')}")
            print(f"📈 Всего пар в кэше: {result['summary'].get('total_pairs', 0)}")
        else:
            print("❌ Не удалось получить курсы ни из одного источника")
            print("Проверьте подключение к интернету и настройки API.")
            
        return 0
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении курсов: {str(e)}")
        print("Проверьте настройки API в файле .env")
        return 1


def show_rates_command(args):
    """Обработка команды show-rates."""
    try:
        parser_usecases = ParserUseCases()
        result = parser_usecases.show_rates(
            currency=args.currency,
            top=args.top,
            base=args.base
        )
        
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        
        if not result["rates"]:
            print(result.get("message", "Нет данных для отображения"))
            return 0
        
        print(f"📊 Актуальные курсы (базовая валюта: {result['base_currency']})")
        print(f"🕒 Последнее обновление: {result.get('last_refresh', 'Неизвестно')}")
        print(f"📈 Всего пар: {result['total']}")
        print()
        
        table = PrettyTable()
        table.field_names = ["Валютная пара", "Курс", "Обновлено", "Источник"]
        
        for pair, data in result["rates"].items():
            # Форматируем дату для удобного чтения
            updated_at = data["updated_at"]
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    updated_str = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    updated_str = updated_at
            else:
                updated_str = "Неизвестно"
            
            table.add_row([
                pair,
                data["formatted_rate"],
                updated_str,
                data["source"]
            ])
        
        print(table)
        return 0
        
    except CurrencyNotFoundError as e:
        print(f"❌ {str(e)}")
        print("Используйте команду 'show-rates' без параметров для списка всех валют.")
        return 1
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
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

    # Команда get-rate (обновленная)
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
    rate_parser.add_argument(
        "--json", action="store_true", help="Вывести результат в формате JSON"
    )

    # Команда update-rates (новая)
    update_rates_parser = subparsers.add_parser(
        "update-rates", help="Обновить курсы валют из внешних источников"
    )
    update_rates_parser.add_argument(
        "--source",
        choices=["coingecko", "exchangerate"],
        help="Обновить только из указанного источника"
    )
    update_rates_parser.add_argument(
        "--json", action="store_true", help="Вывести результат в формате JSON"
    )

    # Команда show-rates (новая)
    show_rates_parser = subparsers.add_parser(
        "show-rates", help="Показать актуальные курсы из кэша"
    )
    show_rates_parser.add_argument(
        "--currency", "-c", help="Показать курсы только для указанной валюты"
    )
    show_rates_parser.add_argument(
        "--top", type=int, help="Показать N самых дорогих криптовалют"
    )
    show_rates_parser.add_argument(
        "--base", default="USD", help="Базовая валюта для отображения (по умолчанию: USD)"
    )
    show_rates_parser.add_argument(
        "--json", action="store_true", help="Вывести результат в формате JSON"
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
    elif args.command == "update-rates":
        return update_rates_command(args)
    elif args.command == "show-rates":
        return show_rates_command(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())