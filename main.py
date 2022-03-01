#discord bot
import os
from xmlrpc import server
import discord
import random
from dotenv import load_dotenv
from discord.ext import commands
from autoResponse import autoresponse

from helpCog import helpCog
# from musicCog import music_cog
import musicCog2

#initialize bot
bot = commands.Bot(command_prefix='$')

#load .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot.remove_command("help")

bot.add_cog(helpCog(bot))
# bot.add_cog(music_cog(bot))
bot.add_cog(musicCog2.music(bot))
bot.add_cog(autoresponse(bot))


@bot.event
async def on_ready():
    print('\nLogged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

#bot commands
@bot.command(pass_context=True)
async def hello(ctx):
    await ctx.trigger_typing()
    await ctx.send("Hello!")

# #bot commands - join author voice call
# @bot.command(pass_context=True)
# async def join(ctx):
#     await ctx.message.author.voice.channel.connect() #connects to channel

# #bot commands - leave author voice call
# @bot.command(pass_context=True)
# async def leave(ctx):
#         #check if bot is in channel first
#         if ctx.guild.voice_client is not None:
#             await ctx.guild.voice_client.disconnect()
#         else:
#             await ctx.channel.send("I'm not in a voice channel")



#client run using token from TOKEN.env file
bot.run(TOKEN)


















# inspirations = [
#     "**_If you masturbate, you're technically gay._**",
#     "**_She in a relationship with you, you single._**",
#     "**_Trees are here to replenish the oxygen you waste._**",
#     "**_there are no such thing as a free black man, they are all escapees._**",
#     "**_Only way you're tripping over a bitch is if she's sleeping on the floor._**",
#     "**_Don't put me on your stories if your cry. I'm tryna see tiddies not tears._**",
#     "**_skate fast, eat ass_**",
# ]

# @client.event
# async def on_message(message):
#     #this is the message that the bot will respond to
#     if message.author == client.user:
#         return

#     #this is for $hello commmand
#     if message.content.startswith("$hello"):
#         await message.channel.send("Hello!")

#     #this is for $help command
#     if message.content.startswith("$help"):
#         await message.channel.send(
#             "1. this shit does nothing \n2. do $inspireme to be inspired "
#         )

#     #sends a random inspirational quote from inspriations list
#     if message.content.startswith("$inspireme"):
#         await message.channel.send(random.choice(inspirations))

#     #checks for $join text and joins the voice channel that the sender is in
#     if message.content.startswith("$join"):
#         channel = message.author.voice.channel
#         await channel.connect()

#     #checks for $leave text and leaves the voice channel that the sender is in
#     if message.content.startswith("$leave"):
#         #check if bot is in channel first
#         if message.guild.voice_client is not None:
#             await message.guild.voice_client.disconnect()
#         else:
#             await message.channel.send("I'm not in a voice channel")

    # #check for $play and url and use the youtube function to pass the url parameter
    # if message.content.startswith("$play"):
    #     #check if bot is in channel first
    #     if message.guild.voice_client is not None:
    #         #check if bot is in a voice channel
    #         if message.author.voice.channel is not None:
    #             #get the url
    #             url = message.content[6:]
    #             #use the youtube function to pass the url parameter
    #             await youtube(url)
    #         else:
    #             await message.channel.send("You need to be in a voice channel to play music")
    #     else:
    #         await message.channel.send("I'm not in a voice channel")

