from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Entrance, Region

if TYPE_CHECKING:
    from .world import FTLMultiverseWorld

import json
import pkgutil

from . import __name__ as package_name

from .utils import load_json

def create_and_connect_regions(world: FTLMultiverseWorld) -> None:

    data = load_json(package_name, "data/sectors.json")

    # Create and connect starting region and abstract hub
    start = Region(data["starting_sector"], world.player, world.multiworld)
    hub = Region(data["abstract_hub_region"], world.player, world.multiworld)

    world.multiworld.regions.append(start)
    world.multiworld.regions.append(hub)

    start.connect(hub)

    # create all the regions according to the player's options
    regions: list[Region] = []

    if world.options.include_generic:
        regions += [Region(s, world.player, world.multiworld) for s in data["generic"]]

    if world.options.include_unique:
        regions += [Region(s, world.player, world.multiworld) for s in data["unique"]]

    if world.options.include_secret:
        regions += [Region(s, world.player, world.multiworld) for s in data["secret"]]

    # add to the multiworld
    world.multiworld.regions += regions

    # connect all regions to the hub
    for region in regions:
        hub.connect(region, lambda state, r=region: state.has(r.name, world.player))
