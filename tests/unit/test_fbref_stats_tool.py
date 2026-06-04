from config.settings import Settings
import pytest
import pandas as pd


def test_creates_fbref_stats_tool(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    from tools.fbref_stats import create_fbref_stats_tool

    settings = Settings(_env_file=None)
    tool = create_fbref_stats_tool(settings)

    assert tool.name == "fbref_stats"


def test_rejects_unsupported_stat_type(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    from tools.fbref_stats import create_fbref_stats_tool

    settings = Settings(_env_file=None)
    tool = create_fbref_stats_tool(settings)

    with pytest.raises(ValueError, match="Unsupported FBref stat_type"):
        tool.invoke({"stat_type": "banana"})


def test_reads_player_season_stats_from_soccerdata(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    calls = {}

    class FakeFBref:
        def __init__(self, leagues, seasons, data_dir=None):
            calls["leagues"] = leagues
            calls["seasons"] = seasons
            calls["data_dir"] = data_dir

        def read_player_season_stats(self, stat_type):
            calls["stat_type"] = stat_type
            return pd.DataFrame(
                [
                    {"player": "Lamine Yamal", "team": "Barcelona", "goals": 7},
                    {"player": "Nico Williams", "team": "Athletic Club", "goals": 5},
                ]
            )

    monkeypatch.setattr("tools.fbref_stats.sd.FBref", FakeFBref)

    from tools.fbref_stats import create_fbref_stats_tool

    settings = Settings(_env_file=None)
    tool = create_fbref_stats_tool(settings)

    result = tool.invoke(
        {
            "player_name": "Lamine",
            "league": "ESP-La Liga",
            "season": "2025-2026",
            "stat_type": "standard",
        }
    )

    assert calls == {
        "leagues": "ESP-La Liga",
        "seasons": "2025-2026",
        "data_dir": settings.soccerdata_dir,
        "stat_type": "standard",
    }
    assert result["count"] == 1
    assert result["results"][0]["player"] == "Lamine Yamal"


def test_returns_explicit_fbref_source_metadata(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    class FakeFBref:
        def __init__(self, leagues, seasons, data_dir=None):
            pass

        def read_player_season_stats(self, stat_type):
            return pd.DataFrame(
                [
                    {"player": "Lamine Yamal", "season": "2526", "goals": 7},
                ]
            )

    monkeypatch.setattr("tools.fbref_stats.sd.FBref", FakeFBref)

    from tools.fbref_stats import create_fbref_stats_tool

    settings = Settings(_env_file=None)
    tool = create_fbref_stats_tool(settings)

    result = tool.invoke(
        {
            "player_name": "Lamine",
            "league": "ESP-La Liga",
            "season": "2025-2026",
            "stat_type": "standard",
        }
    )

    assert result["is_real_data"] is True
    assert result["data_provider"] == "FBref via soccerdata"
    assert result["source_label"] == "FBref vía soccerdata"
    assert "source_detail" not in result
    assert result["requested_season"] == "2025-2026"
    assert result["returned_seasons"] == ["2526"]
    assert result["is_simulated"] is False
    assert result["season_status"] == "unknown"
    assert (
        result["data_cutoff"]
        == "Datos disponibles en FBref vía soccerdata al momento de consulta"
    )


def test_reads_player_stats_with_fbref_multiindex_columns(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    class FakeFBref:
        def __init__(self, leagues, seasons, data_dir=None):
            pass

        def read_player_season_stats(self, stat_type):
            columns = pd.MultiIndex.from_tuples(
                [
                    ("", "player"),
                    ("", "team"),
                    ("standard", "goals"),
                ]
            )
            return pd.DataFrame(
                [
                    ["Lamine Yamal", "Barcelona", 7],
                    ["Nico Williams", "Athletic Club", 5],
                ],
                columns=columns,
            )

    monkeypatch.setattr("tools.fbref_stats.sd.FBref", FakeFBref)

    from tools.fbref_stats import create_fbref_stats_tool

    settings = Settings(_env_file=None)
    tool = create_fbref_stats_tool(settings)

    result = tool.invoke({"player_name": "Lamine"})

    assert result["count"] == 1
    assert result["results"][0]["player"] == "Lamine Yamal"
    assert result["results"][0]["standard_goals"] == 7


def test_reads_player_stats_when_player_is_in_fbref_index(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("LLM_MODEL", "deepseek-chat")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    class FakeFBref:
        def __init__(self, leagues, seasons, data_dir=None):
            pass

        def read_player_season_stats(self, stat_type):
            index = pd.MultiIndex.from_tuples(
                [
                    ("ESP-La Liga", "2526", "Barcelona", "Lamine Yamal"),
                    ("ESP-La Liga", "2526", "Athletic Club", "Nico Williams"),
                ],
                names=["league", "season", "team", "player"],
            )
            columns = pd.MultiIndex.from_tuples(
                [
                    ("nation", ""),
                    ("Performance", "Gls"),
                ]
            )
            return pd.DataFrame(
                [
                    ["ESP", 7],
                    ["ESP", 5],
                ],
                index=index,
                columns=columns,
            )

    monkeypatch.setattr("tools.fbref_stats.sd.FBref", FakeFBref)

    from tools.fbref_stats import create_fbref_stats_tool

    settings = Settings(_env_file=None)
    tool = create_fbref_stats_tool(settings)

    result = tool.invoke({"player_name": "Lamine"})

    assert result["count"] == 1
    assert result["results"][0]["player"] == "Lamine Yamal"
    assert result["results"][0]["Performance_Gls"] == 7
