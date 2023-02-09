"""Application entry point for the Wipe Countdown Discord bot."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Mapping

from discord import Intents
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from utils.mongo import Document


LOGGER = logging.getLogger(__name__)


def _required_env(environment: Mapping[str, str], name: str) -> str:
    value = environment.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} must be set before starting the bot")
    return value


def load_config(environment: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Build the runtime configuration from environment variables only."""

    environment = environment or os.environ
    token = _required_env(environment, "DISCORD_BOT_TOKEN")
    mongo_url = _required_env(environment, "MONGO_URL")

    try:
        guild_id = int(_required_env(environment, "GUILD_ID"))
        staff_role_id = int(_required_env(environment, "STAFF_ROLE_ID"))
        embed_hex = int(environment.get("EMBED_HEX_COLOR", "#5865F2").replace("#", "0x"), 16)
    except (TypeError, ValueError) as error:
        raise RuntimeError("GUILD_ID, STAFF_ROLE_ID and EMBED_HEX_COLOR must be valid values") from error

    if guild_id <= 0 or staff_role_id <= 0:
        raise RuntimeError("GUILD_ID and STAFF_ROLE_ID must be positive Discord IDs")

    return {
        "Misc": {
            "Bot_Prefix": environment.get("BOT_PREFIX", "!").strip() or "!",
            "Bot_Token": token,
            "Server_Name": environment.get("SERVER_NAME", "Rust Server").strip() or "Rust Server",
            "Embed_Hex_Color": embed_hex,
        },
        "Mongo_Config": {
            "MONGO_URL": mongo_url,
            "Database_Name": environment.get("MONGO_DATABASE", "rust_wipes").strip() or "rust_wipes",
        },
        "Discord_Config": {
            "Guild_ID": guild_id,
            "StaffRole_ID": staff_role_id,
        },
    }


def create_bot(config: dict[str, Any]) -> commands.Bot:
    """Create a bot instance without starting any network connections."""

    intents = Intents.default()
    intents.message_content = True
    bot = commands.Bot(
        command_prefix=config["Misc"]["Bot_Prefix"],
        intents=intents,
        help_command=None,
    )
    bot.embed_hex = config["Misc"]["Embed_Hex_Color"]
    bot.data = config

    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument: `{error.param.name}`.")
            return
        LOGGER.error("Unhandled command error: %s", error)
        await ctx.send("Something went wrong while running that command.")

    return bot


async def run() -> None:
    config = load_config()
    bot = create_bot(config)
    database_client = AsyncIOMotorClient(
        config["Mongo_Config"]["MONGO_URL"],
        serverSelectionTimeoutMS=10_000,
    )

    try:
        for extension in ("cogs.Cmds", "cogs.Embeds", "cogs.Servers"):
            await bot.load_extension(extension)

        database = database_client[config["Mongo_Config"]["Database_Name"]]
        bot.wipes = Document(database, "wipes")
        bot.embeds = Document(database, "embeds")
        await bot.start(config["Misc"]["Bot_Token"], reconnect=True)
    finally:
        database_client.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run())
