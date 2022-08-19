import discord
import datetime as dt
from datetime import datetime,timezone
from dateutil.relativedelta import relativedelta
from discord import colour, Intents
from discord.ext.commands import ColourConverter
from motor.motor_asyncio import AsyncIOMotorClient
from discord.ext import commands, tasks
from utils.util import utilmisc
from utils.util import utilmisc
import asyncio
import discord.errors


class Embeds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_task.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} Cog has been loaded\n-----")
        

    @tasks.loop(seconds=30.0)
    async def embed_task(self):
        guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
        embeds = await self.bot.embeds.get_all()
        for embed in embeds:
            await asyncio.sleep(3)

            #Fetch the discord channel
            try:
                channel = guild.get_channel(embed["channel_id"])
                if channel == None:
                    channel = await self.bot.fetch_channel(embed["channel_id"])        
            except:
                channel = None

            #No channel skip to next one
            if not channel:
                print(f"Error : Cannot fetch channel -> {embed['channel_id']}")
                continue
            
            #Fetch the discord message 
            #If message not found send a new one
            try:
                msg = await channel.fetch_message(embed["_id"])   
            except:
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

                print(f"Error : Failed to  fetch message -> {embed['_id']}, created a new one")
                

            e_embed = discord.Embed(title=embed["title"],description=embed["description"],color=embed["color"])
            e_embed.set_footer(text=embed["footer"])
            e_embed.set_thumbnail(url=embed["thumbnail"])

            servers = await self.bot.wipes.find_many_by_custom({"embed_id":embed["_id"]})
        
            for server in servers:
                await asyncio.sleep(3)
                name = server["ServerInfo"]["name"] + await utilmisc.pop_from_bmid(server["ServerInfo"]["bmid"])

                if datetime.now(timezone.utc).timestamp() - server["last_wipe"] <= 86400: #Less than a day
                    name += f" — JUST WIPED: <t:{int(server['last_wipe'])}:R>"

                e_embed.add_field(
                name=name,
                value = (
                    f"IP: `{server['ServerInfo']['ip']}`\n"
                    f"Next Wipe: <t:{int(server['next_wipe_display'])}:F> - (<t:{int(server['next_wipe_display'])}:R>)\n"
                    f"{server['ServerInfo']['serverinfo']}"
                )
                ,inline=False
                )

            if channel and msg:
                try:
                    await msg.edit(embed=e_embed)
                except discord.errors.NotFound:
                    print("Error : Message not found -> will be regen in next run")


    @embed_task.before_loop
    async def before_embed_task(self):
        await self.bot.wait_until_ready()


async def setup(bot):
  await bot.add_cog(Embeds(bot))