from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    SEOUL_API_KEY: str = ""
    SEOUL_API_BASE_URL: str = "http://openapi.seoul.go.kr:8088"
    DATA_GO_KR_API_KEY: str = ""
    DATA_GO_KR_BASE_URL: str = "https://apis.data.go.kr/B553077/api/open/sdsc2"
    BIZINFO_API_KEY: str = ""
    CACHE_TTL: int = 3600  # 1시간

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
