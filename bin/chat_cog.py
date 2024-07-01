import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import logging
import subprocess


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {
            'format' : 'bestaudio/best',
            'postprocessors' : [{
                'key' : 'FFmpegExtractAudio',
                'preferredcodec' : 'mp3',
                'preferredquality' : '192',
            }],
            'outtmpl' : 'downloaded_audio.%(ext)s'
        }
        self.FFMPEG_OPTIONS = {
            'before_options' : '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options' : '-vn -nostdin'
        }
        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception as e:
                logging.error(f"Error occurred while extracting info from YouTube: {e}")
                return False
            
        audio_url = None
        for format in info['formats']:
            if format.get('acodec') and format['acodec'].lower() != 'none':
                audio_url = format['url']
                break
        
        if audio_url is None:
            logging.error("No audio format found for the given video")
            return False
        
        return {'source': audio_url, 'title': info['title']}
    
    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            self.music_queue.pop(0)

            try:
                
    
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()
                if self.vc is None:
                    await ctx.send("Error connecting to voice channel.")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            print(self.music_queue)
            self.music_queue.pop(0)

            try:
                process = subprocess.Popen(['ffmpeg', '-i', m_url, '-f', 'null', '-'], stderr=subprocess.PIPE)
                _, stderr = process.communicate()

                if process.returncode != 0:
                    logging.error(f"FFmpeg returned error code: {process.returncode}")
                    logging.debug(f"Stderr: {stderr.decode()}")
                else:
                    self.vc.play(discord.FFmpegPCMAudio(executable='ffmpeg', source=m_url), after=lambda e: self.play_next())
            except Exception as e:
                logging.error(f"Error occurred while playing the song: {e}")
                self.is_playing = False
        else:
            self.is_playing = False