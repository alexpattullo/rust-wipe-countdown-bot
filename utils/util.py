"""Shared Discord and API helpers used by the cogs."""

from __future__ import annotations

import asyncio
import logging
import re

import aiohttp
import discord
from discord.ext import commands


LOGGER = logging.getLogger(__name__)
TIME_TOKEN = re.compile(r"(\d{1,5})\s*([hmsd])", re.IGNORECASE)
TIME_UNITS = {"h": 3_600, "s": 1, "m": 60, "d": 86_400}


class utilmisc:
    async def send_basic_embed(
        self,
        ctx,
        desc: str,
        *,
        color=None,
        target=None,
        contain_timestamp: bool = True,
        include_command_invoker: bool = True,
        **kwargs,
    ) -> discord.Message:
        """Send a consistently styled embed."""

        target = target or ctx.channel
        embed = discord.Embed(description=desc, colour=color or self.bot.embed_hex)

        if contain_timestamp:
            embed.timestamp = ctx.message.created_at

        if include_command_invoker:
            avatar = getattr(ctx.author.avatar, "url", None)
            if avatar:
                embed.set_footer(text=ctx.author.display_name, icon_url=avatar)
            else:
                embed.set_footer(text=ctx.author.display_name)

        return await target.send(embed=embed, **kwargs)

    async def get_input(
        self,
        ctx,
        title: str | None = None,
        description: str | None = None,
        *,
        timeout: int = 100,
        delete_after: bool = False,
        author_id=None,
    ):
        if not title and not description:
            raise RuntimeError("Expected at least a title or description")

        embed = discord.Embed(title=title, description=description, colour=self.bot.embed_hex)
        sent = await ctx.send(embed=embed)
        author_id = author_id or ctx.author.id

        try:
            message = await ctx.bot.wait_for(
                "message",
                timeout=timeout,
                check=lambda candidate: candidate.author.id == author_id,
            )
        except asyncio.TimeoutError:
            if delete_after:
                await sent.delete()
            return None

        if delete_after:
            await sent.delete()
            await message.delete()
        return message.content

    @staticmethod
    async def time_convertor(argument: str) -> int:
        """Convert values such as ``2h 30m`` into seconds."""

        if not isinstance(argument, str):
            raise commands.BadArgument("A duration must be text, for example `2h 30m`.")

        value = argument.strip().lower()
        matches = list(TIME_TOKEN.finditer(value))
        if not matches or "".join(match.group(0).replace(" ", "") for match in matches) != value.replace(" ", ""):
            raise commands.BadArgument("Use a duration such as `2h 30m`; valid units are h, m, s and d.")

        return sum(int(match.group(1)) * TIME_UNITS[match.group(2).lower()] for match in matches)

    @staticmethod
    async def battlemetrics_server_exists(server_id: str | int) -> bool:
        """Check that a BattleMetrics server record exists without blocking the bot."""

        url = f"https://api.battlemetrics.com/servers/{server_id}"
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            LOGGER.warning("BattleMetrics lookup failed for server %s", server_id)
            return False

    @staticmethod
    async def pop_from_bmid(server_id: str | int) -> str:
        """Return the current BattleMetrics population text for a server."""

        url = f"https://api.battlemetrics.com/servers/{server_id}"
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return f"Server did not respond... - (`{response.status}`)"
                    payload = await response.json(content_type=None)
                    attributes = payload["data"]["attributes"]
                    connected = attributes["players"]
                    maximum = attributes["maxPlayers"]
                    queued = attributes.get("details", {}).get("rust_queued_players", 0)
        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, TypeError, ValueError):
            return "Server population unavailable"

        suffix = f" Q:{queued}" if queued else ""
        return f" : {connected}/{maximum}{suffix}"
