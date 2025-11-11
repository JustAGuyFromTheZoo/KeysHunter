REGIONS_MAP = {
    "1": {"id": 213, "name": "Москва", "base": "msk"},
    "2": {"id": 2, "name": "Санкт-Петербург", "base": "spb"},
    "3": {"id": 11316, "name": "Новосибирск", "base": "nsk"},
    "4": {"id": 56, "name": "Екатеринбург", "base": "ekb"},
    "5": {"id": 54, "name": "Казань", "base": "kzn"},
    "6": {"id": 11079, "name": "Краснодар", "base": "krd"},
    "7": {"id": 51, "name": "Самара", "base": "sam"},
    "8": {"id": 11162, "name": "Челябинск", "base": "chlb"},
    "9": {"id": 65, "name": "Нижний Новгород", "base": "nnov"},
    "10": {"id": 11119, "name": "Омск", "base": "omsk"},
    "all": {"id": "all", "name": "Все регионы", "base": "multi"}
}

REGION_IDS = {
    "msk": [213],
    "spb": [2],
    "nsk": [11316],
    "ekb": [56],
    "kzn": [54],
    "krd": [11079],
    "sam": [51],
    "chlb": [11162],
    "nnov": [65],
    "omsk": [11119],
    "multi": [213, 2, 11316, 56, 54, 11079, 51, 11162, 65, 11119]
}


def show_menu():
    print("\n" + "=" * 80)
    print("🎯 KEYWORD HUNTER - Интерактивный режим")
    print("=" * 80)


def select_region():
    print("\n📍 Выберите регион для поиска:\n")
    for key, region in REGIONS_MAP.items():
        print(f"  {key}. {region['name']}")
    
    while True:
        choice = input("\n👉 Введите номер региона: ").strip()
        if choice in REGIONS_MAP:
            selected = REGIONS_MAP[choice]
            if choice == "all":
                return selected["base"], REGION_IDS["multi"], True
            return selected["base"], [selected["id"]], False
        print("❌ Неверный выбор, попробуйте снова")


def select_settings():
    print("\n⚙️ Дополнительные настройки:\n")
    
    wsk = input("  WSK порог (по умолчанию 80): ").strip()
    wsk = int(wsk) if wsk.isdigit() else 80
    
    words = input("  Минимум слов в запросе (по умолчанию 3): ").strip()
    words = int(words) if words.isdigit() else 3
    
    max_results = input("  Максимум результатов (по умолчанию 1000): ").strip()
    max_results = int(max_results) if max_results.isdigit() else 1000
    
    return_top = input("  Показать в отчете (по умолчанию 50): ").strip()
    return_top = int(return_top) if return_top.isdigit() else 50
    
    offline = input("  Offline режим - только генерация без API? (y/n, по умолчанию n): ").strip().lower()
    offline = offline == "y"
    
    return {
        "wsk_threshold": wsk,
        "min_num_words": words,
        "max_results": max_results,
        "return_top": return_top,
        "offline_mode": offline
    }


def get_niche():
    print("\n📝 Опишите вашу нишу:")
    print("   (например: доставка цветов премиум класса в Москве)")
    
    niche = input("\n👉 Ниша: ").strip()
    while not niche:
        print("❌ Описание ниши не может быть пустым")
        niche = input("\n👉 Ниша: ").strip()
    
    return niche


def get_stop_words():
    print("\n🚫 Минус-слова (через запятую, Enter чтобы использовать по умолчанию):")
    stop_words = input("👉 Минус-слова: ").strip()
    
    if not stop_words:
        return ["бесплатно", "видео", "скачать", "реферат", "вакансии"]
    
    return [w.strip() for w in stop_words.split(",")]


def confirm_settings(config_dict):
    print("\n" + "=" * 80)
    print("📋 НАСТРОЙКИ:")
    print("=" * 80)
    for key, value in config_dict.items():
        if key == "api_token":
            value = "***" if value else "НЕ УКАЗАН"
        print(f"  {key}: {value}")
    print("=" * 80)
    
    confirm = input("\n✅ Запустить? (y/n): ").strip().lower()
    return confirm == "y"
