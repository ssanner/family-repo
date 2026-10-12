"""Quest implementations for DragonFlightGame."""

from .quest import Quest
from .tree_canopy_quest import TreeCanopyQuest
from .hoop_quest import HoopQuest
from .water_journey_quest import WaterJourneyQuest
from .fire_clan_quest import FireClanQuest
from .earth_clan_quest import EarthClanQuest
from .sky_clan_quest import SkyClanQuest

__all__ = ["Quest", "TreeCanopyQuest", "HoopQuest", "WaterJourneyQuest",
           "FireClanQuest", "EarthClanQuest", "SkyClanQuest"]
