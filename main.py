import sys
import argparse
from datetime import datetime
from config import Config
from api_client import KeysAPIClient
from seed_generator import SeedGenerator
from keyword_processor import KeywordProcessor
from exporter import Exporter
from interactive import (
    show_menu, select_region, select_settings, 
    get_niche, get_stop_words, confirm_settings
)


def main():
    parser = argparse.ArgumentParser(
        description="Keyword Hunter - генератор НЧ ключевых фраз для SEO"
    )
    parser.add_argument("--interactive", "-i", action="store_true", help="Интерактивный режим с выбором региона")
    parser.add_argument("--niche", type=str, help="Описание ниши (1-3 предложения)")
    parser.add_argument("--base", type=str, default="msk", help="База keys.so (msk, spb, gru и т.д.)")
    parser.add_argument("--region", type=int, default=213, help="ID региона для подсказок")
    parser.add_argument("--regions", type=str, help="Несколько регионов через запятую")
    parser.add_argument("--wsk", type=int, default=80, help="Порог WSK (точная частотность)")
    parser.add_argument("--words", type=int, default=3, help="Минимальное количество слов")
    parser.add_argument("--max-results", type=int, default=1000, help="Максимум результатов")
    parser.add_argument("--minus", type=str, help="Стоп-слова через запятую")
    parser.add_argument("--top", type=int, default=50, help="Сколько ключей показать в отчете")
    parser.add_argument("--seeds-only", action="store_true", help="Только сгенерировать семена")
    parser.add_argument("--offline", action="store_true", help="Offline режим без API")
    parser.add_argument("--format", type=str, choices=["csv", "json", "both"], default="both", 
                       help="Формат экспорта")
    
    args = parser.parse_args()
    
    if args.interactive:
        run_interactive_mode()
        return
    
    config = Config.from_env()
    
    if args.niche:
        config.niche = args.niche
    if args.base:
        config.base = args.base
    if args.region:
        config.region_id = args.region
    if args.regions:
        config.multi_region = True
        config.regions = [int(r.strip()) for r in args.regions.split(",")]
    if args.wsk:
        config.wsk_threshold = args.wsk
    if args.words:
        config.min_num_words = args.words
    if args.max_results:
        config.max_results = args.max_results
    if args.minus:
        config.stop_words = [w.strip() for w in args.minus.split(",")]
    if args.top:
        config.return_top = args.top
    if args.offline:
        config.offline_mode = True
    
    run_processing(config, args.seeds_only, args.format)


def run_interactive_mode():
    show_menu()
    
    base, regions, multi_region = select_region()
    niche = get_niche()
    stop_words = get_stop_words()
    settings = select_settings()
    
    config = Config.from_env()
    config.niche = niche
    config.base = base
    config.stop_words = stop_words
    config.multi_region = multi_region
    config.wsk_threshold = settings["wsk_threshold"]
    config.min_num_words = settings["min_num_words"]
    config.max_results = settings["max_results"]
    config.return_top = settings["return_top"]
    config.offline_mode = settings["offline_mode"]
    
    if multi_region:
        config.regions = regions
    else:
        config.region_id = regions[0]
    
    config_dict = {
        "ниша": config.niche,
        "регион": base,
        "мульти-регион": multi_region,
        "WSK порог": config.wsk_threshold,
        "мин. слов": config.min_num_words,
        "макс. результатов": config.max_results,
        "в отчете": config.return_top,
        "offline режим": config.offline_mode,
        "api_token": config.api_token
    }
    
    if not confirm_settings(config_dict):
        print("\n❌ Отменено пользователем")
        return
    
    run_processing(config, seeds_only=False, export_format="both")


def run_processing(config, seeds_only=False, export_format="both"):
    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        sys.exit(1)
    
    print("=" * 80)
    print("🎯 KEYWORD HUNTER")
    print("=" * 80)
    print(f"Ниша: {config.niche}")
    print(f"База: {config.base} | Регион: {config.region_id if not config.multi_region else 'Мульти'}")
    if config.multi_region:
        print(f"Регионы: {config.regions}")
    print(f"Порог WSK: <={config.wsk_threshold} | Мин. слов: >={config.min_num_words}")
    print(f"Макс. результатов: {config.max_results}")
    if config.offline_mode:
        print("🔌 OFFLINE РЕЖИМ: без обращения к API")
    print("=" * 80)
    
    generator = SeedGenerator(config.niche, config.seed_targets)
    seeds = generator.generate(count=100)
    
    print(f"\n✅ Сгенерировано {len(seeds)} семян")
    
    if seeds_only:
        print("\n🌱 СЕМЕНА:")
        for i, seed in enumerate(seeds, 1):
            print(f"{i}. {seed}")
        return
    
    if config.offline_mode:
        print("\n🔌 Offline режим: пропускаем API запросы")
        processor = KeywordProcessor(KeysAPIClient(""), config)
    else:
        api_client = KeysAPIClient(config.api_token)
        processor = KeywordProcessor(api_client, config)
    
    try:
        keywords = processor.process_pipeline(seeds)
    except Exception as e:
        print(f"\n❌ Ошибка обработки: {e}")
        sys.exit(1)
    
    if not keywords:
        print("\n⚠️ Не найдено подходящих ключевых фраз")
        return
    
    keywords_sorted = sorted(keywords, key=lambda x: (x.get("wsk", 999999), -x.get("numwords", 0)))
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"keywords_{config.base}_{timestamp}"
    
    if export_format in ["csv", "both"]:
        Exporter.to_csv(keywords_sorted, f"{base_filename}.csv")
    
    if export_format in ["json", "both"]:
        Exporter.to_json(keywords_sorted, f"{base_filename}.json")
    
    report = Exporter.generate_report(keywords_sorted, seeds, config)
    
    report_filename = f"report_{config.base}_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"💾 Отчет сохранен: {report_filename}")
    
    print("\n" + report)
    
    if not config.offline_mode and len(keywords_sorted) >= 5:
        processor.sample_validation(keywords_sorted, sample_size=5)


if __name__ == "__main__":
    main()
