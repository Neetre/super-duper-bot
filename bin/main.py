import getpass
import os

import discord
from discord.ext import commands
import asyncio

from help_cog import help_cog
from music_cog import music_cog
from chat_cog import ChatCog as chat_cog
from cache_cog import cache_cog

from dotenv import load_dotenv
load_dotenv()


# if "DISCORD_TOKEN" not in os.environ:
#     os.environ["DISCORD_TOKEN"] = getpass.getpass("Provide your Discord Token ---> ")
# 
# if "GROQ_API_KEY" not in os.environ:
#     os.environ["GROQ_API_KEY"] = getpass.getpass("Provide your Groq API Key ---> ")

DISCORD_TOKEN=os.environ["DISCORD_TOKEN"]
GROQ_API_KEY=os.environ["GROQ_API_KEY"]

SPOTIFY_CLIENT_ID=os.environ["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET=os.environ["SPOTIFY_CLIENT_SECRET"]

def main():
    bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
    bot.remove_command('help')
    loop = asyncio.get_event_loop()

    loop.run_until_complete(bot.add_cog(help_cog(bot)))
    loop.run_until_complete(bot.add_cog(cache_cog(bot, cache_dir='./cache', cache_size=100, cache_expiry=7*24*60*60)))
    loop.run_until_complete(bot.add_cog(music_cog(bot, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)))
    loop.run_until_complete(bot.add_cog(chat_cog(bot, GROQ_API_KEY)))

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()