import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import logging
import asyncio


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloaded_audio.%(ext)s'
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -nostdin'
        }
        self.vc = None

    async def search_playlist_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(item, download=False)
            except Exception as e:
                logging.error(f'Error occurred while extracting info from YouTube: {e}')
                return []

        if 'entries' not in info:
            return []

        playlist = []
        for entry in info['entries']:
            try:
                print(entry['title'])
                audio_url = None
                for format in entry['formats']:
                    if format.get('acodec') and format['acodec'].lower() != 'none':
                        audio_url = format['url']
                        break
                if audio_url:
                    playlist.append({'source': audio_url, 'title': entry['title']})
            except Exception as e:
                logging.error(f"Error processing entry {entry.get('id', 'unknown')}: {e}")
        
        return playlist
    
    @commands.command(name='playlist', aliases=['pl'], help='Plays the playlist from yt')
    async def playlist(self, ctx, playlist_link):
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("You are not in a voice channel.")
            return
        await ctx.send("Searching 🔎")
        playlist = await self.search_playlist_yt(playlist_link)
        if not playlist:
            await ctx.send("Could not download the playlist. Incorrect format try another keyword.")
            return
        for video in playlist:
            self.music_queue.append([video, voice_channel])

        if not self.is_playing:
            await self.play_music(ctx)

    async def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
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

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()
                if self.vc is None:
                    await ctx.send("Error connecting to voice channel.")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())

            # Start downloading the rest of the playlist while playing
            asyncio.create_task(self.download_remaining_songs())

    async def download_remaining_songs(self):
        while self.is_playing and len(self.music_queue) > 0:
            song = self.music_queue[0][0]
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                try:
                    ydl.download([song['source']])
                except Exception as e:
                    logging.error(f"Error occurred while downloading the song: {e}")
            await asyncio.sleep(1)  # Adjust sleep time if needed

    @commands.command(name='play', aliases=['p', 'playing'], help='Plays the song from yt')
    async def play(self, ctx, *args):
        query = " ".join(args)
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("You are not in a voice channel!")

        elif self.is_paused:
            self.vc.resume()
        
        else:
            await ctx.send("Searching 🔎")
            
            song = await self.search_yt(query)

            if not song:
                await ctx.send("Could not download the song. Incorrect format try another keyword")
            else:
                await ctx.send(f"Added {song['title']} to the queue.")
                self.music_queue.append([song, voice_channel])
                if not self.is_playing:
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
        if self.vc is not None and self.vc.is_playing():
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Queue cleared.")

    @commands.command(name='leave', aliases=['l'], help="Leaves the voice channel")
    async def leave(self, ctx, *args):
        if self.vc is not None:
            await self.vc.disconnect()
            self.is_paused = False
            self.is_playing = False
            self.vc = None
        else:
            await ctx.send("I'm not in a voice channel!")
