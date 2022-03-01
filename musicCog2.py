import discord
from discord.ext import commands
import random
import asyncio
import sys
import traceback
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL
import itertools

from testing import YTDLSource


ytdl_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}


ytdl = YoutubeDL(ytdl_options)

#part of error handling
class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""

class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""
##


#create class for ytdlsource, this is to implement YTDL functionality to the bot itself
class ytdlSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester #requester refers to author

        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.duration = data.get('duration')


    def __getitem__(self, item: str): #overrides the getitem method
        return self.__getattribute__(item) #returns the item from the class

    #create source function, inside an event loop, this returns the link into readable format for the bot
    @classmethod 
    async def create_source (cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop() #create an event loop in case none is provided

        toRun = partial(ytdl.extract_info, url=search, download=download) #create a partial function to run the ytdl function with the url and download option
        data = await loop.run_in_executor(None, toRun) #run the partial function in the event loop

        if 'entries' in data:
            data = data['entries'][0] #if the data is a playlist, get the first entry 

        if download: 
            source = ytdl.prepare_filename(data) #if the download option is true, prepare the filename
        else:
            return {'webpage_url': data('webpage_url'), 'requester': ctx.author, 'title': data('title')} #if the download option is false, return the data

        return cls(discord.FFmpegPCMAudio(source, **ffmpeg_options), data=data, requester=ctx.author) #return the source


    @classmethod
    async def regatherStream(cls, data, *, loop): #regather the stream
        loop = loop or asyncio.get_event_loop() #create an event loop in case none is provided

        requester = data['requester'] #get the requester
        toRun = partial(ytdl.extract_info, url=data['webpage_url'], download=False) #create a partial function to run the ytdl function with the url and download option
        data = await loop.run_in_executor(None, toRun) #run the partial function in the event loop

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester) #return the source


#class for the musicPlayer (the part that plays the music)
class musicPlayer:
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'volume', 'next', 'current', 'queue', 'repeat', 'shuffle')
     #create a list of attributes to expect object instance to have for faster access

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild #_variables is to not throw an error if the variable is not used later in code
        self._channel = ctx.channel
        self._cog = ctx.cog
        self.queue = asyncio.Queue()
        self.next = asyncio.Event() 
        self.volume = 0.5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop()) #create a task to run the player loop

    async def player_loop(self):
        await self.bot.wait_until_ready() #wait until the bot is ready
        while not self.bot.is_closed(): #while the bot is not closed
            self.next.clear() #clear the next event

            try: #try to get the next song
                async with timeout(300): #set a timeout of 300 seconds
                    source = await self.queue.get() #get the next song
            except asyncio.TimeoutError: #if the timeout is reached
                return self.destroy(self._guild) #destroy the player

            if not isinstance(source, YTDLSource): #if the source is not a YTDLSource
                try: #try to regather the stream
                    source = await ytdlSource.regatherStream(source, loop=self.bot.loop) #regather the stream
                except Exception as e: #if there is an error
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```') #send the error
                    continue #continue the loop
            
            source.volume = self.volume #set the volume
            self.current = source #set the current song to the source

            #play the source and set the next event
            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            await self.next.wait() #wait for the next event to be set

            source.cleanup() #call cleanup func to cleanup the source
            self.current = None #set the current song to none
        
    def destroy(self, guild): #calls the cleanup func to cleanup the player and the dc
        return self.bot.loop.create_task(self._cog.cleanup(guild)) #create a task to clean up the player



#######################################################################################################################
#the actual music cog class that gets imported to main.py (the part that controls the whole thing, making calls to the other classes)
class music(commands.Cog):

    __slots__ = ('bot', 'players') #create a list of attributes to expect object instance to have, for faster access

    def __init__(self, bot):
        self.bot = bot #set the bot
        self.players = {} #create a dictionary of players

    #this is to disconnect the player and delete the player from dict
    async def cleanup(self, guild): #clean up the player
        try:
            await guild.voice_client.disconnect() #disconnect the voice client
        except AttributeError:
            pass #if there is no voice client, do nothing
    
        try:
            del self.players[guild.id] #delete the player from the dictionary
        except KeyError:
            pass #if there is no player, do nothing

    #this is to check if the bot was run in a guild/server, not in private messages
    async def __local_check(self, ctx): #check if the user is in a voice channel
        if not ctx.guild: #if the context is not a guild
            raise commands.NoPrivateMessage #raise an error
        return True #return true


    #error handler
    async def __error(self, ctx, error): #error handler
        if isinstance(error, commands.NoPrivateMessage):
            try: 
                return await ctx.send('This command can not be used in private messages.') #send a message
            except discord.HTTPException:
                pass #if there is an error, do nothing
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to voice channel. Please make sure you are in a voice channel.') #send a message
        
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr) #print the error')
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr) #print the error


    #function to get the musicPlayer instance for the guild/server, as each guild/server has it's own musicPlayer instance
    def get_player(self, ctx): #get the player
        try: #try to get the player
            player = self.players[ctx.guild.id] #get the player
        except KeyError:
            player = musicPlayer(ctx) #create a new player by creating an instance of musicPlayer class
            self.players[ctx.guild.id] = player #add the player to the dictionary
        return player #return the player



    ##################################################################################################################
    #bot commands - connect to a voice channel
    @commands.command(name='connect', aliases=['join'], description="connects to a voice channel") #connect to the voice channel
    async def connect(self, ctx, *, channel: discord.VoiceChannel=None):
        if not channel:
            try:
                channel = ctx.author.voice.channel #try to get the voice channel
            except AttributeError:
                ctx.send('Please join a voice channel.') #send a message
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.') #raise an error

        vc = ctx.voice_client #get the voice client
        if vc: #if there is a voice client
            if vc.channel.id == channel.id: #if the voice client is in the same channel
                ctx.send(f'I am already in this <{channel}> channel.') #send a message
                return
            try:
                await vc.move_to(channel) #move the voice client to the channel
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.') #raise an error
        else: #if there is no voice client
            try:
                await channel.connect() #connect to the channel
            except asyncio.TimeoutError: #if the connection timed out
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.') #raise an error
        if (random.randint(0, 1) == 0): #if the random number is 0
            await ctx.send(f'Connected to: **{channel}**') #send a message

    #bot commands - play a song or stream
    @commands.command(name='play', aliases=['p'], description="plays a song") #play a song
    async def play(self, ctx, *, search: str): #bot tries to join a voice channel if its not in one, this function 
    #takes the parameter string to search for songs using YTDL
        await ctx.trigger_typing() #trigger typing

        vc = ctx.voice_client #get the voice client
        if not vc: #if there is no voice client
            await ctx.invoke(self.connect) #invoke the connect command
        player = self.get_player(ctx) #get the player
        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False) #create a source from the search
        await player.queue.put(source) #add the source to the queue

    #bot commands - pause the song
    @commands.command(name='pause', aliases=['pa'], description="pauses the song") #pause the song
    async def pause(self, ctx):
        vc = ctx.voice_client #get the voice client
        if not vc or not vc.is_playing(): #if there is no voice client or the voice client is not playing
            return await ctx.send('Nothing playing.') #send a message
        else:   
            vc.pause()
            return await ctx.send('Paused')
            

    #bot commands - resume the song
    @commands.command(name='resume', aliases=['r'], description="resumes the song") #resume the song
    async def resume(self, ctx):
        vc = ctx.voice_client #get the voice client
        # if not ctx.voice_client or not ctx.voice_client.is_playing(): #if there is no voice client or the voice client is not playing
        if not vc or not vc.is_paused(): #if there is no voice client or the voice client is not playing
            return await ctx.send('Nothing playing.') #send a message
        else:
            vc.resume()
            return await ctx.send('Resumed')

    #bot commands - skip the song
    @commands.command(name='skip', aliases=['s'], description="skips the song") #skip the song
    async def skip(self, ctx):
        vc = ctx.voice_client #get the voice client
        if not vc or not vc.is_connected(): #check if there is a voice client or the voice client is not connected
            return await ctx.send('Not connected.') #send a message
        if vc.is_paused():
            pass
        elif not vc.is_playing(): #if there is a voice client and the voice client is playing
            return 
        await ctx.send('Skipped')
        vc.stop() #stop the voice client, but the event loop will bring it to the next song in queue dict

    #bot commands - leave the voice channel
    @commands.command(name='disconnect', aliases=['d', 'dc', 'leave'], description="disconnects from the voice channel") #disconnect from the voice channel
    async def disconnect(self, ctx):
        vc = ctx.voice_client #get the voice client
        if not vc or not vc.is_connected(): #if there is no voice client or its not connected to any voice channel
            return await ctx.send('Not connected.') #send a message
        else:
            await ctx.send('Disconnecting...')
        
        await self.cleanup(ctx.guild) #cleanup the voice client player in the guild/server
            
    #bot commands - view the queue
    @commands.command(name='queue', aliases=['q'], description="view the queue") #view the queue
    async def queue(self, ctx):
        vc = ctx.voice_client  #get the voice client
        if not vc or not vc.is_connected(): #if there is no voice client or the voice client is not connected
            return await ctx.send('Not connected.') #send a message
        else:
            player = self.get_player(ctx)
            if player.queue.empty():
                return await ctx.send('Empty queue.')
            else:
                queue = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue)))) #get the items in the queue
                inQueue = '\n'.join(f"`{(queue.index(_)) + 1}.` [{_['title']}] ({_['webpage_url']}) |` Requested by {_['requester']}`\n" for _ in queue) #get the queue
                inQueue = f"\nNow playing:\n[{vc.source.title}]({vc.source.url}) | 'Requested by {vc.source.requester}'\n\n Up next:\n" + inQueue + f"\n**{len(queue)} songs in queue**"
                embed =  discord.Embed(title=f'Queue for {ctx.guild.name}', description=inQueue, color=discord.Color.green())
                embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)

                await ctx.send(embed=embed)