from discord import (
    Color,
    Embed,
)
from discord.ext import commands
from discord.ext.commands import Context

# Imports from the modmail core
from core import checks # type: ignore
from core.models import PermissionLevel # type: ignore
from core.utils import getLogger # type: ignore
logger = getLogger(__name__)

# Imports for this plugin
from .config import (
    EvidenceConfigView,
    PluginMode,
    Config,
)
from .commands import Commands
from .bot import EvidenceBot


class Evidence(commands.Cog):
    """
    A plugin that allows users to attach messages as evidence to reports.
    """
    
    def __init__(self, bot) -> None:
        self.bot = bot
        self.coll = bot.api.get_plugin_partition(self)
        self.config = Config(self)
        self.commands = Commands(self)
        self.evidence_bot = EvidenceBot(self)


    async def cog_load(self) -> None:
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

        # Load current config
        await self.config.get()
        # Close and destory old bot if exists
        if self.evidence_bot:
            await self.evidence_bot.destroy()

        try:
            # If the plugin mode is using the evidence bot
            if self.config.document.get("plugin_mode", PluginMode.Disabled) == PluginMode.EvidenceBot:
                await self.evidence_bot.create()
                await self.evidence_bot.start()
            await self.commands.reload()
        except ValueError as err:
            logger.warning(str(err))
        except Exception as err:
            logger.exception(str(err))

    async def cog_unload(self) -> None:
        if self.evidence_bot:
            await self.evidence_bot.destroy()
        if self.bot.tree.get_command(self.commands.add_as_evidence_command.name, type=self.commands.add_as_evidence_command.type):
            self.bot.tree.remove_command(self.commands.add_as_evidence_command.name, type=self.commands.add_as_evidence_command.type)  
        await self.bot.tree.sync()


    # Configure the the plugin
    @commands.command(name="evidence-config", aliases=["econfig"])
    @checks.has_permissions(PermissionLevel.OWNER)
    async def evidence_config(self, ctx: Context) -> None:
        em = Embed(title="Evidence Configuration")
        em.description = "\n".join([
            "Configure the Evidence plugin using the buttons below",
            "",
            "You may need to reload the plugin after changing settings, or to register the commands"
        ])
        em.color = Color.blurple()
        em.add_field(
            name="Plugin Mode",
            value="\n".join([
                "**Disabled**: The plugin is disabled.",
                "**Primary**: The plugin registers the commands to the primary (main) bot.",
                "**EvidenceBot** (Exprimental): The plugin registers the commands to a spesific bot, You will need to add an environment variable for `EVIDENCE_BOT_TOKEN`"
            ]),
            inline=False
        )
        config_view = EvidenceConfigView(self, ctx.author.id)
        config_view.message = await ctx.send(embed=em, view=config_view)


# Setup function for Discord.py main bot thing
async def setup(bot) -> None:
    await bot.add_cog(Evidence(bot))