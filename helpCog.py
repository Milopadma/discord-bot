import discord 
from discord.ext import commands

class helpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.help_message = """
```
$help                - displays this message
$hello               - says hello
$join (or {connect}) - joins the voice channel 
$play (or {p})       - plays a youtube video or stream
$playlist (or {ps})  - shows a list of saved playlist, and plays the selected playlist (not implemented)
$pause (or {pa})     - pauses the current song
$resume (or {r})     - resumes the current song
$skip (or {p})       - skips the current song
$queue (or {q})      - displays the current queue (not implemented)
&clearqueue (or {cq})- clears the current queue (not implemented)
$leave (or {d}, {dc})- leaves the voice channel
```
"""

        self.text_channel_text = []
    
    # @commands.Cog.listener()
    # async def on_ready(self):
    #     for guild in self.bot.guilds:
    #         for channel in guild.text_channels:
    #             self.text_channel_text.append(channel)

    #     await self.send_to_all(self.help_message)

    # async def send_to_all(self, msg):
    #     for text_channel in self.text_channel_text:
    #         await text_channel.send(msg)

    @commands.command(name="hlp", aliases=['help'], help="Displays this message")
    async def help(self, ctx):
        await ctx.send(self.help_message)

    