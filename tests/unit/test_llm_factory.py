from config.settings import Settings


def test_creates_deepseek_chat_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from services.llm_factory import create_chat_model

    settings = Settings(_env_file=None)
    model = create_chat_model(settings)

    assert model.model == "deepseek-chat"


def test_creates_groq_chat_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "qwen/qwen3-32b")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    from services.llm_factory import create_chat_model

    settings = Settings(_env_file=None)
    model = create_chat_model(settings)
    assert model.model_name == "qwen/qwen3-32b"


def test_creates_reasoning_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("LLM_REASONING_MODEL", "deepseek-reasoner")
    monkeypatch.setenv("LLM_REASONING_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from services.llm_factory import create_reasoning_model

    settings = Settings(_env_file=None)
    model = create_reasoning_model(settings)
    assert model.model == "deepseek-reasoner"


def test_creates_fallback_models_in_order(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    from services.llm_factory import create_fallback_models

    settings = Settings(_env_file=None)
    models = create_fallback_models(settings)

    assert [model.model_name for model in models] == [
        "qwen/qwen3-32b",
        "moonshotai/kimi-k2",
        "llama-3.3-70b-versatile",
    ]


def test_creates_reasoning_model_with_independent_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "qwen/qwen3-32b")
    monkeypatch.setenv("LLM_REASONING_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_REASONING_MODEL", "deepseek-reasoner")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from services.llm_factory import create_reasoning_model

    settings = Settings(_env_file=None)
    model = create_reasoning_model(settings)

    assert model.model == "deepseek-reasoner"
