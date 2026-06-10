from openai import AsyncOpenAI

from core.config import settings


def get_openai_client() -> AsyncOpenAI:
    api_key: str = settings.OPENAI_API_KEY or "not-needed"
    return AsyncOpenAI(api_key=api_key, base_url=settings.OPENAI_API_URL)


openai_client: AsyncOpenAI = get_openai_client()
