# valutatrade_hub/parser_service/storage.py
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import shutil


class StorageManager:
    """Менеджер хранения данных парсер-сервиса."""
    
    def __init__(self, rates_file_path: str, history_file_path: str):
        """
        Инициализация менеджера хранилища.
        
        Args:
            rates_file_path: путь к файлу с актуальными курсами (rates.json)
            history_file_path: путь к файлу с историческими данными (exchange_rates.json)
        """
        self.rates_file_path = Path(rates_file_path)
        self.history_file_path = Path(history_file_path)
        
        # Создаем директории, если они не существуют
        self.rates_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _atomic_write(self, file_path: Path, data: Any) -> None:
        """Атомарная запись данных в файл через временный файл.
        
        Args:
            file_path: путь к целевому файлу
            data: данные для записи
        """
        # Создаем временный файл в той же директории
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix=f".{file_path.name}.tmp",
            suffix=".json"
        )
        
        try:
            # Записываем данные во временный файл
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
            
            # Перемещаем временный файл в целевой
            shutil.move(temp_path, file_path)
        except Exception as e:
            # В случае ошибки удаляем временный файл
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
    
    def load_rates(self) -> Dict[str, Any]:
        """Загрузить актуальные курсы из rates.json.
        
        Returns:
            Словарь с актуальными курсами или пустой словарь при ошибке
        """
        try:
            if not self.rates_file_path.exists():
                return {"pairs": {}, "last_refresh": None}
            
            with open(self.rates_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # Если файл поврежден, возвращаем пустую структуру
            return {"pairs": {}, "last_refresh": None}
    
    def save_rates(self, rates: Dict[str, float], source: str) -> None:
        """Сохранить актуальные курсы в rates.json.
        
        Args:
            rates: словарь с курсами валютных пар
            source: источник данных (например, "CoinGecko" или "ExchangeRate-API")
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Преобразуем курсы в формат для хранения
        pairs_data = {}
        for pair, rate in rates.items():
            pairs_data[pair] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": source
            }
        
        # Структура файла rates.json
        data = {
            "pairs": pairs_data,
            "last_refresh": timestamp
        }
        
        # Атомарная запись
        self._atomic_write(self.rates_file_path, data)
    
    def save_to_history(self, rates: Dict[str, float], source: str) -> None:
        """Сохранить курсы в исторический файл exchange_rates.json.
        
        Args:
            rates: словарь с курсами валютных пар
            source: источник данных
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        history_entries = []
        
        # Создаем записи для каждой валютной пары
        for pair, rate in rates.items():
            # Разделяем пару на from_currency и to_currency
            parts = pair.split("_")
            if len(parts) != 2:
                continue
            
            from_currency, to_currency = parts
            
            # Создаем уникальный ID
            entry_id = f"{pair}_{timestamp.replace(':', '-').replace('.', '-')}"
            
            entry = {
                "id": entry_id,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": rate,
                "timestamp": timestamp,
                "source": source,
                "meta": {
                    "request_timestamp": timestamp,
                    "source_api": source
                }
            }
            history_entries.append(entry)
        
        if not history_entries:
            return
        
        # Загружаем существующую историю
        existing_history = self.load_history()
        
        # Добавляем новые записи
        existing_history.extend(history_entries)
        
        # Сохраняем (максимум 1000 последних записей)
        if len(existing_history) > 1000:
            existing_history = existing_history[-1000:]
        
        # Атомарная запись
        self._atomic_write(self.history_file_path, existing_history)
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Загрузить исторические данные из exchange_rates.json.
        
        Returns:
            Список исторических записей или пустой список при ошибке
        """
        try:
            if not self.history_file_path.exists():
                return []
            
            with open(self.history_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def get_latest_rates(self) -> Dict[str, Dict[str, Any]]:
        """Получить последние актуальные курсы.
        
        Returns:
            Словарь с последними курсами для каждой валютной пары
        """
        rates_data = self.load_rates()
        return rates_data.get("pairs", {})
    
    def get_rate(self, pair: str) -> Optional[Dict[str, Any]]:
        """Получить курс для конкретной валютной пары.
        
        Args:
            pair: валютная пара (например, "BTC_USD")
            
        Returns:
            Словарь с данными курса или None, если курс не найден
        """
        rates = self.get_latest_rates()
        return rates.get(pair)
    
    def get_history_for_pair(self, pair: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Получить историю курсов для конкретной валютной пары.
        
        Args:
            pair: валютная пара
            limit: максимальное количество записей
            
        Returns:
            Список исторических записей
        """
        history = self.load_history()
        
        # Фильтруем записи по паре и сортируем по времени (новые сверху)
        filtered = [
            entry for entry in history 
            if f"{entry['from_currency']}_{entry['to_currency']}" == pair
        ]
        
        # Сортируем по времени (новые первые)
        filtered.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return filtered[:limit]