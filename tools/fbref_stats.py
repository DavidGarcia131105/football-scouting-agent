import soccerdata as sd
import pandas as pd
from langchain_core.tools import tool

from config.settings import Settings


SUPPORTED_FBREF_STAT_TYPES = {
    "standard",
    "shooting",
    "passing",
    "passing_types",
    "goal_shot_creation",
    "defense",
    "possession",
    "playing_time",
    "misc",
    "keeper",
    "keeper_adv",
}


def _flatten_fbref_columns(stats: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(stats.columns, pd.MultiIndex):
        return stats

    flattened = stats.copy()
    flattened.columns = [
        "_".join(
            str(part).strip()
            for part in column
            if str(part).strip() and not str(part).startswith("Unnamed:")
        )
        for column in flattened.columns
    ]
    return flattened


def _reset_named_index(stats: pd.DataFrame) -> pd.DataFrame:
    if any(name is not None for name in stats.index.names):
        return stats.reset_index()

    return stats


def _find_player_column(stats: pd.DataFrame) -> str:
    if "player" in stats.columns:
        return "player"

    for column in stats.columns:
        normalized = str(column).lower()
        if normalized == "player" or normalized.endswith("_player"):
            return column

    raise ValueError("FBref stats did not include a player column")


def _unique_values(stats: pd.DataFrame, column: str) -> list[str]:
    if column not in stats.columns:
        return []

    return sorted(str(value) for value in stats[column].dropna().unique())


def create_fbref_stats_tool(settings: Settings):
    @tool("fbref_stats")
    def fbref_stats(
        player_name: str | None = None,
        league: str = "ESP-La Liga",
        season: str = "2025-2026",
        stat_type: str = "standard",
    ) -> dict:
        """Get player season statistics from FBref."""
        if stat_type not in SUPPORTED_FBREF_STAT_TYPES:
            raise ValueError(f"Unsupported FBref stat_type: {stat_type}")

        fbref = sd.FBref(
            leagues=league,
            seasons=season,
            data_dir=settings.soccerdata_dir,
        )
        stats = fbref.read_player_season_stats(stat_type=stat_type)
        stats = _reset_named_index(stats)
        stats = _flatten_fbref_columns(stats)

        if player_name:
            player_column = _find_player_column(stats)
            stats = stats[
                stats[player_column]
                .astype(str)
                .str.contains(player_name, case=False, na=False)
            ]

        results = stats.to_dict(orient="records")

        return {
            "source": "fbref",
            "data_provider": "FBref via soccerdata",
            "source_label": "FBref vía soccerdata",
            "is_real_data": True,
            "is_simulated": False,
            "season_status": "unknown",
            "data_cutoff": "Datos disponibles en FBref vía soccerdata al momento de consulta",
            "league": league,
            "requested_season": season,
            "returned_seasons": _unique_values(stats, "season"),
            "stat_type": stat_type,
            "count": len(results),
            "results": results,
        }

    return fbref_stats
