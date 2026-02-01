#!/usr/bin/env python3
"""Проверка наличия функции main в interface.py."""

import os

print("=== Проверка interface.py ===")

interface_path = "valutatrade_hub/cli/interface.py"
if os.path.exists(interface_path):
    with open(interface_path, "r") as f:
        content = f.read()
        if "def main():" in content:
            print("✅ Функция main найдена в interface.py")
        else:
            print("❌ Функция main НЕ найдена в interface.py")
            print("Содержимое файла:")
            print(content[:500])
else:
    print(f"❌ Файл {interface_path} не найден")
