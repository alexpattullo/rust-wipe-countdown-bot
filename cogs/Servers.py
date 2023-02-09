"""Background task that keeps stored wipe schedules up to date."""

from __future__ import annotations

import logging
import time

from discord.ext import commands, tasks

from utils.scheduling import next_force_wipe, roll_forward


LOGGER = logging.getLogger(__name__)


class Servers(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.server_task.start()

    def cog_unload(self) -> None:
        self.server_task.cancel()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        LOGGER.info("%s cog loaded", self.__class__.__name__)

    @staticmethod
    def _force_overrides(force: int, next_wipe: int, enabled: bool) -> bool:
        return enabled and (force < next_wipe or force - next_wipe < 86_400)

    def _refresh_server(self, server: dict, now: int) -> dict | None:
        """Normalise one stored schedule and return it ready for MongoDB."""

        wipe_type = server.get("wipe_type")
        force = self.bot.force

        if wipe_type == "monthly":
            display = int(server.get("next_wipe_display", 0))
            if display <= now:
                server["last_wipe"] = display
                server["next_wipe_display"] = force
            elif display != force:
                server["next_wipe_display"] = force

        elif wipe_type in {"weekly", "biweekly"}:
            interval = 604_800 if wipe_type == "weekly" else 1_209_600
            next_wipe = roll_forward(server.get("next_wipe", now), interval, now)
            server["next_wipe"] = next_wipe
            display = int(server.get("next_wipe_display", 0))
            if display <= now:
                server["last_wipe"] = display
                server["next_wipe_display"] = (
                    force
                    if self._force_overrides(force, next_wipe, bool(server.get("WipesForce")))
                    else next_wipe
                )

        elif wipe_type == "custom":
            wipes = [roll_forward(wipe, 604_800, now) for wipe in server.get("wipes", [])]
            server["wipes"] = sorted(wipes)
            if not wipes:
                LOGGER.warning("Skipping custom server %s with no wipe dates", server.get("_id"))
                return None

            display = int(server.get("next_wipe_display", 0))
            if display <= now:
                next_wipe = server["wipes"][0]
                server["last_wipe"] = display
                server["next_wipe_display"] = (
                    force
                    if self._force_overrides(force, next_wipe, bool(server.get("WipesForce")))
                    else next_wipe
                )

        else:
            LOGGER.warning("Skipping server %s with unknown wipe type %r", server.get("_id"), wipe_type)
            return None

        return server

    @tasks.loop(seconds=10.0)
    async def server_task(self) -> None:
        now = int(time.time())
        self.bot.force = next_force_wipe()

        try:
            all_servers = await self.bot.wipes.get_all()
        except Exception:
            LOGGER.exception("Could not load wipe schedules; retrying on the next loop")
            return

        for server in all_servers:
            try:
                refreshed = self._refresh_server(server, now)
                if refreshed is not None:
                    await self.bot.wipes.update(refreshed)
            except Exception:
                LOGGER.exception("Could not refresh wipe schedule %s", server.get("_id"))

    @server_task.before_loop
    async def before_server_task(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Servers(bot))
