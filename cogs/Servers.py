import arrow
import datetime as dt
from datetime import datetime,timezone
from dateutil.relativedelta import relativedelta
from discord import colour, Intents
from discord.ext.commands import ColourConverter
from motor.motor_asyncio import AsyncIOMotorClient
from discord.ext import commands, tasks
from utils.util import utilmisc
import pytz


class Servers(commands.Cog):
     def __init__(self, bot):
          self.bot = bot
          self.server_task.start()

     @commands.Cog.listener()
     async def on_ready(self):
          print(f"{self.__class__.__name__} Cog has been loaded\n-----")
          

     def check_uk_gmt_bst_xs():
          tz = pytz.timezone('Europe/London')
          now = datetime.now(tz)
          if now.dst():
               return "BST"
          return "GMT"

     def get_force_time():    
          month = arrow.utcnow().span("month")[0]
          now = arrow.utcnow().timestamp()

          while True:
               # Start at 0 on Monday
               day = month.weekday()
               # First day of month
               if day == 0:
                    # money
                    month = month.replace(day=4)
               elif day == 1:
                    # tuesday
                    month = month.replace(day=3)
               elif day == 2:
                    # wednesday
                    month = month.replace(day=2)
               elif day == 3:
                    # thursday
                    pass
               elif day == 4:
                    # friday
                    month = month.replace(day=7)
               elif day == 5:
                    # saturday
                    month = month.replace(day=6)
               elif day == 6:
                    # sunday
                    month = month.replace(day=5)
               else:
                    raise RuntimeError("Lol this broke msg skizzy")

               s_hour = 19
               GMT_BST = Servers.check_uk_gmt_bst_xs()
               if GMT_BST == "GMT":
                    s_hour = 19
               elif GMT_BST == "BST":
                    #BST = UTC/GMT + 1 so must take away an hour
                    s_hour = 18
               month = month.replace(hour=s_hour)

               if (month.timestamp() - now) > 0:
                    # We have a valid timestamp
                    break

               month = month + relativedelta(months=1)
               month = month.replace(day=1)
               month = month.replace(hour=0)

          force_time = int(month.timestamp())
          return force_time


     @tasks.loop(seconds=10.0)
     async def server_task(self):
          now = arrow.utcnow().timestamp()
          self.bot.force = Servers.get_force_time()
          all_servers = await self.bot.wipes.get_all()

          #Go through all servers
          for server in all_servers:

               #Monthly (Force Wipe)
               if server["wipe_type"] == "monthly":
                    #CheckForNewWipe
                    if now > int(server["next_wipe_display"]):#New
                         server["last_wipe"] = server["next_wipe_display"]
                         server["next_wipe_display"] = self.bot.force
                         await self.bot.wipes.update(server)
                    
                    #ResetWipe to force?
                    if int(server["next_wipe_display"]) != self.bot.force:
                         server["next_wipe_display"] = self.bot.force
                         await self.bot.wipes.update(server)

               #Anything but monthly

               #We must check if wipe is in the past
               #We must check if force wipe is "enabled" and is actually the next time
               #If force wipe is < 24 hours away it will override the wipe even if it's not the next wipe
               else:
                    if server["wipe_type"] == "weekly":
                         if now > int(server["next_wipe"]):#New
                              server["next_wipe"] += 604800 #7days
                         
                    elif server["wipe_type"] == "biweekly":
                         next_wipe = server["next_wipe"]
                         while (next_wipe - now) <= 0:
                              gap = (dt.timedelta(weeks=2)).total_seconds()
                              next_wipe = int(gap + next_wipe)
                              server["next_wipe"] = next_wipe
               
                    elif server["wipe_type"] == "custom":
                         w = []
                         for wipe in server["wipes"]:
                              if now > int(wipe):#New
                                   wipe += 604800
                              w.append(wipe)
                         server["wipes"] = w
               
                    #Display wipe vs actual cycle (Force overriding)
                    if server["wipe_type"] == "weekly" or server["wipe_type"] == "biweekly":

                         #Wipe is in past -> New wipe 
                         if now > server["next_wipe_display"]:
                              server["last_wipe"] = server["next_wipe_display"]

                              #If time until force is less than 24h
                              #OR
                              #Force is the next wipe due
                              #AND
                              #Force is enabled
                              if ((self.bot.force - server["next_wipe"] < 86400) or (self.bot.force < server["next_wipe"])) and server["WipesForce"]:
                                   server["next_wipe_display"] = self.bot.force
                              else:
                                   server["next_wipe_display"] = server["next_wipe"]
                    
                    elif server["wipe_type"] == "custom":
                         if now > server["next_wipe_display"]:   
                              server["last_wipe"] = server["next_wipe_display"]
                         
                              server["wipes"].sort()
                              smallest = server["wipes"][0]

                              #If time until force is less than 24h
                              #OR
                              #Force is the next wipe due
                              #AND
                              #Force is enabled
                              if ((self.bot.force - smallest < 86400) or (self.bot.force < smallest)) and server["WipesForce"]:
                                   server["next_wipe_display"] = self.bot.force
                              else:
                                   server["next_wipe_display"] = smallest
                    
                    await self.bot.wipes.update(server)


     @server_task.before_loop
     async def before_server_task(self):
        await self.bot.wait_until_ready()


async def setup(bot):
  await bot.add_cog(Servers(bot))