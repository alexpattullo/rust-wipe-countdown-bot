import discord
from datetime import datetime,timezone
from discord.ext import commands, tasks
from utils.util import utilmisc
import asyncio
import logging


LOGGER = logging.getLogger(__name__)


class Embeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_task.start()

    def cog_unload(self):
        self.embed_task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        LOGGER.info("%s cog loaded", self.__class__.__name__)
        

    @tasks.loop(seconds=30.0)
    async def embed_task(self):
        try:
            guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
            embeds = await self.bot.embeds.get_all()
            for embed in embeds:
                await asyncio.sleep(3)

                #Fetch the discord channel
                try:
                    channel = guild.get_channel(embed["channel_id"]) if guild else None
                    if channel is None:
                        channel = await self.bot.fetch_channel(embed["channel_id"])
                except (discord.NotFound, discord.Forbidden, discord.HTTPException, AttributeError, TypeError, ValueError):
                    channel = None

                #No channel skip to next one
                if not channel:
                    LOGGER.warning("Cannot fetch channel %s", embed.get("channel_id"))
                    continue

                # Fetch the Discord message.
                #If message not found send a new one
                try:
                    msg = await channel.fetch_message(embed["_id"])
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    msg = await channel.send(embed=discord.Embed(title=embed["title"],description=embed["description"],color=embed["color"]))

                    #Update in db
                    old_id = embed["_id"]
                    embed["_id"] = msg.id
                    #Delete the old record input new one (can't update _id field)
                    await self.bot.embeds.delete_by_id(old_id)
                    await self.bot.embeds.insert(embed)

                    #For each server we must update embed_id
                    servers = await self.bot.wipes.find_many_by_custom({"embed_id":old_id})
                    for server in servers:
                        server["embed_id"] = msg.id
                        await self.bot.wipes.update(server)

                    LOGGER.warning("Message %s was missing, so a replacement was created", old_id)


                e_embed = discord.Embed(title=embed["title"],description=embed["description"],color=embed["color"])
                e_embed.set_footer(text=embed.get("footer", ""))
                if embed.get("thumbnail"):
                    e_embed.set_thumbnail(url=embed["thumbnail"])

                servers = await self.bot.wipes.find_many_by_custom({"embed_id":embed["_id"]})

                for server in servers[:25]:
                    await asyncio.sleep(3)
                    name = server["ServerInfo"]["name"] + await utilmisc.pop_from_bmid(server["ServerInfo"]["bmid"])

                    last_wipe = int(server.get("last_wipe", 0))
                    if last_wipe and datetime.now(timezone.utc).timestamp() - last_wipe <= 86400:
                        name += f" - JUST WIPED: <t:{last_wipe}:R>"

                    e_embed.add_field(
                    name=name,
                    value = (
                        f"IP: `{server['ServerInfo']['ip']}`\n"
                        f"Next Wipe: <t:{int(server['next_wipe_display'])}:F> - (<t:{int(server['next_wipe_display'])}:R>)\n"
                        f"{server['ServerInfo'].get('serverinfo', '')}"
                    )
                    ,inline=False
                    )

                if channel and msg:
                    try:
                        await msg.edit(embed=e_embed)
                    except discord.NotFound:
                        LOGGER.warning("Message %s disappeared and will be recreated", embed.get("_id"))
        except Exception:
            LOGGER.exception("Embed refresh task failed; it will retry on the next loop")


    @embed_task.before_loop
    async def before_embed_task(self):
        await self.bot.wait_until_ready()


async def setup(bot):
  await bot.add_cog(Embeds(bot))
