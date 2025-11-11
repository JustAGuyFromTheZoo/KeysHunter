import csv
import json
from typing import List, Dict
from datetime import datetime


class Exporter:
    @staticmethod
    def to_csv(keywords: List[Dict], filename: str):
        if not keywords:
            return
        
        fieldnames = [
            "word", "wsk", "ws", "numwords", "isquest", "isgeo",
            "adscnt", "avbid", "docs", "cnt"
        ]
        
        available_fields = set(keywords[0].keys())
        fieldnames = [f for f in fieldnames if f in available_fields]
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for kw in keywords:
                row = {}
                for field in fieldnames:
                    value = kw.get(field)
                    if field == "word":
                        value = kw.get("destination_key") or kw.get("word", "")
                    row[field] = value
                writer.writerow(row)
        
        print(f"💾 CSV сохранен: {filename}")

    @staticmethod
    def to_json(keywords: List[Dict], filename: str):
        clean_keywords = []
        for kw in keywords:
            clean_kw = kw.copy()
            if "destination_key" in clean_kw:
                clean_kw["word"] = clean_kw.pop("destination_key")
            clean_keywords.append(clean_kw)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(clean_keywords, f, ensure_ascii=False, indent=2)
        
        print(f"💾 JSON сохранен: {filename}")

    @staticmethod
    def generate_report(keywords: List[Dict], seeds: List[str], config) -> str:
        report = []
        report.append("=" * 80)
        report.append(f"НЧ-ключи по нише: {config.niche}")
        report.append(f"База: {config.base} · Порог WSK: <={config.wsk_threshold} · Мин. слов: >={config.min_num_words}")
        report.append("=" * 80)
        report.append("")
        
        top_n = min(config.return_top, len(keywords))
        report.append(f"📊 ТОП-{top_n} КЛЮЧЕЙ:")
        report.append("-" * 80)
        
        for i, kw in enumerate(keywords[:top_n], 1):
            word = kw.get("destination_key") or kw.get("word", "")
            wsk = kw.get("wsk", 0)
            numwords = kw.get("numwords", 0)
            report.append(f"{i}. {word}")
            report.append(f"   └─ wsk: {wsk} · слов: {numwords}")
        
        report.append("")
        report.append("=" * 80)
        report.append(f"🌱 СГЕНЕРИРОВАННЫЕ СЕМЕНА ({len(seeds)}):")
        report.append("-" * 80)
        
        for i, seed in enumerate(seeds[:30], 1):
            report.append(f"{i}. {seed}")
        
        if len(seeds) > 30:
            report.append(f"... и еще {len(seeds) - 30} семян")
        
        report.append("")
        report.append("=" * 80)
        report.append("📈 СТАТИСТИКА:")
        report.append("-" * 80)
        report.append(f"Семян сгенерировано: {len(seeds)}")
        report.append(f"Ключей собрано: {len(keywords)}")
        report.append(f"Средний WSK: {sum(kw.get('wsk', 0) for kw in keywords) / len(keywords):.0f}")
        report.append(f"Средняя длина: {sum(kw.get('numwords', 0) for kw in keywords) / len(keywords):.1f} слов")
        
        stop_words_filtered = sum(1 for kw in keywords if any(
            sw in (kw.get("destination_key") or kw.get("word", "")).lower() 
            for sw in config.stop_words
        ))
        report.append(f"Отфильтровано стоп-словами: ~{stop_words_filtered}")
        
        report.append("")
        report.append("=" * 80)
        report.append(f"Отчет сгенерирован: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        return "\n".join(report)
