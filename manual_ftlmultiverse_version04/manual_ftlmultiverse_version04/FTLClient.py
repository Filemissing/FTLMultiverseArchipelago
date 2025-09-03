from __future__ import annotations
import time
from typing import Any
import typing
from worlds import AutoWorldRegister, network_data_package
import json

import asyncio, re

import ModuleUpdate
ModuleUpdate.update()

import Utils

from tkinter import Tk, filedialog
from .Memory import MemoryInterface

if __name__ == "__main__":
    Utils.init_logging("FTLClient", exception_logger="Client")

from NetUtils import ClientStatus
from CommonClient import CommonContext, gui_enabled, logger, get_base_parser, ClientCommandProcessor, server_loop
from MultiServer import mark_raw

class FTLClientCommandProcessor(ClientCommandProcessor):
    def log(self, text: str):
        super(FTLClientCommandProcessor, self).output(text)

    def _cmd_check(self):
        """manually check the contents of the modToClient vector"""
        self.ctx.log(self.ctx.memory_interface.read_vector(self.ctx.memory_interface.modToClient_address))

    def _cmd_check2(self):
        """manually check the contents of the clientToMod vector"""
        self.ctx.log(self.ctx.memory_interface.read_vector(self.ctx.memory_interface.clientToMod_address))

    @mark_raw
    def _cmd_message(self, message: str) -> bool:
        """Send a message to the mod"""
        if not message:
            self.output("No message provided.")
            return False
        self.ctx.send_message_to_mod(message)
        return True

    @mark_raw
    def _cmd_send(self, location_name: str) -> bool:
        """Send a check"""
        names = self.ctx.location_names_to_id.keys()
        location_name, usable, response = Utils.get_intended_text(
            location_name,
            names
        )
        if usable:
            location_id = self.ctx.location_names_to_id[location_name]
            self.ctx.locations_checked.append(location_id)
            self.ctx.syncing = True
        else:
            self.output(response)
            return False

class FTLContext(CommonContext):
    command_processor = FTLClientCommandProcessor
    game = "FTLMultiverse" # using "FTLMultiverse" as name causes issues with autoWorld
    items_handling = 0b111 # full remote, idk know exactly what this does
    tags = {"AP"}

    exe_path = ""

    location_table = {}
    item_table = {}
    region_table = {}
    category_table = {}

    tracker_reachable_locations = []
    tracker_reachable_events = []

    set_deathlink = False
    last_death_link = 0
    deathlink_out = False

    colors = {
        'location_default': [219/255, 218/255, 213/255, 1],
        'location_in_logic': [2/255, 242/255, 42/255, 1],
        'category_even_default': [0.5, 0.5, 0.5, 0.1],
        'category_odd_default': [1.0, 1.0, 1.0, 0.0],
        'category_in_logic': [2/255, 82/255, 2/255, 1],
        'deathlink_received': [1, 0, 0, 1],
        'deathlink_primed': [1, 1, 1, 1],
        'deathlink_sent': [0, 1, 0, 1]
    }

    def __init__(self, server_address, password, player_name) -> None:
        super(FTLContext, self).__init__(server_address, password)

        self.send_index: int = 0
        self.syncing = False
        self.username = player_name

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(FTLContext, self).server_auth(password_requested)

        world = AutoWorldRegister.world_types.get(self.game)
        if not self.location_table and not self.item_table and world is None:
            raise Exception(f"Cannot load {self.game}, please add the apworld to lib/worlds/")

        data_package = network_data_package["games"].get(self.game, {})

        self.update_ids(data_package)

        if world is not None and hasattr(world, "victory_names"):
            self.victory_names = world.victory_names
            self.goal_location = self.get_location_by_name(world.victory_names[0])
        else:
            self.victory_names = ["__Manual Game Complete__"]
            self.goal_location = self.get_location_by_name("__Manual Game Complete__")

        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        super().on_package(cmd, args)

        if cmd in {"Connected", "DataPackage"}:
            if cmd == "Connected":
                Utils.persistent_store("client", "last_manual_game", self.game)
                goal = args["slot_data"].get("goal")
                if goal and goal < len(self.victory_names):
                    self.goal_location = self.get_location_by_name(self.victory_names[goal])
                if args['slot_data'].get('death_link'):
                    self.ui.enable_death_link()
                    self.set_deathlink = True
                    self.last_death_link = 0
                logger.info(f"Slot data: {args['slot_data']}")

        elif cmd in {"ReceivedItems"}:
            self.send_message_to_mod(f"ReceivedItems: {args['items']}")
        elif cmd in {"RoomUpdate"}:
            pass

    # not currently functional
    async def update(self):
        while not self.exit_event.is_set():
            self.check_message_from_mod()
            await asyncio.sleep(0.1)

    # ----------------------------------------------------------------
    # Methods from ManualClient
    # ----------------------------------------------------------------

    def get_location_by_name(self, name) -> dict[str, Any]:
        location = self.location_table.get(name)
        if not location:
            # It is absolutely possible to pull categories from the data_package via self.update_game. I have not done this yet.
            location = AutoWorldRegister.world_types[self.game].location_name_to_location.get(name, {"name": name})
        return location

    def get_location_by_id(self, id) -> dict[str, Any]:
        name = self.location_names.lookup_in_game(id)
        return self.get_location_by_name(name)

    def get_item_by_name(self, name):
        item = self.item_table.get(name)
        if not item:
            item = AutoWorldRegister.world_types[self.game].item_name_to_item.get(name, {"name": name})
        return item

    def get_item_by_id(self, id):
        name = self.item_names.lookup_in_game(id)
        return self.get_item_by_name(name)

    def update_ids(self, data_package) -> None:
        self.location_names_to_id = data_package['location_name_to_id']
        self.item_names_to_id = data_package['item_name_to_id']

    def update_data_package(self, data_package: dict):
        super().update_data_package(data_package)
        for game, game_data in data_package["games"].items():
            if game == self.game:
                self.update_ids(game_data)

    # ----------------------------------------------------------------
    # Methods relating to mod communication and memory module
    # ----------------------------------------------------------------
    def select_exe_sync(self):
        root = Tk()
        root.withdraw()
        return filedialog.askopenfilename(
            title="Select FTLGame.exe",
            filetypes=[("Executable Files", "FTLGame.exe")],
        )
    async def select_exe(self):
        self.exe_path = await asyncio.to_thread(self.select_exe_sync)

    def setup_memory(self):
        self.memory_interface = MemoryInterface(self.exe_path, self)

    def check_message_from_mod(self):
        messages = self.memory_interface.check_messages()
        for msg_id, msg in messages:
            self.log(msg)

    def send_message_to_mod(self, msg: str):
        self.memory_interface.send_message(msg)

    # ------------------
    # Helper methods
    # ------------------
    def log(self, text: str):
        self.on_print({"text": text})

async def game_watcher(ctx: FTLContext):
    while not ctx.exit_event.is_set():
        if ctx.syncing == True:
            sync_msg = [{'cmd': 'Sync'}]
            if ctx.locations_checked:
                sync_msg.append({"cmd": "LocationChecks", "locations": list(ctx.locations_checked)})
            await ctx.send_msgs(sync_msg)
            ctx.syncing = False

        if ctx.set_deathlink:
            ctx.set_deathlink = False
            await ctx.update_death_link(True)

        if ctx.deathlink_out:
            ctx.deathlink_out = False
            await ctx.send_death()

        sending = []
        victory = ("__Victory__" in ctx.items_received)
        ctx.locations_checked = sending
        message = [{"cmd": 'LocationChecks', "locations": sending}]
        await ctx.send_msgs(message)
        if not ctx.finished_game and victory:
            await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            ctx.finished_game = True
        await asyncio.sleep(0.1)

def read_apmanual_file(apmanual_file):
    from base64 import b64decode

    with open(apmanual_file, 'r') as f:
        return json.loads(b64decode(f.read()))

async def main(args):
    config_file = {}
    if args.apmanual_file:
        config_file = read_apmanual_file(args.apmanual_file)
    ctx = FTLContext(args.connect, args.password, config_file.get("player_name"))
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    ctx.item_table = config_file.get("items", {})
    ctx.location_table = config_file.get("locations", {})
    ctx.region_table = config_file.get("regions", {})
    ctx.category_table = config_file.get("categories", {})

    await ctx.select_exe()

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()
    progression_watcher = asyncio.create_task(
        game_watcher(ctx), name="FTLProgressionWatcher")

    ctx.update_task = asyncio.create_task(
        ctx.update(), name="FTLUpdateLoop")

    ctx.setup_memory()

    # start the update loop
    ctx.update()

    await ctx.exit_event.wait()
    ctx.server_address = None

    await ctx.shutdown()

def launch() -> None:
    import colorama

    parser = get_base_parser(description="Manual Client, for operating a Manual game in Archipelago.")
    parser.add_argument('apmanual_file', default="", type=str, nargs="?", help='Path to an APMANUAL file')

    args, rest = parser.parse_known_args()
    colorama.init()
    asyncio.run(main(args))
    colorama.deinit()

if __name__ == '__main__':
    launch()
