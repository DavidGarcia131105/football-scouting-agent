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


def test_system_prompt_trusts_tool_metadata_as_real_data():
    assert "is_real_data" in SYSTEM_PROMPT
    assert "No llames simulados" in SYSTEM_PROMPT


def test_system_prompt_hides_tool_metadata_from_final_user_response():
    assert "No muestres campos técnicos" in SYSTEM_PROMPT
    assert "is_simulated" in SYSTEM_PROMPT
    assert "source_label" in SYSTEM_PROMPT


def test_system_prompt_avoids_claiming_unknown_season_status():
    assert "season_status" in SYSTEM_PROMPT
    assert "no afirmes que la temporada está en curso o finalizada" in SYSTEM_PROMPT
