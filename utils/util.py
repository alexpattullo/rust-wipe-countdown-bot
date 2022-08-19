import asyncio
import json
import re
import aiohttp
import discord
from dateutil.relativedelta import relativedelta
from discord import colour, Intents
from discord.ext.commands import ColourConverter
from motor.motor_asyncio import AsyncIOMotorClient
from discord.ext import commands, tasks


class utilmisc():
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
          """Wraps a string to send formatted as an embed"""
          target = target or ctx.channel

          embed = discord.Embed(description=desc,color=self.bot.embed_hex)

          if color:
               embed.colour = color

          if contain_timestamp:
               embed.timestamp = ctx.message.created_at

          if include_command_invoker:
               embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar.url)

          return await target.send(embed=embed, **kwargs)


     async def get_input(self,ctx,title: str = None,description: str = None,*,timeout: int = 100,delete_after: bool = False,author_id=None):
          if title and not description:
               embed = discord.Embed(
                    title=title,
                    colour= self.bot.embed_hex
               )
          elif not title and description:
               embed = discord.Embed(
                    description=description,
                    colour= self.bot.embed_hex
               )
          elif title and description:
               embed = discord.Embed(
                    title=title,
                    description=description,
                    colour= self.bot.embed_hex
               )
          else:
               raise RuntimeError("Expected atleast title or description")

          sent = await ctx.send(embed=embed)
          val = None

          author_id = author_id or ctx.author.id or ctx.id  # or self.id for User/Member

          try:
               msg = await ctx.bot.wait_for(
                    "message",
                    timeout=timeout,
                    check=lambda message: message.author.id == author_id,
               )
               if msg:
                    val = msg.content
          except asyncio.TimeoutError:
               if delete_after:
                    await sent.delete()

               return val

          try:
               if delete_after:
                    await sent.delete()
                    await msg.delete()
          finally:
               return val

     async def time_convertor(argument):
          time_regex = re.compile(r"(( ?(\d{1,5})(h|s|m|d))+)")
          time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}
          args = argument.lower()
          matches = re.findall(time_regex, args)
          if not matches:
               return 0

          matches = matches[0][0].split(" ")
          matches = [filter(None, re.split(r"(\d+)", s)) for s in matches]
          time = 0
          for match in matches:
               key, value = match
               try:
                    time += time_dict[value] * float(key)
               except KeyError:
                    raise commands.BadArgument(
                         f"{value} is an invalid time key! h|m|s|d are valid arguments"
                    )
               except ValueError:
                    raise commands.BadArgument(f"{key} is not a number!")
          return time


     async def pop_from_bmid(id):
          url = (f"https://api.battlemetrics.com/servers/{id}")
          pop_info = ""
          ConnectedPlayers = 0
          MaxPlayers = 0
          QueuedPlayers = 0
          async with aiohttp.ClientSession() as session:
               async with session.get(url) as resp:
                    if resp.status != 200:
                         print(f"Battlemetrics - Error with status code: {resp.status}")
                         pop_info = f"Server didn't respond... - (`{resp.status}`)"
                    if resp.status == 200:
                         resp_dict = json.loads(await resp.text())
                         try:
                              ConnectedPlayers = resp_dict["data"]["attributes"]["players"] 
                              MaxPlayers = resp_dict["data"]["attributes"]["maxPlayers"]
                              QueuedPlayers = resp_dict["data"]["attributes"]["details"]["rust_queued_players"]
                         except:
                              pass #FallbackSince if its not a rust server id will break
          
          if pop_info != f"Server didn't respond... - (`{resp.status}`)":
               if QueuedPlayers > 0:
                    pop_info = f" : {ConnectedPlayers}/{MaxPlayers} Q:{QueuedPlayers}"
               else:
                    pop_info = f" : {ConnectedPlayers}/{MaxPlayers}"
          
          return pop_info