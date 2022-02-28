import discord 
from discord.ext import commands

class helpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.help_message = """
```
$hlp - displays this message
$hello - says hello
$join - joins the voice channel 
$play - plays a youtube video
$pause - pauses the current song
$resume - resumes the current song
$skip - skips the current song
$queue - displays the current queue
&clearqueue - clears the current queue
$leave - leaves the voice channel
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

    @commands.command(name="hlp", aliases=['he'], help="Displays this message")
    async def help(self, ctx):
        await ctx.send(self.help_message)