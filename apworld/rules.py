from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import CollectionState
from worlds.generic.Rules import add_rule, set_rule

if TYPE_CHECKING:
    from .world import FTLMultiverseWorld

from .utils import load_json

def set_all_rules(world: FTLMultiverseWorld) -> None:
    # we don't need to define entrance rules since that is already done in regions.py
    set_all_location_rules(world)
    set_completion_condition(world)

def set_all_location_rules(world: FTLMultiverseWorld) -> None:
    location_data = load_json("data/locations.json")

    for loc in location_data["unique"]:
        if "requires" in loc:
            location = world.get_location(loc["name"])
            set_rule(location, resolve_requirement(loc["requires"], world))

def set_completion_condition(world: FTLMultiverseWorld) -> None:
    location_data = load_json("data/locations.json")

    selected_value = world.options.ending.value
    required_amount = world.options.unique_ship_victories

    ending_item_name = next(
        ending["name"]
        for ending in location_data["endings"]
        if selected_value == getattr(world.options.ending, ending["option_name"])
    )

    world.multiworld.completion_condition[world.player] = (
        lambda state, e=ending_item_name, r=required_amount:
            state.has(e, world.player, r)
    )

# helper function
def resolve_requirement(req, world):
    if req["type"] == "any":
        items = tuple(req["items"])
        return lambda state, items=items: state.has_any(items, world.player)

    if req["type"] == "all":
        items = tuple(req["items"])
        return lambda state, items=items: state.has_all(items, world.player)

    raise Exception(f"Unknown requirement: {req}")