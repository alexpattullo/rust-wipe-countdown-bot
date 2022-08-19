import asyncio
import json
from discord import colour, Intents
from discord.ext.commands import ColourConverter
from motor.motor_asyncio import AsyncIOMotorClient
from utils.mongo import Document
from discord.ext import commands, tasks
import logging
logging.basicConfig(level=logging.INFO)


with open("config.json", "r") as f:
    data = json.load(f)
bot = commands.Bot(command_prefix=data["Misc"]["Bot_Prefix"], intents=Intents.all(), help_command=None)
bot.embed_hex = int(data["Misc"]["Embed_Hex_Color"].replace("#", "0x"), 16)
bot.data = data
bot.force = 999999999999999999999

@bot.event
async def on_ready():
    print("We have logged in as {0.user}\n".format(bot))

@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        return

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("> **Error** : You have not passed all the required arguments.")

    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        raise error



extensions = [
  "cogs.Cmds",
  "cogs.Embeds",
  "cogs.Servers"
]  
async def main():
    if __name__ == "__main__":
        for ext in extensions:
            await bot.load_extension(ext)
        async with bot:
            db = AsyncIOMotorClient(data["Mongo_Config"]["MONGO_URL"]).rust_wipes
            bot.wipes = Document(db, "wipes")
            bot.embeds = Document(db, "embeds")
            await bot.start(data["Misc"]["Bot_Token"],reconnect=True)
asyncio.run(main())