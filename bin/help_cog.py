import discord
from discord.ext import commands


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_msg = """
```
For music:
!play <url> - Play a song from youtube
!pause - Pause the song
!resume - Resume the song
!skip - Skip the song
!queue - Show the queue
!clear - Clear the queue
!leave - Leave the voice channel

For chatbot:
!chat
!quit
```
"""
        self.text_channel_name = 'your-channel-name'

    async def send_to_all(self, msg):
        for channel in self.text_channel_text:
            await channel.send(msg)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name.lower() == self.text_channel_name.lower():
                    try:
                        await channel.send(self.help_msg)
                    except discord.Forbidden:
                        print(f"Bot doesn't have permission to send messages in {channel.name} of {guild.name}.")

    @commands.command(name='help', help='Shows this message')
    async def help_command(self, ctx, *args):
        await ctx.send(self.help_msg)
