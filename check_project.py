#!/usr/bin/env python3
"""
Тестовый скрипт для проверки текущего состояния проекта.
Проверяет корректность структуры и базовую функциональность.
"""

import json
import os
import sys


def check_project_structure():
    """Проверяет базовую структуру проекта."""
    print("=" * 60)
    print("Проверка структуры проекта")
    print("=" * 60)

    required_dirs = [
        "data",
        "valutatrade_hub",
        "valutatrade_hub/core",
        "valutatrade_hub/cli",
        "valutatrade_hub/infra"
    ]

    required_files = [
        "pyproject.toml",
        "Makefile",
        "main.py",
        "valutatrade_hub/__init__.py",
        "valutatrade_hub/core/__init__.py",
        "valutatrade_hub/cli/__init__.py",
        "valutatrade_hub/infra/__init__.py",
        "data/users.json",
        "data/portfolios.json",
        "data/rates.json"
    ]

    all_ok = True

    # Проверка директорий
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ Директория {dir_path} существует")
        else:
            print(f"✗ Директория {dir_path} отсутствует")
            all_ok = False

    # Проверка файлов
    for file_path in required_files:
        if os.path.isfile(file_path):
            print(f"✓ Файл {file_path} существует")
        else:
            print(f"✗ Файл {file_path} отсутствует")
            all_ok = False

    return all_ok

def check_python_files():
    """Проверяет корректность Python файлов."""
    print("\n" + "=" * 60)
    print("Проверка Python файлов")
    print("=" * 60)

    python_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    all_ok = True

    for py_file in python_files[:10]:  # Проверим первые 10 файлов
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Проверка синтаксиса
            compile(content, py_file, 'exec')
            print(f"✓ {py_file} - синтаксис корректен")

            # Проверка на соответствие PEP8 (базовые проверки)
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    print(f"  Внимание: строка {i} в {py_file} превышает 120 символов")

        except SyntaxError as e:
            print(f"✗ {py_file} - синтаксическая ошибка: {e}")
            all_ok = False
        except Exception as e:
            print(f"✗ {py_file} - ошибка при чтении: {e}")
            all_ok = False

    return all_ok

def check_json_files():
    """Проверяет корректность JSON файлов."""
    print("\n" + "=" * 60)
    print("Проверка JSON файлов")
    print("=" * 60)

    json_files = [
        "data/users.json",
        "data/portfolios.json",
        "data/rates.json"
    ]

    all_ok = True

    for json_file in json_files:
        if not os.path.isfile(json_file):
            print(f"✗ {json_file} - файл не существует")
            all_ok = False
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✓ {json_file} - JSON корректен")

            # Базовая проверка структуры
            if json_file == "data/users.json" and not isinstance(data, list):
                print(f"  Внимание: {json_file} должен содержать список")

            if json_file == "data/portfolios.json" and not isinstance(data, list):
                print(f"  Внимание: {json_file} должен содержать список")

        except json.JSONDecodeError as e:
            print(f"✗ {json_file} - ошибка JSON: {e}")
            all_ok = False
        except Exception as e:
            print(f"✗ {json_file} - ошибка при чтении: {e}")
            all_ok = False

    return all_ok

def check_imports():
    """Проверяет возможность импорта основных модулей."""
    print("\n" + "=" * 60)
    print("Проверка импортов")
    print("=" * 60)

    imports_to_test = [
        ("valutatrade_hub.core.models", "User"),
        ("valutatrade_hub.core.models", "Wallet"),
        ("valutatrade_hub.core.models", "Portfolio"),
        ("valutatrade_hub.cli.interface", "main"),
    ]

    all_ok = True

    for module_name, class_name in imports_to_test:
        try:
            # Добавляем текущую директорию в путь Python
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

            module = __import__(module_name, fromlist=[class_name])
            if hasattr(module, class_name):
                print(f"✓ Модуль {module_name} успешно импортирован, класс {class_name} найден")
            else:
                print(f"✗ Модуль {module_name} импортирован, но класс {class_name} не найден")
                all_ok = False

        except ImportError as e:
            print(f"✗ Ошибка импорта {module_name}.{class_name}: {e}")
            all_ok = False
        except Exception as e:
            print(f"✗ Неизвестная ошибка при импорте {module_name}.{class_name}: {e}")
            all_ok = False

    return all_ok

def check_makefile():
    """Проверяет корректность Makefile."""
    print("\n" + "=" * 60)
    print("Проверка Makefile")
    print("=" * 60)

    makefile_path = "Makefile"

    if not os.path.isfile(makefile_path):
        print("✗ Makefile не существует")
        return False

    try:
        with open(makefile_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_targets = ["install", "project", "build", "publish", "package-install", "lint"]
        present_targets = []

        for line in content.split('\n'):
            line = line.strip()
            if line.endswith(':'):
                target = line[:-1].strip()
                present_targets.append(target)

        all_ok = True
        for target in required_targets:
            if target in present_targets:
                print(f"✓ Цель '{target}' найдена в Makefile")
            else:
                print(f"✗ Цель '{target}' отсутствует в Makefile")
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"✗ Ошибка при чтении Makefile: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("Запуск проверки проекта...\n")

    tests = [
        ("Структура проекта", check_project_structure),
        ("Python файлы", check_python_files),
        ("JSON файлы", check_json_files),
        ("Импорты", check_imports),
        ("Makefile", check_makefile),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Ошибка при выполнении теста '{test_name}': {e}")
            results.append((test_name, False))

    # Вывод итогов
    print("\n" + "=" * 60)
    print("ИТОГИ ПРОВЕРКИ")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ ПРОЙДЕН" if result else "✗ ПРОВАЛЕН"
        print(f"{test_name}: {status}")

    print(f"\nПройдено тестов: {passed}/{total}")

    if passed == total:
        print("\nВсе проверки пройдены успешно!")
        return 0
    else:
        print(f"\nНайдены проблемы в {total - passed} тестах")
        return 1

if __name__ == "__main__":
    sys.exit(main())
