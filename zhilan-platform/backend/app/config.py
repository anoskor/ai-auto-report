"""应用配置管理"""

from typing import Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "智览 API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # ========== MySQL ==========
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "zhilian"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ========== Redis ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # ========== Elasticsearch ==========
    ES_HOST: str = "http://localhost:9200"
    ES_USER: str = "elastic"
    ES_PASSWORD: str = ""

    # ========== DeepSeek LLM ==========
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ========== 阿里云 DashScope（Embedding 向量） ==========
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v3"
    DASHSCOPE_EMBEDDING_DIMENSIONS: int = 1024
    DASHSCOPE_RERANK_MODEL: str = "qwen3-rerank"
    DASHSCOPE_RERANK_BASE: str = "https://dashscope.aliyuncs.com/compatible-api/v1/reranks"

    # ========== 天聚数行 TianAPI ==========
    TIANAPI_KEY: Optional[str] = None
    TIANAPI_BASE: str = "https://apis.tianapi.com"

    # ========== 数据采集（网络爬虫） ==========
    RSS_SOURCES: str = ""
    CRAWL_TARGETS: str = ""
    CRAWL_TIMEOUT: int = 10
    CRAWL_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

    # ========== QQ邮箱通知 ==========
    QQ_EMAIL_SENDER: Optional[str] = None
    QQ_EMAIL_AUTH_CODE: Optional[str] = None
    QQ_EMAIL_RECEIVER: Optional[str] = None

    # ========== 采集与调度 ==========
    COLLECTION_INTERVAL_MINUTES: int = 120
    REPORT_GENERATION_HOUR: int = 7
    REPORT_GENERATION_MINUTE: int = 0

    # ========== WebSocket ==========
    WS_HEARTBEAT_INTERVAL: int = 30

    # ========== 后端服务 ==========
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ========== CORS ==========
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # ========== 文件存储 ==========
    EXPORT_DIR: str = "./runtime/exports"
    TEMPLATE_DIR: str = "./templates"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
