from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification

if TYPE_CHECKING:
    from .world import FTLMultiverseWorld

from .utils import load_json

ITEM_NAME_TO_ID: dict[str, int] = {}

DEFAULT_ITEM_CLASSIFICATIONS: dict[str, ItemClassification] = {}

class FTLMultiverseItem(Item):
    game = "FTL: Multiverse"

def get_random_filler_item_name(world: FTLMultiverseWorld) -> str:
    item_data = load_json("data/items.json")

    if world.random.randint(0, 99) < world.options.filler_trap_chance:
        return world.random.choice(item_data["traps"])["name"]
    else:
        return world.random.choice(item_data["fillers"])["name"]

def create_item_with_correct_classification(world: FTLMultiverseWorld, name: str) -> FTLMultiverseItem:
    classification = DEFAULT_ITEM_CLASSIFICATIONS[name]

    # add any clasification overrides (based on options?) here

    return FTLMultiverseItem(name, classification, ITEM_NAME_TO_ID[name], world.player)

def create_all_items(world: FTLMultiverseWorld) -> None:
    item_data = load_json("data/items.json")
    
    itempool: list[FTLMultiverseItem] = []

    for item in item_data["items"]:
        itempool.append(world.create_item(item["name"]))

    number_of_items = len(itempool)
    number_of_unfilled_locations = len(world.multiworld.get_unfilled_locations(world.player))
    needed_number_of_filler_items = max(0, number_of_unfilled_locations - number_of_items)

    itempool += [world.create_filler() for _ in range(needed_number_of_filler_items)]

    world.multiworld.itempool += itempool

# populates the ITEM_NAME_TO_ID and DEFAULT_ITEM_CLASSIFICATIONS dictionaries
def populate_lookup_tables() -> None:
    item_data = load_json("data/items.json")

    item_id = 1
    for item in sorted(item_data["items"], key=lambda r: r["name"]):
        ITEM_NAME_TO_ID[item["name"]] = item_id
        item_id += 1

        classification = ItemClassification.filler
        for c in item["classifications"]:
            classification |= getattr(ItemClassification, c)

        DEFAULT_ITEM_CLASSIFICATIONS[item["name"]] = classification

    for filler in sorted(item_data["fillers"], key=lambda r: r["name"]):
        ITEM_NAME_TO_ID[filler["name"]] = item_id
        item_id += 1

        DEFAULT_ITEM_CLASSIFICATIONS[filler["name"]] = ItemClassification.filler

    for trap in sorted(item_data["traps"], key=lambda r: r["name"]):
        ITEM_NAME_TO_ID[trap["name"]] = item_id
        item_id += 1

        DEFAULT_ITEM_CLASSIFICATIONS[trap["name"]] = ItemClassification.trap

populate_lookup_tables() # populate at load so the table is ready when the locations are created
