import argparse
from icecream import ic

import discord
from discord.ext import commands
import asyncio

from help_cog import help_cog
from music_cog import music_cog
from chat_cog import chat_cog


def args_parsing():
    argparse.ArgumentParser(description='Discord bot')
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, help='Discord bot token')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
    args = parser.parse_args()
    return args


def main():
    args = args_parsing()

    if args.verbose:
        ic.enable()
    else:
        ic.disable()

    bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
    bot.remove_command('help')
    loop = asyncio.get_event_loop()

    loop.run_until_complete(bot.add_cog(help_cog(bot)))
    loop.run_until_complete(bot.add_cog(music_cog(bot)))
    loop.run_until_complete(bot.add_cog(chat_cog(bot)))

    bot.run(args.token)


if __name__ == "__main__":
    main()