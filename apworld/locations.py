from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import ItemClassification, Location

from . import items
from .utils import load_json

if TYPE_CHECKING:
    from .world import FTLMultiverseWorld

LOCATION_NAME_TO_ID: dict[str, int] = {}

class FTLMultiverseLocation(Location):
    game = "FTL: Multiverse"

def get_location_names_with_ids(location_names: list[str]) -> dict[str, int | None]:
    return {location_name: LOCATION_NAME_TO_ID[location_name] for location_name in location_names}

def create_all_locations(world: FTLMultiverseWorld) -> None:
    create_regular_locations(world)
    create_events(world)

def create_regular_locations(world: FTLMultiverseWorld) -> None:
    sector_data = load_json("data/sectors.json")
    location_data = load_json("data/locations.json")

    hub = world.get_region(sector_data["abstract_hub_region"])

    # create repeating locations
    for repeating_location in location_data["repeating"]:
        for i in range(0, getattr(world.options, repeating_location["option_name"])):
            if world.options.split_default_locations and repeating_location["can_split"]:
                for sector in sector_data["generic"] + sector_data["unique"]:
                    region = world.get_region(sector)
                    region.add_locations(get_location_names_with_ids([sector + " " + repeating_location["name"] + " " + str(i + 1)]), FTLMultiverseLocation)
            else:
                hub.add_locations(get_location_names_with_ids([repeating_location["name"] + " " + str(i + 1)]), FTLMultiverseLocation)

    # create unique locations
    for unique_location in location_data["unique"]:
        sector_id = unique_location["sector_id"]
        if not world.options.include_secret and sector_id in sector_data["secret"]:
            continue

        region = world.get_region(sector_id)
        region.add_locations(get_location_names_with_ids([unique_location["name"]]), FTLMultiverseLocation)

def create_events(world: FTLMultiverseWorld) -> None:
    sector_data = load_json("data/sectors.json")
    location_data = load_json("data/locations.json")

    hub = world.get_region(sector_data["abstract_hub_region"])

    ending_events = [loc["name"] for loc in location_data["endings"]]

    for event_name in ending_events:
        for i in range(0, 123):
            hub.add_event(
                location_name=f"{event_name} event {i + 1}",
                item_name=event_name,
                location_type=FTLMultiverseLocation,
                item_type=items.FTLMultiverseItem,
            )

# populates the LOCATION_NAME_TO_ID dictionary with the location names and their corresponding IDs to account for repeating locations and split repeating locations
def populate_lookup_table() -> None:
    sector_data = load_json("data/sectors.json")
    location_data = load_json("data/locations.json")

    location_id = 1
    # create global repeating locations
    for repeating_location in sorted(location_data["repeating"], key=lambda r: r["name"]):
        for i in range(0, repeating_location["max"]):
            LOCATION_NAME_TO_ID[repeating_location["name"] + " " + str(i + 1)] = location_id
            location_id += 1

    # create split repeating locations
    for repeating_location in sorted(location_data["repeating"], key=lambda r: r["name"]):
        if repeating_location["can_split"]:
            for sector in sorted(sector_data["generic"] + sector_data["unique"]):
                for i in range(0, repeating_location["max"]):
                    LOCATION_NAME_TO_ID[sector + " " + repeating_location["name"] + " " + str(i + 1)] = location_id
                    location_id += 1

    # create unique locations
    for unique_location in sorted(location_data["unique"], key=lambda r: r["name"]):
        LOCATION_NAME_TO_ID[unique_location["name"]] = location_id
        location_id += 1

populate_lookup_table() # populate at load so the table is ready when the locations are created
