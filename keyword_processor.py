import re
from typing import List, Dict, Set
from api_client import KeysAPIClient


class KeywordProcessor:
    def __init__(self, api_client: KeysAPIClient, config):
        self.api = api_client
        self.config = config

    def process_pipeline(self, seeds: List[str]) -> List[Dict]:
        print(f"\n🌱 Начинаем обработку {len(seeds)} семян...")
        
        if self.config.offline_mode:
            print("\n🔌 OFFLINE режим: работа без API")
            return self._offline_mode_results(seeds)
        
        if self.config.multi_region:
            print(f"\n🌍 Мульти-регион режим: {len(self.config.regions)} регионов")
            return self._multi_region_pipeline(seeds)
        
        return self._single_region_pipeline(seeds)
    
    def _offline_mode_results(self, seeds: List[str]) -> List[Dict]:
        print(f"\n✅ Сгенерировано {len(seeds)} ключей в offline режиме")
        results = []
        for seed in seeds:
            results.append({
                "word": seed,
                "destination_key": seed,
                "wsk": 0,
                "ws": 0,
                "numwords": len(seed.split()),
                "isquest": 1 if any(q in seed.lower() for q in ["как", "где", "сколько", "что", "какой"]) else 0,
                "isgeo": 0,
                "adscnt": 0,
                "avbid": 0,
                "docs": 0,
                "cnt": 0,
                "offline": True
            })
        return results[:self.config.max_results]
    
    def _multi_region_pipeline(self, seeds: List[str]) -> List[Dict]:
        all_results = []
        
        print("\n📋 Шаг 1: Получение подсказок по всем регионам...")
        multi_suggested = self.api.suggest_multi_region(seeds, self.config.regions)
        
        all_keywords = list(set(seeds))
        for region, suggested in multi_suggested.items():
            print(f"   ✓ Регион {region}: {len(suggested)} подсказок")
            all_keywords.extend(suggested)
        
        all_keywords = list(set(all_keywords))
        print(f"   ✓ Всего уникальных: {len(all_keywords)}")
        
        print(f"\n🔄 Шаг 2: Расширение ключевых фраз...")
        extended = self._process_extended_keywords(all_keywords)
        
        print(f"\n🔍 Шаг 3: Фильтрация и очистка...")
        filtered = self._filter_keywords(extended)
        print(f"   ✓ После фильтрации: {len(filtered)} ключей")
        
        print(f"\n🎯 Шаг 4: Удаление дублей...")
        deduplicated = self._deduplicate_keywords(filtered)
        
        print(f"\n✅ Обработка завершена!")
        return deduplicated[:self.config.max_results]
    
    def _single_region_pipeline(self, seeds: List[str]) -> List[Dict]:
        print("\n📋 Шаг 1: Получение быстрых подсказок...")
        suggested = self.api.suggest(seeds, self.config.region_id)
        print(f"   ✓ Получено {len(suggested)} подсказок")
        
        all_keywords = list(set(seeds + suggested))
        
        print(f"\n🔄 Шаг 2: Расширение ключевых фраз...")
        extended = self._process_extended_keywords(all_keywords)
        
        print(f"\n🔍 Шаг 3: Фильтрация и очистка...")
        filtered = self._filter_keywords(extended)
        print(f"   ✓ После фильтрации: {len(filtered)} ключей")
        
        print(f"\n🎯 Шаг 4: Удаление дублей...")
        deduplicated = self._deduplicate_keywords(filtered)
        
        print(f"\n✅ Обработка завершена!")
        return deduplicated[:self.config.max_results]
    
    def _process_extended_keywords(self, keywords: List[str]) -> List[Dict]:
        uid = self.api.create_extended_keywords(
            base=self.config.base,
            keywords=keywords,
            similarity=30,
            delete_duplicate=True,
            additions=True
        )
        
        if not uid:
            raise Exception("❌ Не удалось создать задание на расширение")
        
        print(f"   ✓ Задание создано: {uid}")
        self.api.wait_for_extended_keywords(uid)
        
        print("\n📥 Загрузка расширенных ключей...")
        extended = self._fetch_all_keywords(uid)
        print(f"   ✓ Загружено {len(extended)} ключей")
        
        return extended
    
    def _deduplicate_keywords(self, keywords: List[Dict]) -> List[Dict]:
        words_only = [kw.get("destination_key") or kw.get("word", "") for kw in keywords]
        deduplicated_words = self.api.delete_doubles(words_only)
        
        deduplicated = []
        dedup_set = set(deduplicated_words)
        for kw in keywords:
            word = kw.get("destination_key") or kw.get("word", "")
            if word in dedup_set:
                deduplicated.append(kw)
                dedup_set.discard(word)
        
        print(f"   ✓ После дедупликации: {len(deduplicated)} ключей")
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
