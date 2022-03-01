import discord
from discord.ext import commands

class autoresponse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  
    

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.startswith('<@!873951998372900904>'):
            await message.channel.send('Hello!')

    @commands.Cog.listener()  #event for when a reaction is added 
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        if reaction.emoji == "1️⃣":
            message = reaction.message
            await reaction.remove(user)
            #get the first line of the embedded message
            embed = message.embeds[0]
            first_line = embed.description.split('\n')[0]
            print(first_line)
            await message.channel.send(first_line)