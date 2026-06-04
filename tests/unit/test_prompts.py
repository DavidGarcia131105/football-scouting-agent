from agent.prompts import SYSTEM_PROMPT


def test_system_prompt_requires_spanish_responses():
    assert "Responde siempre en español" in SYSTEM_PROMPT


def test_system_prompt_forbids_inventing_data():
    assert "No inventes" in SYSTEM_PROMPT


def test_system_prompt_requires_distinguishing_facts_from_inferences():
    assert "datos confirmados" in SYSTEM_PROMPT
    assert "inferencias" in SYSTEM_PROMPT


def test_system_prompt_requires_web_search_for_current_news():
    assert "actualidad" in SYSTEM_PROMPT
    assert "búsqueda web" in SYSTEM_PROMPT
