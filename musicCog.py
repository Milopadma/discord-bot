
import discord
from discord.ext import commands
from youtube_dl import YoutubeDL


class music_cog(commands.Cog):
    def __init__(self, commands):
        self.commands = commands

        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.VDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

        self.vc = None

    #commands commands - search youtube video
    def searchyt(self, item):
        with YoutubeDL(self.VDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False
        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def playnext(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']
            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.playnext())
        else:
            self.is_playing = False

    async def playmusic(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']

            if self.vc == None or not self.vc.is_connected():
                self.vc = await ctx.author.voice.channel.connect()

                if self.vc == None:
                    await ctx.send('Could not connect to voice channel!')
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.music_queue.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.playnext())

        else:
            self.is_playing = False

    #commands commands - play function
    @commands.command(name="play", aliases=['p'], help="Plays the selected song from YT") 
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Connect to a voice channel!!")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.searchyt(query)
            if type(song) == type(True):
                await ctx.send("Unable to download song, try a different keyword!")
            else:
                await ctx.send("Song added to queue!")
                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.playmusic(ctx)            
    
    #commands commands - pause function
    @commands.command(name="pause", aliases=['pl'], help="Pauses the current song")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    #commands commands - resume function
    @commands.command(name="resume", aliases=['r'], help="Resumes the current song")
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    #commands commands - skip function
    @commands.command(name="skip", aliases=['s'], help="Skips the current song")
    async def skip(self, ctx, *args):
        if self.vc != None and self.vc:
            self.vc.stop()
            await self.playmusic(ctx)

    #commands commands - queue function
    @commands.command(name="queue", aliases=['q'], help="Shows the current queue")
    async def queue(self, ctx):
        retval = ""

        for i in range(0, len(self.music_queue)):
            if i > 4: break
            retval += self.music_queue[i][0]['title'] + "\n"

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("Queue is empty!")

    #commands commands - clear queue function
    @commands.command(name="clearqueue", aliases=['cq'], help="Clears the current queue")
    async def clearqueue(self, ctx, *args):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Queue cleared!")

    #commands commands - leave function
    @commands.command(name="leave", aliases=['l'], help="Leaves the current voice channel")
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()

