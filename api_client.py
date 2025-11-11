import time
import requests
from typing import Dict, List, Optional, Any
from rate_limiter import RateLimiter


class KeysAPIClient:
    BASE_URL = "https://api.keys.so"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.rate_limiter = RateLimiter(max_requests=10, time_window=10)
        self.session = requests.Session()
        self.session.headers.update({
            "X-Keyso-TOKEN": api_token,
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, max_retries: int = 3, **kwargs) -> Dict:
        for attempt in range(max_retries):
            try:
                self.rate_limiter.wait_if_needed()
                
                url = f"{self.BASE_URL}{endpoint}"
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 202:
                    time.sleep(2)
                    continue
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 15))
                    print(f"⏳ Превышен лимит запросов. Ожидание {retry_after} сек...")
                    time.sleep(retry_after)
                    continue
                
                if response.status_code == 401:
                    raise Exception("❌ Неверный или просроченный токен API")
                
                if response.status_code == 404:
                    return None
                
                if response.status_code == 500:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"⚠️ Ошибка сервера. Повтор через {wait_time} сек...")
                        time.sleep(wait_time)
                        continue
                    raise Exception("❌ Ошибка сервера после нескольких попыток")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise Exception(f"❌ Ошибка запроса: {str(e)}")
        
        return None

    def suggest(self, keywords: List[str], region: int) -> List[str]:
        response = self._request(
            "POST",
            "/tools/suggest",
            json={"list": keywords, "region": region}
        )
        return response.get("keys", []) if response else []

    def create_extended_keywords(self, base: str, keywords: List[str], 
                                 similarity: int = 30, 
                                 delete_duplicate: bool = True,
                                 additions: bool = True) -> Optional[str]:
        response = self._request(
            "POST",
            "/tools/extended_keywords",
            json={
                "base": base,
                "list": keywords,
                "config": {
                    "similarity": similarity,
                    "deleteDuplicate": delete_duplicate,
                    "additions": additions
                }
            }
        )
        return response.get("uid") if response else None

    def check_extended_keywords_state(self, uid: str) -> Dict:
        response = self._request("GET", f"/tools/extended_keywords/state/{uid}")
        return response if response else {"state": 0, "progress": 0}

    def get_extended_keywords(self, uid: str, page: int = 1, per_page: int = 100, 
                             filters: str = "", sort: str = "wsk|asc") -> Dict:
        params = {
            "page": page,
            "per_page": per_page,
            "sort": sort
        }
        if filters:
            params["filter"] = filters
        
        response = self._request(
            "GET",
            f"/tools/extended_keywords/{uid}",
            params=params
        )
        return response if response else {"data": [], "total": 0}

    def wait_for_extended_keywords(self, uid: str, max_wait: int = 60) -> bool:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            state = self.check_extended_keywords_state(uid)
            if state.get("state") == 10:
                return True
            if state.get("state") == 2:
                raise Exception("❌ Ошибка обработки отчета")
            
            progress = state.get("progress", 0)
            print(f"⏳ Обработка: {progress}%")
            time.sleep(3)
        
        raise Exception("❌ Превышено время ожидания отчета")

    def delete_doubles(self, keywords: List[str]) -> List[str]:
        response = self._request(
            "POST",
            "/tools/delete_double",
            json={"list": keywords}
        )
        return response.get("keys", []) if response else keywords

    def get_keyword_dashboard(self, base: str, keyword: str) -> Optional[Dict]:
        response = self._request(
            "GET",
            "/report/simple/keyword_dashboard",
            params={"base": base, "keyword": keyword}
        )
        return response
