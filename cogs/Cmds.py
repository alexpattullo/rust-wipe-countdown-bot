import discord
import logging
from datetime import datetime,timezone
from discord.ext.commands import ColourConverter
from discord.ext import commands
from utils.util import utilmisc
import random
import string


LOGGER = logging.getLogger(__name__)

class EmbedOrServerCreate(discord.ui.View):
    def __init__(self,*,timeout=60):
        super().__init__(timeout=timeout)
        self.value = None
        
    @discord.ui.button(label="Server", style=discord.ButtonStyle.blurple)
    async def Server(self, interaction: discord.Interaction, button: discord.ui.Button):
         for child in self.children:
               child.disabled=True
         await interaction.response.edit_message(view=self)
         self.value = "Server"
         self.stop()

    @discord.ui.button(label='Embed', style=discord.ButtonStyle.red)
    async def Embed(self, interaction: discord.Interaction, button: discord.ui.Button):
         for child in self.children:
               child.disabled=True
         await interaction.response.edit_message(view=self)
         self.value = "Embed"
         self.stop()

class ConfirmView(discord.ui.View):
    def __init__(self,*,timeout=60):
        super().__init__(timeout=timeout)
        self.value = None
        
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def Confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
         for child in self.children:
               child.disabled=True
         await interaction.response.edit_message(view=self)
         self.value = "Confirm"
         self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def Cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
         for child in self.children:
               child.disabled=True
         await interaction.response.edit_message(view=self)
         self.value = "Cancel"
         self.stop()


class SelectC(discord.ui.Select):
    def __init__(self,bot):
         self.bot = bot
         super().__init__(options = None , placeholder=None,min_values = 1,max_values = 1)


    async def callback(self, interaction: discord.Interaction):
      self.view.response = self.values
      self.disabled = True
      self.view.stop()
      await interaction.response.edit_message(view=self.view)


class SelectCView(discord.ui.View):
    def __init__(self,bot, *, timeout = 60):
         self.bot = bot
         super().__init__(timeout=timeout)
         #self.add_item(SelectC(self.bot))
         self.response = None


class Cmds(commands.Cog):
   def __init__(self, bot):
      self.bot = bot

   @commands.Cog.listener()
   async def on_ready(self):
      LOGGER.info("%s cog loaded", self.__class__.__name__)


   @commands.command()
   async def help(self,ctx):
      guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
      StaffRole = guild.get_role(self.bot.data["Discord_Config"]["StaffRole_ID"])
      if StaffRole not in ctx.author.roles:
         await ctx.message.delete()
         return await ctx.send(f"> **Error** : You dont have the required role to use this command `{StaffRole.name}`",delete_after=15)

      embed = discord.Embed(
         title="**List of Commands**",
         description=f"**{ctx.prefix}create** - create a server wipe / new embed\n"
         f"**{ctx.prefix}wipe** - displays all servers and their next wipes\n"
         f"**{ctx.prefix}list** - shows current embeds & wipes\n"
         f"**{ctx.prefix}editembed** <msgid / id> - allows you to change the embed\n"
         f"**{ctx.prefix}editserver** <id> - allows you to change serverinfo\n"
         f"**{ctx.prefix}delete server/embed <id>** - delete a wipe\n",
         colour=self.bot.embed_hex,
      )
      await ctx.send(embed=embed)

   @commands.command()
   async def force(self,ctx):
      if not getattr(self.bot, "force", None):
         return await ctx.send("The force-wipe schedule is not ready yet. Please try again shortly.")
      await ctx.send(f"The next force wipe takes place <t:{int(self.bot.force)}:F> - (<t:{int(self.bot.force)}:R>)")

   @commands.command()
   async def wipe(self,ctx):
         wipes =  await self.bot.wipes.get_all()
         if len(wipes) == 0:
            return await ctx.send(embed=discord.Embed(description=f"> **Error** : No current servers.",color=self.bot.embed_hex))
         description = ""
         for wipe in wipes:
            description += f"{wipe['ServerInfo']['name']}: <t:{int(wipe['next_wipe_display'])}:F> - (<t:{int(wipe['next_wipe_display'])}:R>)\n"
         
         wipeembed = discord.Embed(title = self.bot.data["Misc"]["Server_Name"],description = description[0:1020],color = self.bot.embed_hex )
         wipeembed.set_footer(text="Automatically displayed in your local timezone!")
         await ctx.send(embed=wipeembed)



   @commands.command()
   async def create(self,ctx):
      guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
      StaffRole = guild.get_role(self.bot.data["Discord_Config"]["StaffRole_ID"])
      if StaffRole not in ctx.author.roles:
         await ctx.message.delete()
         return await ctx.send(f"> **Error** : You dont have the required role to use this command `{StaffRole.name}`",delete_after=15)

      embeds = await self.bot.embeds.get_all()
      view = EmbedOrServerCreate()
      await ctx.send(embed=discord.Embed(description=f"What would you like to create? - A new server or embed?",colour=self.bot.embed_hex),view=view)
      
      await view.wait()
      if view.value is None:
         await ctx.send("> **Error** : You have taken too long to answer")
         type = None
      else:
         type = view.value
         if type == "Server":
               if len(embeds) <= 0:
                  return await ctx.send(embed=discord.Embed(description=f"> **Error** : You must create a embed first!",colour=self.bot.embed_hex))
               else:
                  options = []
                  for embed in embeds:
                     options.append(discord.SelectOption(label=str(embed["_id"]) + " : " + embed["title"],value=embed["_id"]))
                  view = SelectCView(self.bot)
                  select = SelectC(self.bot)
                  select.options = options
                  select.placeholder = f"Select the embed you would like this to be in."
                  view.add_item(select)

                  await ctx.send(f"Which embed would you like this to be in?",view=view)     

                  await view.wait()
                  if not view.response:
                     return await ctx.send("> **Error** : You took too long to answer")
                  else:
                     ServerName = await utilmisc.get_input(self,ctx,description="Please provide the server name (Capitals are important)\nExample :\n\n :flag_eu: **__EU 2x Main__** *using bold & underlining is important*")
                     ServerIP = await utilmisc.get_input(self,ctx,description="What is the IP connect for this server?\nExample : `connect eumain.skizzyrust.com:28015`/`connect 51.195.60.74:28015`",)
                     ServerInfo = await utilmisc.get_input(self,ctx,description="Please provide any server information\nExample :\n\nMap Wipe Friday @ 5pm BST\nTeam UI : 4 Max\nMap Size : 3700",)
                     ServerBMID = await utilmisc.get_input(self,ctx, description="What is the battlemetrics ID for this server?\n> Example : **1234143** would be the id [here](https://cdn.discordapp.com/attachments/944601713023795281/973941405128986714/Screenshot_2022-05-11_at_14.35.22.png).")
                     if not await utilmisc.battlemetrics_server_exists(ServerBMID):
                        return await ctx.send(f"> **Error** : `{ServerBMID}` is not a valid battlemetrics server ID.")
                        

                     type_wipe = await utilmisc.get_input(self,ctx, description="Is this wipe schedule `monthly`,`biweekly`,`weekly`or `custom`(mutliple wipes a week)?")
                     if type_wipe.lower() not in ["monthly", "biweekly", "weekly","custom"]:
                        return await ctx.send("> **Error** : Invalid type of server,  Allowed : `monthly`,`biweekly`,`weekly` or `custom`")
                        

                     if not ServerName or not ServerIP or not ServerInfo or not ServerBMID or not type_wipe:
                        return await ctx.send("> **Error** : You failed to answer all the questions.")

                     if type_wipe == "monthly":
                        data = {
                           "_id":(''.join(random.choices((string.ascii_letters + string.digits), k=25))),
                           "wipe_type":"monthly",
                           "next_wipe_display":0,
                           "last_wipe":0,
                           "ServerInfo":{
                              "name":ServerName,
                              "ip":ServerIP,
                              "serverinfo":ServerInfo,
                              "bmid":ServerBMID
                           },
                           "embed_id":int(view.response[0])
                        }
                        await self.bot.wipes.insert(data)
                        return await ctx.send(f'Done, I have created a new wipe for "**{data["ServerInfo"]["name"]}**"')

                     else:
                        WipesForce = await utilmisc.get_input(self,ctx, description="Does the server wipe at force? (or skip it) - `Yes`/`No`")
                        if WipesForce.lower() == "yes":
                           WipesForce = True
                        elif WipesForce.lower() == "no":
                           WipesForce = False
                        else:
                           return await ctx.send(f"> **Error** : `{WipesForce}` is not a valid response. (`Yes`/`No`)")


                        if type_wipe == "biweekly" or type_wipe == "weekly":
                           next_wipe = await utilmisc.get_input(
                                 self,
                                 ctx,
                                 description=f"Please provide the epoch timestamp for the **Next Wipe**\n"
                                 f"Current time: **{int(datetime.now(timezone.utc).timestamp())}**\n"
                                 f"Use [epochconverter.com](https://www.epochconverter.com/) or [unixtimestamp.com](https://www.unixtimestamp.com/) UTC TIME!",
                           )
                           if not next_wipe:
                              return await ctx.send("Cancelling...")

                           if next_wipe.isdecimal():
                              next_wipe = datetime.fromtimestamp(float(next_wipe), tz=timezone.utc)

                           else:
                              time = await utilmisc.time_convertor(next_wipe)
                              next_wipe = datetime.fromtimestamp(
                                 datetime.now(timezone.utc).timestamp() + time,
                                 tz=timezone.utc,
                              )

                           if type_wipe == "biweekly" and next_wipe.weekday() != 3:
                              return await ctx.send(f"> **Error** : `{next_wipe}` was not a thursday.")
                           
                           if WipesForce and self.bot.force < int(next_wipe.timestamp()):
                              display = int(self.bot.force)
                           else:
                              display = int(next_wipe.timestamp())

                           data = {
                              "_id":(''.join(random.choices((string.ascii_letters + string.digits), k=25))),
                              "wipe_type":type_wipe.lower(),
                              "next_wipe_display":display,
                              "next_wipe":int(next_wipe.timestamp()),
                              "last_wipe":0,
                              "WipesForce":WipesForce,
                              "ServerInfo":{
                                 "name":ServerName,
                                 "ip":ServerIP,
                                 "serverinfo":ServerInfo,
                                 "bmid":ServerBMID
                              },
                              "embed_id":int(view.response[0])
                           }
                           await self.bot.wipes.insert(data)
                           return await ctx.send(f'Done, I have created a new wipe for "**{data["ServerInfo"]["name"]}**"')

                        elif type_wipe == "custom":
                           Num_Wipes = await utilmisc.get_input(self,ctx, description="How many wipes does this server have a week? eg : `2`,`3`,`4`,`5`")
                           try:
                              Num_Wipes = int(Num_Wipes)
                           except (TypeError, ValueError):
                              return await ctx.send("> **Error** : That is not a number or less than 2")
                           if Num_Wipes < 2:
                              return await ctx.send("> **Error** : That is not a number or less than 2")
                           
                           await ctx.send("I will go through each wipe asking you some questions.")
                           
                           wipes = []
                           for wipe_i in range(Num_Wipes):
                              next_wipe = await utilmisc.get_input(
                                    self,
                                    ctx,
                                    description=f"Please provide the epoch timestamp for the **Next Wipe**\n"
                                    f"Current time: **{int(datetime.now(timezone.utc).timestamp())}**\n"
                                    f"Use [epochconverter.com](https://www.epochconverter.com/) or [unixtimestamp.com](https://www.unixtimestamp.com/)",
                              )
                              if not next_wipe:
                                 return await ctx.send("Cancelling...")

                              if next_wipe.isdecimal():
                                 next_wipe = datetime.fromtimestamp(float(next_wipe), tz=timezone.utc)

                              else:
                                 time = await utilmisc.time_convertor(next_wipe)
                                 next_wipe = datetime.fromtimestamp(
                                    datetime.now(timezone.utc).timestamp() + time,
                                    tz=timezone.utc,
                                 )
                              
                              wipes.append(int(next_wipe.timestamp()))
                           data = {
                              "_id":(''.join(random.choices((string.ascii_letters + string.digits), k=25))),
                              "wipe_type":type_wipe.lower(),                           
                              "next_wipe_display":0,
                              "wipes":wipes,
                              "last_wipe":0,
                              "WipesForce":WipesForce,                              
                              "ServerInfo":{
                                 "name":ServerName,
                                 "ip":ServerIP,
                                 "serverinfo":ServerInfo,
                                 "bmid":ServerBMID
                              },
                              "embed_id":int(view.response[0])
                           }
                           await self.bot.wipes.insert(data)
                           return await ctx.send(f'Done, I have created a new wipe for "**{data["ServerInfo"]["name"]}**"')                         
                           
         if type == "Embed":
            channel_id = await utilmisc.get_input(self,ctx, description="What is the channel id of the channel you want this embed in?")

            try:
               channel_id = int(channel_id)
            except (TypeError, ValueError):
               return await ctx.send("> **Error** : That is not a valid Discord channel ID.")

            guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
            channel = guild.get_channel(channel_id) if guild else None
            if channel == None:
               channel = await  self.bot.fetch_channel(channel_id)       
            
            if not channel:
               return await ctx.send(f"> **Error** : I was unable to fetch that channel. <#{channel_id}>")

            m = await channel.send(embed=discord.Embed(description=f"Waiting to be edited, `{ctx.prefix}editembed`",colour=self.bot.embed_hex))
            await self.bot.embeds.insert(
               {
                  "_id": m.id,
                  "channel_id":channel.id,
                  "title": "Set with !changembed",
                  "description": "Set with !changembed",
                  "footer": "Set with !changembed",
                  "thumbnail": "https://cdn.discordapp.com/attachments/860941782887039007/911970910439895050/ss.png",
                  "color": self.bot.embed_hex,
               }
            )
            await ctx.send(embed=discord.Embed(description=f"[All Done!]({m.jump_url}) , to edit this embed use `{ctx.prefix}editembed {m.id}`",colour=self.bot.embed_hex))



   @commands.command()
   async def delete(self,ctx,item,id):
      guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
      StaffRole = guild.get_role(self.bot.data["Discord_Config"]["StaffRole_ID"])
      if StaffRole not in ctx.author.roles:
         await ctx.message.delete()
         return await ctx.send(f"> **Error** : You dont have the required role to use this command `{StaffRole.name}`",delete_after=15)

      if item.lower() == "server":
         server = await self.bot.wipes.find_by_custom({"_id": id})
         if not server:
            return await ctx.send(f"> **Error** : Invalid server id use `{ctx.prefix}list` for a list of ids")
         
         view = ConfirmView()
         msg = await ctx.send(embed=discord.Embed(title="Delete Confirmation",description=f"Are you sure you want to delete **{server['ServerInfo']['name']}**?",colour = self.bot.embed_hex),view=view)   
         await view.wait()
         if view.value is None:
            await ctx.send("> **Error** : You have taken too long to answer")
            type = None
         else:
            type = view.value
            if type == "Confirm":
               await self.bot.wipes.delete(server)   
               return await msg.edit(embed=discord.Embed(title="Confirmed",description=f"I have deleted **{server['ServerInfo']['name']}**.",colour = 0x00FF00)) 
            else:
               return await msg.edit(embed=discord.Embed(description=f"Cancelling...",colour = 0xff0000))
      
      elif item.lower() == "embed":
         embed = await self.bot.embeds.find_by_custom({"_id": int(id)})
         if not embed:
            return await ctx.send("> **Error** : Invalid embed id, please use the embed msg id")
         
         view = ConfirmView()
         msg = await ctx.send(embed=discord.Embed(title="Delete Confirmation",description=f"Are you sure you want to delete this embed? (This will delete all servers contained inside it)",colour = self.bot.embed_hex),view=view)   
         await view.wait()
         if view.value is None:
            await ctx.send("> **Error** : You have taken too long to answer")
            type = None
         else:
            type = view.value
            if type == "Confirm":
               await self.bot.embeds.delete(embed)   
               servers = await self.bot.wipes.find_many_by_custom({"embed_id":embed["_id"]})
               for server in servers:
                  await self.bot.wipes.delete(server)
               
               try:
                  channel = guild.get_channel(embed["channel_id"])
                  if channel == None:
                     channel = await self.bot.fetch_channel(embed["channel_id"])       

                  embed_msg = await channel.fetch_message(embed["_id"])   
                  await embed_msg.delete()
               except (discord.NotFound, discord.Forbidden, discord.HTTPException, AttributeError, TypeError, ValueError):
                  LOGGER.info("Embed message %s was already unavailable", embed.get("_id"))

               return await msg.edit(embed=discord.Embed(title="Confirmed",description=f"I have deleted that embed.",colour = 0x00FF00)) 
            else:
               return await msg.edit(embed=discord.Embed(description=f"Cancelling...",colour = 0xff0000))         
      

      else:
         return await ctx.send(f"> **Error** : `{item.lower()}` is not a `server`/`embed`")


   @commands.command()
   async def list(self,ctx):
      guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
      StaffRole = guild.get_role(self.bot.data["Discord_Config"]["StaffRole_ID"])
      if StaffRole not in ctx.author.roles:
         await ctx.message.delete()
         return await ctx.send(f"> **Error** : You dont have the required role to use this command `{StaffRole.name}`",delete_after=15)

      s_list = []
      s_all = await self.bot.wipes.get_all()
      embeds = await self.bot.embeds.get_all()
      if len(embeds) == 0:
         return await ctx.send(f"> **Error** : No embeds exist :(")
      for embed in embeds:
         e_embed = discord.Embed(title=embed["title"],description=embed["description"],color=embed["color"])
         e_embed.set_footer(text=embed["footer"])
         e_embed.set_thumbnail(url=embed["thumbnail"])

         servers = await self.bot.wipes.find_many_by_custom({"embed_id":embed["_id"]})
         for server in servers:
            if server["_id"] not in s_list:
               s_list.append(server["_id"])
            name = server["ServerInfo"]["name"] + await utilmisc.pop_from_bmid(server["ServerInfo"]["bmid"])
            if datetime.now(timezone.utc).timestamp() - server["last_wipe"] <= 86400: #Less than a day
               name += f" — JUST WIPED: <t:{int(server['last_wipe'])}:R>"
            e_embed.add_field(
               name=name,
               value = (
                  f"IP: `{server['ServerInfo']['ip']}`\n"
                  f"Next Wipe: <t:{int(server['next_wipe_display'])}:F> - (<t:{int(server['next_wipe_display'])}:R>)\n"
                  f"{server['ServerInfo']['serverinfo']}\n"
                  f"Server ID : `{server['_id']}`"
               )
               ,inline=False
            )
         await ctx.send(f"<#{embed['channel_id']}> Embed ID : {embed['_id']} https://discord.com/channels/{self.bot.user.id}/{embed['channel_id']}/{embed['_id']}",embed=e_embed)

      for s in s_all:
         if s["_id"] not in s_list:
            name = s["ServerInfo"]["name"] + await utilmisc.pop_from_bmid(s["ServerInfo"]["bmid"])
            if datetime.now(timezone.utc).timestamp() - s["last_wipe"] <= 86400: #Less than a day
               name += f" — JUST WIPED: <t:{int(s['last_wipe'])}:R>"

            value = (
               f"IP: `{s['ServerInfo']['ip']}`\n"
               f"Next Wipe: <t:{int(s['next_wipe_display'])}:F> - (<t:{int(s['next_wipe_display'])}:R>)\n"
               f"{s['ServerInfo']['serverinfo']}\n"
               f"Server ID : `{s['_id']}`"
            )
            await ctx.send(f"{name}\n{value}")
           




   @commands.command(aliases=["changeembed"])
   async def editembed(self,ctx, embed_id=None):
      guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
      StaffRole = guild.get_role(self.bot.data["Discord_Config"]["StaffRole_ID"])
      if StaffRole not in ctx.author.roles:
         await ctx.message.delete()
         return await ctx.send(f"> **Error** : You dont have the required role to use this command `{StaffRole.name}`",delete_after=15)

      if not embed_id:
         return await ctx.send(f"Give me the embed id to edit, `{ctx.prefix}editembed <embedmsg id>`")

      data = await self.bot.embeds.find_by_custom({"_id": int(embed_id)})

      if not data:
         return await ctx.send("> **Error** : Invalid embed id, please use the embed msg id")

      view = SelectCView(self.bot)
      select = SelectC(self.bot)
      select.options = [
         discord.SelectOption(label="Title",description="Edit the embeds title",value="Title"),
         discord.SelectOption(label="Description",description="Edit the embeds Description",value="Description"),
         discord.SelectOption(label="Footer",description="Edit the embeds footer",value="Footer"),
         discord.SelectOption(label="Color",description="Edit the embeds color",value="Color"),
         discord.SelectOption(label="Thumbnail",description="Edit the embeds thumbnail",value="Thumbnail"),
         
      ]
      select.placeholder = f"Select the feature to edit."
      view.add_item(select)


      await ctx.send(embed=discord.Embed(title="Pick something to edit",colour=self.bot.embed_hex),view=view)

      await view.wait()
      if not view.response:
         return await ctx.send("> **Error** : You took too long to answer")
      else:
            answer = view.response[0]
            if answer == "Title":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new title to be?")
               data["title"] = change_to

            elif answer == "Description":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new description to be?")
               data["description"] = change_to

            elif answer == "Footer":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new footer to be?")
               data["footer"] = change_to
               
            elif answer == "Color":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new color to be?")
               color = await ColourConverter().convert(ctx, change_to)
               data["color"] = color.value

            elif answer == "Thumbnail":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new thumbnail to be? Use an imgur or discord link etc")
               data["thumbnail"] = change_to

            await self.bot.embeds.update_by_custom({"_id": data["_id"]}, data)
            return await ctx.send(f"Done, I have updated that for you!")


   @commands.command(aliases=["changeserver"])
   async def editserver(self,ctx, server_id=None):
      guild = self.bot.get_guild(self.bot.data["Discord_Config"]["Guild_ID"])
      StaffRole = guild.get_role(self.bot.data["Discord_Config"]["StaffRole_ID"])
      if StaffRole not in ctx.author.roles:
         await ctx.message.delete()
         return await ctx.send(f"> **Error** : You dont have the required role to use this command `{StaffRole.name}`",delete_after=15)

      if not server_id:
         return await ctx.send(f"Give me the server id to edit, `{ctx.prefix}editserver <server id>`")

      wipe = await self.bot.wipes.find_by_custom({"_id": server_id})
      if not wipe:
         return await ctx.send(f"> **Error** : Invalid server id use `{ctx.prefix}list` for a list of ids")

      
      view = SelectCView(self.bot)
      select = SelectC(self.bot)
      options = [
         discord.SelectOption(label="Name",description="Edit the servers name",value="Name"),
         discord.SelectOption(label="Info",description="Edit the servers info",value="Info"),
         discord.SelectOption(label="IP Connect",description="Edit the IP Connect",value="IPConnect"),
         discord.SelectOption(label="BmID",description="Edit the servers bmid",value="BmID"),
         discord.SelectOption(label="Embed its in",description="Edit which embed the server is in",value="Embed"),
      ]
      if wipe["wipe_type"] == "weekly" or wipe["wipe_type"] == "biweekly":
         options.append(discord.SelectOption(label="When's wipe",description="Edit the wipetime for the server",value="SWipe"),)
      
      select.options = options
      select.placeholder = f"Select what you wish to edit."
      view.add_item(select)

      await ctx.send(embed=discord.Embed(title="Pick something to edit",colour=self.bot.embed_hex),view=view)

      await view.wait()
      if not view.response:
         return await ctx.send("> **Error** : You took too long to answer")
      else:
            if view.response[0] == "Name":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new servername to be?")
               wipe["ServerInfo"]["name"] = change_to

            elif view.response[0] == "Embed":
               change_to = await utilmisc.get_input(self,ctx, "What is the msg id of the embed you want the server to be in?")
               if change_to:
                  try:
                     change_to = int(change_to)
                  except (TypeError, ValueError):
                     return await ctx.send("> **Error** : Invalid embed ID")
                  embed = await self.bot.embeds.find_by_custom({"_id":int(change_to)})
                  if not embed:
                     return await ctx.send("> **Error** : Invalid embed ID")
                  wipe["embed_id"] = int(change_to)

            elif view.response[0] == "Info":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new server description to be?")
               wipe["ServerInfo"]["serverinfo"] = change_to                                

            elif view.response[0] == "IPConnect":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new server IP connect to be?")
               wipe["ServerInfo"]["ip"] = change_to           

            elif view.response[0] == "BmID":
               change_to = await utilmisc.get_input(self,ctx, "What do you want the new bmid to be?")
               wipe["ServerInfo"]["bmid"] = change_to   
            
            elif view.response[0] == "SWipe":
               next_wipe = await utilmisc.get_input(
                     self,
                     ctx,
                     description=f"Please provide the epoch timestamp for the **Next Wipe**\n"
                     f"Current time: **{int(datetime.now(timezone.utc).timestamp())}**\n"
                     f"Use [epochconverter.com](https://www.epochconverter.com/) or [unixtimestamp.com](https://www.unixtimestamp.com/) UTC TIME!",
               )
               if not next_wipe:
                  return await ctx.send("Cancelling...")

               if next_wipe.isdecimal():
                  next_wipe = datetime.fromtimestamp(float(next_wipe), tz=timezone.utc)

               else:
                  time = await utilmisc.time_convertor(next_wipe)
                  next_wipe = datetime.fromtimestamp(
                     datetime.now(timezone.utc).timestamp() + time,
                     tz=timezone.utc,
                  )

               if wipe["wipe_type"] == "biweekly" and next_wipe.weekday() != 3:
                  return await ctx.send(f"> **Error** : `{next_wipe}` was not a thursday.")
               

               if wipe["WipesForce"] and self.bot.force < int(next_wipe.timestamp()):
                  display = int(self.bot.force)
               else:
                  display = int(next_wipe.timestamp())

               wipe["next_wipe"] = int(next_wipe.timestamp())
               wipe["next_wipe_display"] = display
               
            await self.bot.wipes.update(wipe)
            return await ctx.send(f'Done, I have updated **{wipe["ServerInfo"]["name"]}**!')


async def setup(bot):
  await bot.add_cog(Cmds(bot))
