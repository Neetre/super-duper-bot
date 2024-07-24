'''
This file contains the chat_cog class which is a discord cog that allows the bot to chat with users.

Neetre 2024
'''
import json

from discord.ext import commands

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


class chat_cog(commands.Cog):
    def __init__(self, bot, GROQ_API_KEY):
        self.bot = bot
        self.chat = ChatGroq(temperature=1, groq_api_key=GROQ_API_KEY, model_name="llama-3.1-70b-versatile")
        self.data = self.load_data()

    @commands.command(name='chat', aliases=['c'], help='Chat with the bot')
    async def chat(self, ctx, *message):
        print(message)
        message = " ".join(message)
        print(message)
        if message is None and len(message) == 0:
            await ctx.send("Please provide a message to chat with the bot.")
            return

        message = message.strip()
        if self.data is not None:
            message = self.data[-1]["output"] + " " + message if len(self.data) > 0 else message # Append the last response to the message if it exists

        system = "You are a helpful assistant."
        human = "{text}"
        prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

        chain = prompt | self.chat
        response = chain.invoke({"text": message})
        text_response = response.content
        new_data = {"input":message, "output":text_response}
        self.data.append(new_data)
        self.save_data()
        
        await ctx.send(text_response)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} has connected to Discord!')

    @commands.command(name="cclear", help="Clears the chat history")
    async def clear(self, ctx):
        self.data = []
        await ctx.send("Chat history cleared.")

    def load_data(self):
        try:
            with open('../data/data.json', 'r') as f:
                data = json.load(f)
                # Ensure self.data is a list if the file is empty or data is None
                return data if data is not None else []
        except FileNotFoundError:
            return []

    def save_data(self):
        with open('../data/data.json', 'w') as f:
            json.dump(self.data, f)
