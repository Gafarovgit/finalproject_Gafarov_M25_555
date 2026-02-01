#!/usr/bin/env python3
"""
Точка входа для парсер-сервиса.
Может использоваться для запуска как отдельное приложение.
"""
import argparse
import sys
from valutatrade_hub.parser_service.usecases import ParserUseCases


def main():
    parser = argparse.ArgumentParser(
        description='Parser Service - Сервис обновления курсов валют'
    )
    subparsers = parser.add_subparsers(dest='command', help='Команды')
    
    # Команда update
    update_parser = subparsers.add_parser('update', help='Обновить курсы валют')
    update_parser.add_argument(
        '--source',
        choices=['coingecko', 'exchangerate'],
        help='Обновить только из указанного источника'
    )
    
    # Команда status
    subparsers.add_parser('status', help='Показать статус парсер-сервиса')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        usecases = ParserUseCases()
        
        if args.command == 'update':
            result = usecases.update_rates(args.source)
            print(f"Обновление завершено. Получено курсов: {sum(result['results'].values())}")
            print(f"Источники: {', '.join(result['results'].keys())}")
            
        elif args.command == 'status':
            rates_data = usecases.show_rates()
            freshness = usecases.updater.check_freshness()
            
            print(f"Статус парсер-сервиса:")
            print(f"  Всего курсов в кэше: {rates_data.get('total', 0)}")
            last_refresh = rates_data.get('last_refresh')
            if last_refresh is None:
                last_refresh = 'Никогда'
            print(f"  Последнее обновление: {last_refresh}")
            print(f"  Свежесть данных: {freshness[1]}")
            
    except Exception as e:
        print(f"Ошибка: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
