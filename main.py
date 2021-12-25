import os
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!', case_insensitive=True, intents=discord.Intents.all())
token = ""


@bot.event
async def on_ready():
    print("Running")


for e in os.listdir('extensions'):
    if e == '__pycache__' or e.startswith('-'):
        continue
    try:
        bot.load_extension(f'extensions.{e.replace(".py", "")}')
    except Exception as error:
        print(f'{e} 로드 실패.\n{error}')
bot.run(token, reconnect=True)
