import re
from typing import List, Set


class SeedGenerator:
    TRANSACTIONAL = [
        "купить", "заказать", "цена", "стоимость", "прайс", "скидка", "акция",
        "в наличии", "доставка", "срочно", "сегодня", "ночью", "недорого"
    ]
    
    LOCALIZATION = [
        "москва", "спб", "рядом", "около", "24/7", "круглосуточно",
        "с выездом", "на дом", "в офис"
    ]
    
    CONSTRAINTS = [
        "недорого", "дешево", "срочно", "быстро", "ночью", "рассрочка",
        "гарантия", "возврат", "чек", "официально", "с документами"
    ]
    
    QUESTIONS = [
        "как выбрать", "где купить", "сколько стоит", "какой лучше",
        "что лучше", "отличия", "сравнение", "обзор"
    ]
    
    SEASONS = [
        "черная пятница", "новый год", "8 марта", "23 февраля",
        "день рождения", "праздник", "распродажа"
    ]

    def __init__(self, niche: str, seed_targets: List[str] = None):
        self.niche = niche.lower()
        self.seed_targets = seed_targets or []
        self.generated_seeds = set()

    def generate(self, count: int = 50) -> List[str]:
        seeds = []
        
        if self.seed_targets:
            seeds.extend(self.seed_targets[:count // 2])
        
        base_phrases = self._extract_base_phrases()
        
        for base in base_phrases[:5]:
            seeds.extend(self._generate_transactional(base))
            seeds.extend(self._generate_localized(base))
            seeds.extend(self._generate_constrained(base))
            seeds.extend(self._generate_questions(base))
            seeds.extend(self._generate_seasonal(base))
        
        seeds = self._deduplicate(seeds)
        seeds = self._filter_quality(seeds)
        
        return seeds[:count]

    def _extract_base_phrases(self) -> List[str]:
        words = re.findall(r'\b\w+\b', self.niche)
        
        phrases = []
        if len(words) >= 2:
            phrases.append(' '.join(words[:2]))
        if len(words) >= 3:
            phrases.append(' '.join(words[:3]))
        phrases.append(' '.join(words))
        
        return phrases

    def _generate_transactional(self, base: str) -> List[str]:
        seeds = []
        for intent in self.TRANSACTIONAL[:8]:
            seeds.append(f"{intent} {base}")
            seeds.append(f"{base} {intent}")
        return seeds

    def _generate_localized(self, base: str) -> List[str]:
        seeds = []
        for location in self.LOCALIZATION[:6]:
            for intent in ["купить", "заказать", "доставка"]:
                seeds.append(f"{intent} {base} {location}")
        return seeds

    def _generate_constrained(self, base: str) -> List[str]:
        seeds = []
        for constraint in self.CONSTRAINTS[:8]:
            seeds.append(f"{base} {constraint}")
            for intent in ["купить", "заказать"]:
                seeds.append(f"{intent} {base} {constraint}")
        return seeds

    def _generate_questions(self, base: str) -> List[str]:
        seeds = []
        for question in self.QUESTIONS[:6]:
            seeds.append(f"{question} {base}")
        return seeds

    def _generate_seasonal(self, base: str) -> List[str]:
        seeds = []
        for season in self.SEASONS[:5]:
            seeds.append(f"{base} {season}")
            seeds.append(f"{base} на {season}")
        return seeds

    def _deduplicate(self, seeds: List[str]) -> List[str]:
        seen = set()
        unique = []
        for seed in seeds:
            normalized = ' '.join(sorted(seed.lower().split()))
            if normalized not in seen:
                seen.add(normalized)
                unique.append(seed)
        return unique

    def _filter_quality(self, seeds: List[str]) -> List[str]:
        filtered = []
        for seed in seeds:
            words = seed.split()
            if len(words) >= 2 and len(seed) >= 10:
                filtered.append(seed)
        return filtered
