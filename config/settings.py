from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SUPPORTED_MODELS = {
    "deepseek": {"deepseek-chat", "deepseek-reasoner"},
    "groq": {"qwen/qwen3-32b", "moonshotai/kimi-k2", "llama-3.3-70b-versatile"},
}

PROVIDER_API_KEYS = {"deepseek": "deepseek_api_key", "groq": "groq_api_key"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")
    llm_reasoning_provider: str = Field(
        default="deepseek", alias="LLM_REASONING_PROVIDER"
    )
    llm_reasoning_model: str = Field(
        default="deepseek-reasoner", alias="LLM_REASONING_MODEL"
    )
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")

    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")

    llm_fallback_1_provider: str | None = Field(
        default="groq", alias="LLM_FALLBACK_1_PROVIDER"
    )
    llm_fallback_1_model: str | None = Field(
        default="qwen/qwen3-32b", alias="LLM_FALLBACK_1_MODEL"
    )
    llm_fallback_2_provider: str | None = Field(
        default="groq", alias="LLM_FALLBACK_2_PROVIDER"
    )
    llm_fallback_2_model: str | None = Field(
        default="moonshotai/kimi-k2", alias="LLM_FALLBACK_2_MODEl"
    )
    llm_fallback_3_provider: str | None = Field(
        default="groq", alias="LLM_FALLBACK_3_PROVIDER"
    )
    llm_fallback_3_model: str | None = Field(
        default="llama-3.3-70b-versatile", alias="LLM_FALLBACK_3_MODEL"
    )

    @model_validator(mode="after")
    def validate_llm_config(self):
        if self.llm_provider not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

        provider_models = SUPPORTED_MODELS[self.llm_provider]
        if self.llm_model not in provider_models:
            raise ValueError(
                f"Model '{self.llm_model}' is not supported by provider '{self.llm_provider}'"
            )

        api_key_field = PROVIDER_API_KEYS.get(self.llm_provider)
        if api_key_field and not getattr(self, api_key_field):
            raise ValueError(
                f"Missing API key for active provider: {api_key_field.upper()}"
            )

        reasoning_provider_models = SUPPORTED_MODELS[self.llm_reasoning_provider]

        if self.llm_reasoning_model not in reasoning_provider_models:
            raise ValueError(
                f"Reasoning model '{self.llm_reasoning_model}' is not supported"
                f"by provider '{self.llm_reasoning_provider}'"
            )

        if self.llm_reasoning_provider not in SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported reasonig LLM provider: {self.llm_reasoning_provider}"
            )

        fallbacks = [
            (self.llm_fallback_1_provider, self.llm_fallback_1_model),
            (self.llm_fallback_2_provider, self.llm_fallback_2_model),
            (self.llm_fallback_3_provider, self.llm_fallback_3_model),
        ]

        for provider, model in fallbacks:
            if provider is None and model is None:
                continue

            if provider is None or model is None:
                raise ValueError(
                    "Fallback provider and model must be configured together"
                )

            if provider not in SUPPORTED_MODELS:
                raise ValueError(f"Unsupported fallback LLM provider: {provider}")

            if model not in SUPPORTED_MODELS[provider]:
                raise ValueError(
                    f"Fallback model '{model}' is not supported by provider '{provider}'"
                )

        return self
