from discord import (
    AppCommandType,
    Color,
    Embed,
    Interaction,
    Message,
)
from discord.app_commands import (
    AppInstallationType,
    AppCommandContext,
    ContextMenu,
)
from .ratelimits import (
    RatelimitAction, 
    check_ratelimits,
)
from .config import PluginMode

# Type checks
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .evidence import Evidence


class Commands:
    def __init__(self, plugin: "Evidence"):
        self.plugin = plugin

        # Build the Message Command to add to the reports
        self.add_as_evidence_command = ContextMenu(
            name="Add as Evidence to Report",
            callback=self.on_add_as_evidence_message_command,
            type=AppCommandType.message,
            allowed_installs=AppInstallationType(
                guild=False,
                user=True,
            ),
            allowed_contexts=AppCommandContext(
                guild=False,
                dm_channel=True,
                private_channel=True,
            ),
        )


    async def on_add_as_evidence_message_command(self, interaction: Interaction, message: Message) -> None:
            await interaction.response.defer(ephemeral=True)
    
            thread = await self.plugin.bot.threads.find(recipient_id=interaction.user.id)
            if not thread or not thread.ready:
                await interaction.followup.send("No active thread found", ephemeral=True)
                return
    
            embed = Embed(
                title="Evidence Submitted",
                description=(message.content or "")[:4000],
                color=Color.orange(),
                timestamp=message.created_at,
            )
            embed.set_author(
                name=f"{message.author} ({message.author.id})",
                icon_url=message.author.display_avatar.url,
            )
            embed.add_field(
                name="Sent",
                value=f"<t:{int(message.created_at.timestamp())}:R>",
                inline=True,
            )
    
            embed.set_footer(text="Internal - not visible to the user")
    
            embeds = []
            embeds.append(embed)        
            for a in message.attachments:
                em = Embed(
                    title=f"Attachment: {a.filename}",
                    color=Color.orange(),
                    timestamp=message.created_at,
                )
                if a.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                    em.set_image(url=a.url)
                else:
                    em.description = f"[Download]({a.url})"
                embeds.append(em)
    
            BATCH_SIZE = 10
            for i in range(0, len(embeds), BATCH_SIZE):
                batch = embeds[i:i + BATCH_SIZE]
                sent = await thread.channel.send(embeds=batch)
            
            await self.plugin.bot.api.append_log(
                message,
                message_id=sent.id,
                channel_id=thread.channel.id,
                type_="internal",
            )
    
            await interaction.followup.send("Evidence submitted successfully")


    # Sync the commands with the bots
    async def sync(self) -> None:
        # Checks the rate limit for syncing commands
        await check_ratelimits(self.plugin, RatelimitAction.SyncCommands)

        if not self.plugin.bot.is_ready():
            await self.plugin.bot.wait_until_ready()
        await self.plugin.bot.tree.sync()

        if self.plugin.config.document.get("plugin_mode", PluginMode.Disabled) == PluginMode.EvidenceBot:
            if not self.plugin.evidence_bot.client.is_ready():
                await self.plugin.evidence_bot.client.wait_until_ready()
            await self.plugin.evidence_bot.tree.sync()


    # Reload/readd commands to the bots
    async def reload(self) -> None:
        if self.plugin.config.document.get("plugin_mode", PluginMode.Disabled) == PluginMode.Primary:
            if self.plugin.bot.tree.get_command(self.add_as_evidence_command.name, type=self.add_as_evidence_command.type):
                self.plugin.bot.tree.remove_command(self.add_as_evidence_command.name, type=self.add_as_evidence_command.type)
            self.plugin.bot.tree.add_command(self.add_as_evidence_command)

        elif self.plugin.config.document.get("plugin_mode", PluginMode.Disabled) == PluginMode.EvidenceBot:
            if self.plugin.bot.tree.get_command(self.add_as_evidence_command.name, type=self.add_as_evidence_command.type):
                self.plugin.bot.tree.remove_command(self.add_as_evidence_command.name, type=self.add_as_evidence_command.type)
            if not self.plugin.evidence_bot.get_command(self.add_as_evidence_command.name, type=self.add_as_evidence_command.type):
                self.plugin.evidence_bot.add_command(self.add_as_evidence_command)
