from datetime import datetime, timezone
from enum import StrEnum

# Type checks
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .evidence import Evidence
    

class RatelimitAction(StrEnum):
    SyncCommands = "sync_commands"
    ConnectBot = "connect_evidence_bot"

# All of these are in seconds
ratelimits = {
    RatelimitAction.SyncCommands: 2,
    RatelimitAction.ConnectBot: 10,
}

async def check_ratelimits(plugin: "Evidence", action: str) -> None:
    timestamp = plugin.config.document.get("timestamps", {}).get(action, None)
    if timestamp:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
        seconds_since = (datetime.now(timezone.utc) - timestamp).total_seconds()
        remaining = ratelimits[action] - seconds_since
        if remaining > 0:
            raise RuntimeError(f"{action} is rate limited, try again in {remaining:.1f} seconds.")
    await plugin.config.update({f"timestamps.{action}": datetime.now(timezone.utc)})