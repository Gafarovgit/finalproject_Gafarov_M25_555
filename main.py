# main.py
"""
Главная точка входа приложения ValutaTrade Hub.
Поддерживает два режима работы: CLI и Parser Service.
"""
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='ValutaTrade Hub - Платформа для торговли валютами'
    )
    parser.add_argument(
        '--mode',
        choices=['cli', 'parser'],
        default='cli',
        help='Режим работы (cli - основной интерфейс, parser - сервис парсинга)'
    )
    
    # Проверяем, есть ли аргумент --mode
    args_to_check = sys.argv[1:] if len(sys.argv) > 1 else []
    has_mode_arg = any(arg.startswith('--mode=') for arg in args_to_check)
    
    if has_mode_arg:
        # Если передан режим parser, передаем аргументы парсер-сервису
        sys.argv = [sys.argv[0]] + [arg for arg in args_to_check if not arg.startswith('--mode=')]
        
        if '--mode=parser' in sys.argv:
            sys.argv.remove('--mode=parser')
        
        from valutatrade_hub.parser_service.__main__ import main as parser_main
        parser_main()
    else:
        # Работаем в режиме CLI
        from valutatrade_hub.cli.interface import main as cli_main
        cli_main()


if __name__ == '__main__':
    main()