import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    api_token: str = ""
    base: str = "msk"
    region_id: int = 213
    niche: str = ""
    seed_targets: Optional[List[str]] = None
    wsk_threshold: int = 80
    ws_threshold: int = 1000
    min_num_words: int = 3
    stop_words: List[str] = None
    return_top: int = 50
    max_results: int = 1000
    ad_filters: Optional[str] = None
    safe_filters: bool = True
    cache_ttl: int = 86400
    offline_mode: bool = False
    multi_region: bool = False
    regions: Optional[List[int]] = None

    @classmethod
    def from_env(cls):
        regions_str = os.getenv("REGIONS", "")
        multi_region = os.getenv("MULTI_REGION", "0") == "1"
        
        return cls(
            api_token=os.getenv("API_TOKEN", ""),
            base=os.getenv("BASE", "msk"),
            region_id=int(os.getenv("REGION_ID", "213")),
            niche=os.getenv("NICHE", ""),
            seed_targets=os.getenv("SEED_TARGETS", "").split(",") if os.getenv("SEED_TARGETS") else None,
            wsk_threshold=int(os.getenv("WSK_THRESHOLD", "80")),
            ws_threshold=int(os.getenv("WS_THRESHOLD", "1000")),
            min_num_words=int(os.getenv("MIN_NUM_WORDS", "3")),
            stop_words=os.getenv("STOP_WORDS", "бесплатно,видео,скачать,реферат,вакансии").split(","),
            return_top=int(os.getenv("RETURN_TOP", "50")),
            max_results=int(os.getenv("MAX_RESULTS", "1000")),
            ad_filters=os.getenv("AD_FILTERS"),
            safe_filters=os.getenv("SAFE_FILTERS", "1") == "1",
            offline_mode=os.getenv("OFFLINE_MODE", "0") == "1",
            multi_region=multi_region,
            regions=[int(r.strip()) for r in regions_str.split(",")] if regions_str and multi_region else None,
        )

    def validate(self):
        if not self.offline_mode and not self.api_token:
            raise ValueError("API_TOKEN обязателен (или включите OFFLINE_MODE=1)")
        if not self.niche:
            raise ValueError("NICHE обязателен")
        if self.min_num_words < 1:
            raise ValueError("MIN_NUM_WORDS должен быть >= 1")
        if self.multi_region and not self.regions:
            raise ValueError("При MULTI_REGION=1 необходимо указать REGIONS")
