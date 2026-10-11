from discord import (
    ButtonStyle,
    Interaction,
)
from discord.ui import (
    Button,
    button,
    View,
)
from enum import StrEnum

# Type checks
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .evidence import Evidence


class Config:
    def __init__(self, plugin: "Evidence"):
        self.plugin = plugin
        self.document = None

    async def get(self) -> dict[str]:
        cfg = await self.plugin.coll.find_one({"_id": "config"})
        # if not, create default cfg
        if not cfg:
            cfg = {
                "_id": "config",
                "timestamps": {
                    "sync_commands": None,
                    "connect_evidence_bot": None
                },
                "plugin_mode": PluginMode.Disabled,
            }
            self.plugin.coll.insert_one(cfg)
        self.document = cfg
        return cfg

    async def update(self, cfg_updates: dict) -> None:
        await self.plugin.coll.update_one({"_id": "config"}, {"$set": cfg_updates}, upsert=True)
        await self.get()


class PluginMode(StrEnum):
    Disabled = "Disabled"
    Primary = "Primary"
    EvidenceBot = "EvidenceBot"


class EvidenceConfigView(View):
    def __init__(self, plugin: "Evidence", user_id: int | None = None):
        super().__init__(timeout=300)
        self.plugin = plugin
        self.message = None
        self.user_id = user_id

        self.update()


    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


    async def check(self, interaction: Interaction) -> bool:
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message("You do not own this menu", ephemeral=True)
            return False
        return True

    
    # Update the view
    def update(self):
        plugin_mode = self.plugin.config.document.get("plugin_mode", PluginMode.Disabled)
        self.plugin_mode_button.label = f"Mode: {plugin_mode}"
        if plugin_mode == PluginMode.Primary:
            self.plugin_mode_button.style = ButtonStyle.success
        elif plugin_mode == PluginMode.EvidenceBot:
            self.plugin_mode_button.style = ButtonStyle.success
        else:
            self.plugin_mode_button.style = ButtonStyle.grey


    @button()
    async def plugin_mode_button(self, interaction: Interaction, button: Button):
        if not await self.check(interaction):
            return
        plugin_mode = self.plugin.config.document.get("plugin_mode", PluginMode.Disabled)
        if plugin_mode == PluginMode.Disabled:
            plugin_mode = PluginMode.Primary
        elif plugin_mode == PluginMode.Primary:
            plugin_mode = PluginMode.EvidenceBot
        else:
            plugin_mode = PluginMode.Disabled

        await self.plugin.config.update({"plugin_mode": plugin_mode})
        self.update()
        await interaction.response.edit_message(view=self)


    @button(label="Reload Plugin", style=ButtonStyle.primary)
    async def reload_plugin_button(self, interaction: Interaction, button: Button):
        if not await self.check(interaction):
            return
        await interaction.response.defer()
        try:
            if self.plugin.config.document.get("plugin_mode", PluginMode.Disabled) == PluginMode.EvidenceBot:
                await self.plugin.evidence_bot.create()
                await self.plugin.evidence_bot.restart()
            await self.plugin.commands.reload()
            #await self.plugin.commands.sync()
        except Exception as err:
            await interaction.followup.send(f"Error reloading plugin: {err}", ephemeral=True)
            return
        await interaction.followup.send("Plugin reloaded successfully", ephemeral=True)