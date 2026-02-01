#!/bin/bash
echo "=== Финальный тест парсер-сервиса v2 ==="
echo ""

echo "1. Проверка статуса парсера:"
poetry run python main.py --mode=parser status

echo -e "\n2. Показ всех курсов:"
poetry run project show-rates

echo -e "\n3. Показ топ-5 криптовалют:"
poetry run project show-rates --top 5

echo -e "\n4. Показ курсов для EUR:"
poetry run project show-rates --currency EUR

echo -e "\n5. Получение курса BTC/USD:"
poetry run project get-rate --from BTC --to USD

echo -e "\n6. Получение курса USD/EUR:"
poetry run project get-rate --from USD --to EUR

echo -e "\n7. Обновление курсов:"
poetry run project update-rates

echo -e "\n8. Проверка статуса после обновления:"
poetry run python main.py --mode=parser status

echo -e "\n=== Тест завершен ==="
