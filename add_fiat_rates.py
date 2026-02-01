import json
import datetime
import sys

# Популярные фиатные валюты и их примерные курсы
FIAT_RATES = {
    "EUR_USD": 1.0821,
    "GBP_USD": 1.2628,
    "JPY_USD": 0.0067,
    "CAD_USD": 0.7412,
    "AUD_USD": 0.6589,
    "CHF_USD": 1.1284,
    "CNY_USD": 0.1389,
    "RUB_USD": 0.0108,
}

def add_fiat_rates():
    try:
        # Загружаем существующие курсы
        with open('data/rates.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"pairs": {}, "last_refresh": None}
    except json.JSONDecodeError:
        print("Ошибка чтения rates.json, создаем новый файл")
        data = {"pairs": {}, "last_refresh": None}
    
    # Добавляем или обновляем фиатные курсы
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    added = 0
    updated = 0
    
    for pair, rate in FIAT_RATES.items():
        if pair not in data["pairs"]:
            data["pairs"][pair] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": "ExchangeRate-API (mocked)"
            }
            added += 1
        else:
            data["pairs"][pair]["rate"] = rate
            data["pairs"][pair]["updated_at"] = timestamp
            data["pairs"][pair]["source"] = "ExchangeRate-API (mocked)"
            updated += 1
    
    data["last_refresh"] = timestamp
    
    # Сохраняем
    with open('data/rates.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Добавлено: {added}, Обновлено: {updated}, Всего пар: {len(data['pairs'])}")
    print(f"Обновление завершено: {timestamp}")

if __name__ == "__main__":
    add_fiat_rates()
