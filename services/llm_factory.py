from langchain_deepseek import ChatDeepSeek
from langchain_groq import ChatGroq
from config.settings import Settings


def _create_model(provider: str, model: str, settings: Settings):
    if provider == "deepseek":
        return ChatDeepSeek(
            model=model, api_key=settings.deepseek_api_key, temperature=0
        )

    if provider == "groq":
        return ChatGroq(model=model, api_key=settings.groq_api_key, temperature=0)

    raise ValueError(f"Unsupported LLM provider {provider}")


def create_chat_model(settings: Settings):
    if settings.llm_provider == "deepseek":
        return _create_model(
            provider=settings.llm_provider, model=settings.llm_model, settings=settings
        )

    if settings.llm_provider == "groq":
        return _create_model(
            provider=settings.llm_provider, model=settings.llm_model, settings=settings
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def create_reasoning_model(settings: Settings):
    if settings.llm_reasoning_provider == "deepseek":
        return _create_model(
            provider=settings.llm_reasoning_provider,
            model=settings.llm_reasoning_model,
            settings=settings,
        )

    if settings.llm_reasoning_provider == "groq":
        return _create_model(
            provider=settings.llm_reasoning_provider,
            model=settings.llm_reasoning_model,
            settings=settings,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_reasoning_provider}")


def create_fallback_models(settings: Settings):
    fallback_configs = [
        (settings.llm_fallback_1_provider, settings.llm_fallback_1_model),
        (settings.llm_fallback_2_provider, settings.llm_fallback_2_model),
        (settings.llm_fallback_3_provider, settings.llm_fallback_3_model),
    ]

    return [
        _create_model(provider=provider, model=model, settings=settings)
        for provider, model in fallback_configs
        if provider is not None and model is not None
    ]
