#!/usr/bin/env python3
"""
Проверка реализации класса User
"""

import os
import sys

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def inspect_user_class():
    """Инспектирует класс User для понимания его структуры."""
    print("Инспекция класса User...")

    try:
        # Проверяем сигнатуру конструктора
        import inspect

        from valutatrade_hub.core.models import User
        sig = inspect.signature(User.__init__)
        print(f"Сигнатура конструктора User: {sig}")

        # Проверяем атрибуты класса
        print("\nАтрибуты класса User:")
        user_instance = User.__new__(User)

        # Пытаемся создать экземпляр с разными параметрами
        test_cases = [
            {
                'args': (1, "testuser", "testpass"),
                'desc': '3 аргумента (user_id, username, password)'
            },
            {
                'args': (1, "testuser", "hashedpass", "salt"),
                'desc': '4 аргумента'
            },
            {
                'args': (1, "testuser", "hashedpass", "salt", "2024-01-01"),
                'desc': '5 аргументов'
            }
        ]

        for i, test in enumerate(test_cases, 1):
            try:
                user = User(*test['args'])
                print(f"✓ Тест {i}: {test['desc']} - УСПЕХ")
                print(f"  Атрибуты: {[attr for attr in dir(user) if not attr.startswith('__')]}")
            except Exception as e:
                print(f"✗ Тест {i}: {test['desc']} - ОШИБКА: {e}")

        return True

    except Exception as e:
        print(f"Ошибка при инспекции класса User: {e}")
        return False

def check_user_implementation():
    """Проверяет соответствие класса User требованиям ТЗ."""
    print("\n" + "="*60)
    print("Проверка соответствия класса User ТЗ")
    print("="*60)

    try:
        # Читаем исходный код класса User
        import inspect

        from valutatrade_hub.core.models import User
        source = inspect.getsource(User.__init__)
        print("Исходный код конструктора User:")
        print("-"*40)
        print(source)
        print("-"*40)

        # Проверяем наличие необходимых атрибутов
        required_attrs = ['_user_id', '_username', '_hashed_password', '_salt', '_registration_date']

        # Пытаемся создать пользователя с параметрами из ТЗ
        print("\nПопытка создания User с параметрами из ТЗ:")
        print("Параметры: user_id=1, username='alice', hashed_password='hash123', salt='salt123', registration_date='2024-01-01T12:00:00'")

        try:
            user = User(
                user_id=1,
                username="alice",
                hashed_password="hash123",
                salt="salt123",
                registration_date="2024-01-01T12:00:00"
            )
            print("✓ Успешно создан объект User")

            # Проверяем атрибуты
            attrs_found = []
            for attr in required_attrs:
                if hasattr(user, attr):
                    attrs_found.append(attr)
                    print(f"✓ Найден атрибут: {attr}")
                else:
                    print(f"✗ Отсутствует атрибут: {attr}")

            if len(attrs_found) == len(required_attrs):
                print("\n✓ Все необходимые атрибуты присутствуют")
                return True
            else:
                print(f"\n✗ Отсутствуют атрибуты: {set(required_attrs) - set(attrs_found)}")
                return False

        except Exception as e:
            print(f"✗ Ошибка при создании User: {e}")
            print("\nРекомендация: нужно обновить конструктор User, чтобы он принимал:")
            print("  __init__(self, user_id, username, hashed_password, salt, registration_date)")
            return False

    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def main():
    """Основная функция проверки."""
    print("="*60)
    print("ДИАГНОСТИКА ПРОБЛЕМ С КЛАССОМ USER")
    print("="*60)

    # Инспекция класса
    inspect_success = inspect_user_class()

    # Проверка реализации
    implementation_success = check_user_implementation()

    print("\n" + "="*60)
    print("РЕКОМЕНДАЦИИ:")
    print("="*60)

    if not inspect_success:
        print("1. Класс User не найден или не может быть импортирован")
        print("2. Проверьте файл valutatrade_hub/core/models.py")
    elif not implementation_success:
        print("1. Конструктор User не соответствует ТЗ")
        print("2. Обновите конструктор, чтобы он принимал 5 параметров:")
        print("   - user_id: int")
        print("   - username: str")
        print("   - hashed_password: str")
        print("   - salt: str")
        print("   - registration_date: str или datetime")
    else:
        print("✓ Класс User соответствует ТЗ")

    return 0 if implementation_success else 1

if __name__ == "__main__":
    sys.exit(main())
