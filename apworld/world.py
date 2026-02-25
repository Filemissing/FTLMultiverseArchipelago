from collections.abc import Mapping
from typing import Any

# Imports of base Archipelago modules must be absolute.
from worlds.AutoWorld import World

# Imports of your world's files must be relative.
from . import items, locations, regions, rules, web_world
from . import options as FTLMultiverse_options  # rename due to a name conflict with World.options
from .utils import load_json

class FTLMultiverseWorld(World):
    """
    FTL: Faster Than Light is a sci-fi rogue-like strategy game developed by Subset Games.
    FTL: Multiverse is a mod for FTL that adds over 300 new playable ships, over 200 new weapons and drones, and over 30 brand new sectors to explore.
    """

    game = "FTL: Multiverse"

    # The WebWorld is a definition class that governs how this world will be displayed on the website.
    # it's not necessary yet unless we want to get core-verified
    # web = web_world.APQuestWebWorld()

    options_dataclass = FTLMultiverse_options.FTLMultiverseOptions
    options: FTLMultiverse_options.FTLMultiverseOptions

    location_name_to_id = locations.LOCATION_NAME_TO_ID
    item_name_to_id = items.ITEM_NAME_TO_ID

    origin_region_name = load_json("data/sectors.json")["starting_sector"]

    def create_regions(self) -> None:
        regions.create_and_connect_regions(self)
        locations.create_all_locations(self)

    def set_rules(self) -> None:
        rules.set_all_rules(self)

    def create_items(self) -> None:
        items.create_all_items(self)

    def create_item(self, name: str) -> items.FTLMultiverseItem:
        return items.create_item_with_correct_classification(self, name)

    def get_filler_item_name(self) -> str:
        return items.get_random_filler_item_name(self)

    def fill_slot_data(self) -> Mapping[str, Any]:
        return self.options.as_dict(
            "death_link"
        )
