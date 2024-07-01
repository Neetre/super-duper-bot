import os

import discord
from discord.ext import commands

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


class chat_cog(commands.Cog):
    def __init__(self, bot, GROQ_API_KEY):
        self.bot = bot
        self.chat = ChatGroq(temperature=0, groq_api_key=GROQ_API_KEY, model_name="mixtral-8x7b-32768")

    @commands.command(name='chat', aliases=['c'], help='Chat with the bot')
    async def chat(self, ctx, *, message):
        human = "{text}"
        prompt = ChatPromptTemplate.from_messages([("human", human)])

        chain = prompt | self.chat
        response = chain.invoke({"text": message})
        text_response = response.content
        await ctx.send(text_response)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} has connected to Discord!')
