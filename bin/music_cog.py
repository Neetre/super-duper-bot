import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import logging
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import concurrent.futures


class music_cog(commands.Cog):
    def __init__(self, bot, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET):
        self.bot = bot
        self.is_playing = False
        self.is_paused = False

        self.music_queue = asyncio.Queue()
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
        
        # Initialize Spotify client
        client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        # Create a ThreadPoolExecutor for background tasks
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        
        self.song_list = []
        
    async def search_spotify(self, query):
        try:
            if 'open.spotify.com/track/' in query:
                track_id = query.split('/')[-1].split('?')[0]
                track = self.sp.track(track_id)
                search_query = f"{track['name']} {track['artists'][0]['name']}"
            elif 'open.spotify.com/playlist/' in query:
                playlist_id = query.split('/')[-1].split('?')[0]
                playlist = self.sp.playlist(playlist_id)
                tracks = []
                for item in playlist['tracks']['items']:
                    track = item['track']
                    tracks.append(f"{track['name']} {track['artists'][0]['name']}")
                return tracks
            else:
                search_query = query

            return await self.search_yt(search_query)
        except Exception as e:
            logging.error(f"Error occurred while searching Spotify: {e}")
            return False

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

    def search_yt(self, item):
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
            self.music_queue.get()

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self):
        while True:
            if self.vc is None or not self.vc.is_connected():
                self.is_playing = False
                break

            if self.is_paused:
                await asyncio.sleep(2)
                continue

            if self.music_queue.empty():
                self.is_playing = False
                await asyncio.sleep(2)
                continue

            self.is_playing = True

            song, voice_channel = await self.music_queue.get()
            self.song_list.pop(0)  # Remove the song from our tracking list

            if self.vc.channel != voice_channel:
                await self.vc.move_to(voice_channel)

            # Use run_in_executor to run FFmpeg in a separate thread
            loop = asyncio.get_event_loop()
            audio_source = await loop.run_in_executor(
                self.thread_pool,
                lambda: discord.FFmpegPCMAudio(song['source'], **self.FFMPEG_OPTIONS)
            )

            self.vc.play(audio_source, after=lambda e: print('Player error: %s' % e) if e else None)

            await self.bot.change_presence(activity=discord.Game(name=song['title']))
            await asyncio.sleep(0.5)

    async def download_remaining_songs(self):
        while self.is_playing and len(self.music_queue) > 0:
            song = self.music_queue[0][0]
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                try:
                    ydl.download([song['source']])
                except Exception as e:
                    logging.error(f"Error occurred while downloading the song: {e}")
            await asyncio.sleep(1)  # Adjust sleep time if needed

    @commands.command(name='play', aliases=['p', 'playing'], help='Plays a song from YouTube or Spotify')
    async def play(self, ctx, *args):
        query = " ".join(args)
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("You are not in a voice channel!")
            return

        if self.is_paused:
            self.vc.resume()
        else:
            await ctx.send("Searching 🔎")
            
            if 'open.spotify.com' in query:
                result = await self.search_spotify(query)
                if isinstance(result, list):  # It's a playlist
                    for track in result:
                        song = await self.bot.loop.run_in_executor(self.thread_pool, self.search_yt, track)
                        if song:
                            await self.music_queue.put([song, voice_channel])
                            self.song_list.append(song['title'])  # Add to our tracking list
                    await ctx.send(f"Added {len(result)} songs from Spotify playlist to the queue.")
                else:
                    song = result
            else:
                song = await self.bot.loop.run_in_executor(self.thread_pool, self.search_yt, query)

            if not song:
                await ctx.send("Could not download the song. Incorrect format try another keyword")
            else:
                await ctx.send(f"Added {song['title']} to the queue.")
                await self.music_queue.put([song, voice_channel])
                self.song_list.append(song['title'])  # Add to our tracking list
                
            if not self.is_playing:
                self.is_playing = True
                self.bot.loop.create_task(self.play_music())

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
    async def queue(self, ctx):
        if not self.song_list:
            await ctx.send("No music in queue.")
            return

        queue_embed = discord.Embed(title="Music Queue", color=discord.Color.blue())
        for i, song_title in enumerate(self.song_list, start=1):
            queue_embed.add_field(name=f"{i}.", value=song_title, inline=False)

        await ctx.send(embed=queue_embed)

    @commands.command(name='clear', help='Clears the queue')
    async def clear(self, ctx):
        if self.vc is not None and self.vc.is_playing():
            self.vc.stop()
        
        # Clear the asyncio.Queue
        while not self.music_queue.empty():
            await self.music_queue.get()
        
        # Clear our tracking list
        self.song_list.clear()
        
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
