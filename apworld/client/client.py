import asyncio
import sys
from argparse import Namespace
from tkinter import Tk, filedialog
from typing import Any

from CommonClient import CommonContext, ClientCommandProcessor, gui_enabled, server_loop
import Utils

from .memory import MemoryInterface
from ..utils import load_json


class FTLMultiverseClientCommandProcessor(ClientCommandProcessor):
    pass

class FTLMultiverseContext(CommonContext):
    command_processor = FTLMultiverseClientCommandProcessor
    game = "FTL: Multiverse"
    items_handling = 0b111 # full remote

    client_loop: asyncio.Task[None]

    slot_data: dict[str, Any]
    death_link: bool = False

    item_data = load_json("data/items.json")
    location_data = load_json("data/locations.json")
    sector_data = load_json("data/sectors.json")

    def __init__(self, server_address: str | None = None, password: str | None = None) -> None:
        super().__init__(server_address, password)

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)

        await self.get_username()
        await self.send_connect(game=self.game)

    def on_package(self, cmd: str, args: dict):
        super().on_package(cmd, args)
        if cmd == "Connected":
            self.slot_data = args["slot_data"]
            self.death_link = bool(self.slot_data["death_link"])
            self.log(f"Death Link = {self.death_link}")
            Utils.async_start(self.update_death_link(self.death_link))

        if cmd == "RecievedItems":
            pass

    async def update(self):
        while not self.exit_event.is_set():
            await self.check_message_from_mod()
            await asyncio.sleep(0.1)

    async def on_mod_message(self, cmd: str, args: list[str] | None):
        if cmd == "CHOICE":
            choicebox_id = args[0]
            self.log(choicebox_id)
            locations = [loc["name"] for loc in self.location_data["unique"] if loc["choicebox_id"] == choicebox_id]
            if len(locations) > 0:
                ids = [self.location_names[loc] for loc in locations]
                await self.check_locations()
        if cmd == "LOCATION":
            await self.check_locations([self.location_names[args[0]]])
        if cmd == "DEATH":
            await self.send_death()

    async def shutdown(self):
        super().shutdown()
        self.send_message_to_mod("EXIT")

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

    async def check_message_from_mod(self):
        messages = self.memory_interface.check_messages()
        for msg_id, msg in messages:
            parts: list[str] = str.split(msg, "|")
            cmd = parts[0]
            args = parts[1:]
            await self.on_mod_message(cmd, args)

    def send_message_to_mod(self, msg: str):
        self.memory_interface.send_message(msg)

    # ------------------
    # Helper methods
    # ------------------
    def log(self, text: str):
        self.on_print({"text": text})

async def main(args: Namespace) -> None:
    ctx = FTLMultiverseContext(args.connect, args.password)
    ctx.auth = args.name
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    await ctx.select_exe()

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    ctx.update_task = asyncio.create_task(
        ctx.update(), name="FTLUpdateLoop")

    ctx.setup_memory()

    await ctx.exit_event.wait()
    await ctx.shutdown()

def launch(*args: str) -> None:
    from .launch import launch_client

    launch_client(*args)

if __name__ == "__main__":
    launch(*sys.argv[1:])