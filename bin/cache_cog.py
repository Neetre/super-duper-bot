import discord
from discord.ext import commands
import yt_dlp
import os
import json
from collections import OrderedDict
import time

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return None
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class cache_cog(commands.Cog):
    def __init__(self, bot, cache_dir='./cache', cache_size=100, cache_expiry=7*24*60*60):
        self.bot = bot
        self.cache_dir = cache_dir
        self.cache_size = cache_size
        self.cache_expiry = cache_expiry  # Cache expiry time in seconds (default: 7 days)
        self.cache = LRUCache(cache_size)
        self.search_history = {}
        self.ensure_cache_dir()
        self.load_cache()

    def ensure_cache_dir(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def load_cache(self):
        cache_file = os.path.join(self.cache_dir, 'cache.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                for key, value in cache_data.items():
                    if time.time() - value['timestamp'] <= self.cache_expiry:
                        self.cache.put(key, value)

    def save_cache(self):
        cache_file = os.path.join(self.cache_dir, 'cache.json')
        with open(cache_file, 'w') as f:
            json.dump(self.cache.cache, f)

    async def add_to_cache(self, query, song_info):
        cache_key = query.lower()
        audio_file = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        
        # Download the audio file
        await self.download_audio(song_info['source'], audio_file)
        
        cache_value = {
            'title': song_info['title'],
            'file_path': audio_file,
            'timestamp': time.time()
        }
        self.cache.put(cache_key, cache_value)
        self.save_cache()

    async def get_from_cache(self, query):
        cache_key = query.lower()
        cache_hit = self.cache.get(cache_key)
        if cache_hit:
            if time.time() - cache_hit['timestamp'] <= self.cache_expiry:
                return cache_hit
            else:
                # Remove expired cache entry
                self.cache.cache.pop(cache_key, None)
                if os.path.exists(cache_hit['file_path']):
                    os.remove(cache_hit['file_path'])
        return None

    async def download_audio(self, url, file_path):
        # Implement the audio download logic here
        # You can use yt_dlp or another library to download the audio
        # For example:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': file_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel:
            guild_id = after.channel.guild.id
            if guild_id not in self.search_history:
                self.search_history[guild_id] = []
            # You can implement logic here to update search history based on voice channel activity

    @commands.command(name='cache_stats', help='Shows cache statistics')
    async def cache_stats(self, ctx):
        total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in os.listdir(self.cache_dir) if f.endswith('.mp3'))
        embed = discord.Embed(title="Cache Statistics", color=discord.Color.blue())
        embed.add_field(name="Cached Items", value=str(len(self.cache.cache)), inline=False)
        embed.add_field(name="Total Cache Size", value=f"{total_size / (1024*1024):.2f} MB", inline=False)
        embed.add_field(name="Cache Capacity", value=str(self.cache_size), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='clear_cache', help='Clears the entire cache')
    @commands.has_permissions(administrator=True)
    async def clear_cache(self, ctx):
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.mp3'):
                os.remove(os.path.join(self.cache_dir, filename))
        self.cache = LRUCache(self.cache_size)
        self.save_cache()
        await ctx.send("Cache cleared successfully.")

    def cog_unload(self):
        self.save_cache()

# Don't forget to add this cog to your bot setup
# bot.add_cog(cache_cog(bot, cache_dir='./cache', cache_size=100, cache_expiry=7*24*60*60))
