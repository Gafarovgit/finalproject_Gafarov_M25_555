#!/bin/bash
echo "=== Финальный тест парсер-сервиса ==="
echo ""

echo "1. Проверка статуса парсера:"
poetry run python main.py --mode=parser status

echo -e "\n2. Показ курсов (топ-3):"
poetry run project show-rates --top 3

echo -e "\n3. Показ курсов для EUR:"
poetry run project show-rates --currency EUR

echo -e "\n4. Получение курса BTC/USD:"
poetry run project get-rate --from BTC --to USD

echo -e "\n5. Получение курса USD/EUR:"
poetry run project get-rate --from USD --to EUR

echo -e "\n6. Показ в формате JSON:"
poetry run project show-rates --json | head -20

echo -e "\n=== Тест завершен ==="
