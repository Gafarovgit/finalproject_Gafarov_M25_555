#!/bin/bash
echo "=== Проверка всех критериев оценки проекта ==="
echo ""

# 1. Проверка структуры
echo "1. 📁 Проверка структуры проекта..."
required_files=(
    "pyproject.toml"
    "Makefile"
    "README.md"
    "main.py"
    "valutatrade_hub/core/__init__.py"
    "valutatrade_hub/infra/__init__.py"
    "valutatrade_hub/cli/__init__.py"
    "valutatrade_hub/parser_service/__init__.py"
    "data/rates.json"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file"
        missing_files=$((missing_files + 1))
    fi
done

# 2. Проверка Poetry
echo -e "\n2. ⚙️ Проверка Poetry..."
if command -v poetry &> /dev/null; then
    echo "  ✅ Poetry установлен"
    
    # Проверка зависимостей
    if poetry show requests &> /dev/null; then
        echo "  ✅ Зависимости установлены"
    else
        echo "  ❌ Зависимости не установлены"
    fi
else
    echo "  ❌ Poetry не установлен"
fi

# 3. Проверка Makefile
echo -e "\n3. 🔧 Проверка Makefile..."
make_targets=("install" "project" "build" "publish" "package-install" "lint")
for target in "${make_targets[@]}"; do
    if grep -q "^$target:" Makefile; then
        echo "  ✅ $target"
    else
        echo "  ❌ $target"
    fi
done

# 4. Проверка линтера
echo -e "\n4. 🧹 Проверка линтера..."
make lint > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ make lint проходит успешно"
else
    echo "  ❌ make lint находит ошибки"
fi

# 5. Проверка импортов
echo -e "\n5. 🔄 Проверка импортов..."
python3 -c "from valutatrade_hub.cli.interface import main; print('  ✅ CLI интерфейс импортируется')" 2>/dev/null || echo "  ❌ Ошибка импорта CLI"
python3 -c "from valutatrade_hub.parser_service.usecases import ParserUseCases; print('  ✅ Парсер-сервис импортируется')" 2>/dev/null || echo "  ❌ Ошибка импорта парсера"

# 6. Проверка команд CLI
echo -e "\n6. 📟 Проверка команд CLI..."
commands=("register" "login" "logout" "show-portfolio" "buy" "sell" "get-rate" "update-rates" "show-rates")
for cmd in "${commands[@]}"; do
    if poetry run project --help 2>/dev/null | grep -q "$cmd"; then
        echo "  ✅ $cmd"
    else
        echo "  ❌ $cmd"
    fi
done

# 7. Проверка парсер-сервиса
echo -e "\n7. 📊 Проверка парсер-сервиса..."
if [ -f "data/rates.json" ]; then
    pair_count=$(python3 -c "import json; data=json.load(open('data/rates.json')); print(len(data.get('pairs', {})))" 2>/dev/null || echo "0")
    echo "  ✅ В кэше $pair_count курсов"
else
    echo "  ❌ Файл rates.json не найден"
fi

# Итог
echo -e "\n📊 ИТОГОВАЯ СТАТИСТИКА:"
echo "=" * 40
echo "Всего проверок: 7 категорий"
echo "Рекомендуется:"
echo "1. Запустить демо: ./examples/demo_workflow.sh"
echo "2. Проверить тесты: ./examples/test_api.py"
echo "3. Изучить критерии: cat CRITERIA.md"
echo "=" * 40
