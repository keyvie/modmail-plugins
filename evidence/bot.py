from discord import (
    AppCommandType,
    MemberCacheFlags,
    Intents,
    Client,
)
from discord.app_commands import (
    Command, 
    CommandTree,
)
from os import getenv
import asyncio

from .ratelimits import (
    RatelimitAction, 
    check_ratelimits,
)

# Type checks
from typing import TYPE_CHECKING, Literal
if TYPE_CHECKING:
    from .evidence import Evidence


class EvidenceBot:
    def __init__(self, plugin: "Evidence"):
        self.plugin = plugin
        self.client = None
        self.tree = None
        self.task = None

    async def create(self) -> None:
        if self.client:
            return
        intents = Intents.none()
        intents.guilds = True
        intents.message_content = True

        self.client = Client(
            intents=intents,
            member_cache_flags=MemberCacheFlags.none(),
            max_messages=None,
            chunk_guilds_at_startup=False,
        )
        self.tree = CommandTree(self.client)

    async def start(self) -> None:
        if not self.client:
            raise ValueError("Evidence bot has not been created")
        bot_token = getenv("EVIDENCE_BOT_TOKEN")
        if not bot_token:
            raise ValueError("You need to set EVIDENCE_BOT_TOKEN in your environment variables")
        
        # Checks the rate limit for connecting the bot
        await check_ratelimits(self.plugin, RatelimitAction.ConnectBot)
        
        loop = asyncio.get_running_loop()
        self.task = loop.create_task(self._run(bot_token))

    async def _run(self, bot_token: str) -> None:
            if not self.client:
                raise ValueError("Evidence bot has not been created")
            try:
                await self.client.start(bot_token)
            except Exception as e:
                print(f"Error starting Evidence bot: {e}")

    async def close(self) -> None:
        if not self.client:
            return
        try:
            await self.client.close()
        except Exception:
            pass
        if self.task:
            self.task.cancel()
            self.task = None

    async def restart(self) -> None:
        await self.close()
        await self.start()

    async def destroy(self) -> None:
        await self.close()
        self.client = None
        self.tree = None


    # Command functions

    def get_command(self, name: str, type: Literal[AppCommandType.message, AppCommandType.user] = None) -> Command:
        if not self.tree:
            raise ValueError("Evidence bot has not been created")
        return self.tree.get_command(name, type=type)
    
    def add_command(self, command) -> None:
        if not self.tree:
            raise ValueError("Evidence bot has not been created")
        self.tree.add_command(command)

    def remove_command(self, command) -> None:
        if not self.tree:
            raise ValueError("Evidence bot has not been created")
        self.tree.remove_command(command)

    async def sync_commands(self) -> None:
        if not self.tree:
            raise ValueError("Evidence bot has not been created")
        await self.tree.sync()