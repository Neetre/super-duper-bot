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

    def search_playlist_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(item, download=False)
            except Exception as e:
                logging.error(f'Error occurred while extracting info from YouTube: {e}')
                return False
        
        playlist = []
        for entry in info['entries']:
            print(entry['title'])
            audio_url = None
            for format in entry['formats']:
                if format.get('acodec') and format['acodec'].lower() != 'none':
                    audio_url = format['url']
                    break
            if audio_url:
                playlist.append({'source': audio_url, 'title': entry['title']})
        return playlist
    
    @commands.command(name='playlist', aliases=['pl'], help='Plays the playlist from yt')
    async def playlist(self, ctx, playlist_link):
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("You are not in a voice channel.")
            return
        await ctx.send("Searching 🔎")
        playlist = self.search_playlist_yt(playlist_link)
        if not playlist:
            await ctx.send("Could not download the playlist. Incorrect format try another keyword.")
            return
        for video in playlist:
            self.music_queue.append([video, voice_channel])

        if self.is_playing == False:
            await self.play_music(ctx)

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

    @commands.command(name='play', aliases=['p', 'playing'], help='Plays the song from yt')
    async def play(self, ctx, source, *args):
        query = " ".join(args)
        voice_channel  = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("You are nont in a voice channel!")

        elif self.is_paused:
            self.vc.resume()
        
        else:
            await ctx.send("Searching 🔎")
            
            song = self.search_yt(query)

            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword")
            else:
                await ctx.send(f"Added {song['title']} to the queue.")
                self.music_queue.append([song, voice_channel])
                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name='pause', help='Pauses the song')
    async def pause(self, ctx, *args):
        if self.vc and self.vc.is_playing():
            self.is_playing = False
            self.vc.pause()
            self.is_paused = True
            await ctx.send("Paused ⏸️")
        elif self.is_paused:
            self.vc.resume()
    
    @commands.command(name='resume', help='Resumes the song')
    async def resume(self, ctx , *args):
        if self.vc and self.vc.is_paused():
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
            await ctx.send("Resumed ▶️")

    @commands.command(name='stop', help='Stops the song')
    async def stop(self, ctx, *args):
        if self.vc and self.vc.is_playing():
            self.is_playing = False
            self.vc.stop()
            self.is_paused = False
            await ctx.send("Stopped ⏹️")

    @commands.command(name='skip', help='Skips the song')
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await self.play_next()

    @commands.command(name='queue', aliases=['q'], help='Shows the queue')
    async def queue(self, ctx, *args):
        retval= ''

        for i in range(0, len(self.music_queue)):
            retval += f"{i+1}. {self.music_queue[i][0]['title']}\n"

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue.")

    @commands.command(name='clear', hepl='Clears the queue')
    async def clear(self, ctx, *args):
        if self.vc != None and self.vc.is_playing():
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Queue cleared.")

    @commands.command(name='leave', aliases=['l'], help="Leaves the voice channel")
    async def leave(self, ctx, *args):
        if self.vc != None:
            await self.vc.disconnect()
            self.is_paused = False
            self.is_playing = False
            self.vc = None
        else:
            await ctx.send("I'm not in a voice channel!")
