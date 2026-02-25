from dataclasses import dataclass

from Options import Choice, OptionGroup, PerGameCommonOptions, Range, Toggle, DefaultOnToggle, DeathLink

from .utils import load_json

locations_data = load_json("data/locations.json")

class FTLDeathLink(DeathLink):
    """Enable death link?"""
    display_name = "Death link"

class Ending(Choice):
    """ The ending that is required for completion"""
    display_name = "Ending"
    option_multiverse = 0
    option_peace = 1
    option_slug = 2
    option_true = 3
    option_nexus = 4
    option_chaos = 5
    default = 0

class UniqueShipVictories(Range):
    """The amount of unique ships that you need to beat the chosen ending with to complete the game"""
    display_name = "Unique ship victories"
    default = 1
    range_start = 1
    range_end = 123

class IncludeSecret(DefaultOnToggle):
    """Whether to include sectors in the 'Secret' category of the Super Magic Hat mod in the randomization"""
    display_name = "Include Secret Sectors"

class SplitDefaultLocations(Toggle):
    """Whether to split the default locations into separate locations for each sector or keep them as one pool"""
    display_name = "Split Default Locations"

class ShopAmount(Range):
    """The amount of shops checks, this is global or per sector depending on SplitDefaultLocations option"""
    display_name = "Shop Amount"
    default = 10
    range_start = locations_data["repeating"][0]["min"]
    range_end = locations_data["repeating"][0]["max"]

class CombatAmount(Range):
    """The amount of combat checks, this is global or per sector depending on SplitDefaultLocations option"""
    display_name = "Combat Amount"
    default = 20
    range_start = locations_data["repeating"][1]["min"]
    range_end = locations_data["repeating"][1]["max"]

class FillerTrapChance(Range):
    """The chance for a filler item to be a trap"""
    display_name = "Filler Trap Chance"
    default = 50
    range_start = 0
    range_end = 100

@dataclass
class FTLMultiverseOptions(PerGameCommonOptions):
    death_link: FTLDeathLink
    ending: Ending
    unique_ship_victories: UniqueShipVictories
    include_secret: IncludeSecret
    split_default_locations: SplitDefaultLocations
    shop_amount: ShopAmount
    combat_amount: CombatAmount
    filler_trap_chance: FillerTrapChance
