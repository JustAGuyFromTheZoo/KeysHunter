import re
from typing import List, Dict, Set
from api_client import KeysAPIClient


class KeywordProcessor:
    def __init__(self, api_client: KeysAPIClient, config):
        self.api = api_client
        self.config = config

    def process_pipeline(self, seeds: List[str]) -> List[Dict]:
        print(f"\n🌱 Начинаем обработку {len(seeds)} семян...")
        
        print("\n📋 Шаг 1: Получение быстрых подсказок...")
        suggested = self.api.suggest(seeds, self.config.region_id)
        print(f"   ✓ Получено {len(suggested)} подсказок")
        
        all_keywords = list(set(seeds + suggested))
        
        print(f"\n🔄 Шаг 2: Расширение ключевых фраз...")
        uid = self.api.create_extended_keywords(
            base=self.config.base,
            keywords=all_keywords,
            similarity=30,
            delete_duplicate=True,
            additions=True
        )
        
        if not uid:
            raise Exception("❌ Не удалось создать задание на расширение")
        
        print(f"   ✓ Задание создано: {uid}")
        self.api.wait_for_extended_keywords(uid)
        
        print("\n📥 Шаг 3: Загрузка расширенных ключей...")
        extended = self._fetch_all_keywords(uid)
        print(f"   ✓ Загружено {len(extended)} ключей")
        
        print("\n🔍 Шаг 4: Фильтрация и очистка...")
        filtered = self._filter_keywords(extended)
        print(f"   ✓ После фильтрации: {len(filtered)} ключей")
        
        print("\n🎯 Шаг 5: Удаление дублей...")
        words_only = [kw.get("destination_key") or kw.get("word", "") for kw in filtered]
        deduplicated_words = self.api.delete_doubles(words_only)
        
        deduplicated = []
        dedup_set = set(deduplicated_words)
        for kw in filtered:
            word = kw.get("destination_key") or kw.get("word", "")
            if word in dedup_set:
                deduplicated.append(kw)
                dedup_set.discard(word)
        
        print(f"   ✓ После дедупликации: {len(deduplicated)} ключей")
        
        print("\n✅ Обработка завершена!")
        return deduplicated

    def _fetch_all_keywords(self, uid: str) -> List[Dict]:
        all_keywords = []
        page = 1
        per_page = 100
        
        filters = self._build_filters()
        
        while True:
            result = self.api.get_extended_keywords(
                uid=uid,
                page=page,
                per_page=per_page,
                filters=filters,
                sort="wsk|asc,numwords|desc"
            )
            
            data = result.get("data", [])
            if not data:
                break
            
            all_keywords.extend(data)
            
            if len(data) < per_page:
                break
            
            page += 1
        
        return all_keywords

    def _build_filters(self) -> str:
        filters = []
        
        filters.append(f"numwords>={self.config.min_num_words}")
        filters.append(f"wsk<={self.config.wsk_threshold}")
        
        if self.config.ws_threshold:
            filters.append(f"ws<={self.config.ws_threshold}")
        
        for stop_word in self.config.stop_words:
            if stop_word.strip():
                filters.append(f"destination_keyNOT LIKE{stop_word.strip()}")
        
        if self.config.safe_filters:
            filters.append("isadult=0")
        
        if self.config.ad_filters:
            filters.append(self.config.ad_filters)
        
        return "^".join(filters)

    def _filter_keywords(self, keywords: List[Dict]) -> List[Dict]:
        filtered = []
        
        for kw in keywords:
            word = kw.get("destination_key") or kw.get("word", "")
            numwords = kw.get("numwords", 0)
            wsk = kw.get("wsk", 999999)
            
            if numwords < self.config.min_num_words:
                continue
            
            if wsk > self.config.wsk_threshold:
                continue
            
            if self._contains_stop_words(word):
                continue
            
            if not self._is_valid_keyword(word):
                continue
            
            filtered.append(kw)
        
        return filtered

    def _contains_stop_words(self, text: str) -> bool:
        text_lower = text.lower()
        for stop_word in self.config.stop_words:
            if stop_word.strip() and stop_word.strip().lower() in text_lower:
                return True
        return False

    def _is_valid_keyword(self, text: str) -> bool:
        if len(text) < 5:
            return False
        
        if re.search(r'[^\w\s\-]', text):
            return False
        
        words = text.split()
        if len(set(words)) < len(words) * 0.5:
            return False
        
        return True

    def sample_validation(self, keywords: List[Dict], sample_size: int = 5):
        import random
        
        if len(keywords) < sample_size:
            sample_size = len(keywords)
        
        sample = random.sample(keywords, sample_size)
        
        print(f"\n🔬 Валидация выборки ({sample_size} ключей):")
        for kw in sample:
            word = kw.get("destination_key") or kw.get("word", "")
            dashboard = self.api.get_keyword_dashboard(self.config.base, word)
            if dashboard:
                print(f"   ✓ '{word}' - существует в базе")
            else:
                print(f"   ⚠ '{word}' - не найден")
