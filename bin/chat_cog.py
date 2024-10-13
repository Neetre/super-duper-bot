import json
import asyncio
from typing import List, Dict, Any

import discord
from discord.ext import commands
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

class ChatCog(commands.Cog):
    def __init__(self, bot: commands.Bot, groq_api_key: str):
        self.bot = bot
        self.chat = ChatGroq(temperature=0.7, groq_api_key=groq_api_key, model_name="llama-3.1-70b-versatile")
        self.data: List[Dict[str, str]] = self.load_data()
        self.conversation_length = 5  # Number of previous messages to include in context

    @commands.command(name='chat', aliases=['c'], help='Chat with the bot')
    async def chat(self, ctx: commands.Context, *, message: str):
        if not message:
            await ctx.send("Please provide a message to chat with the bot.")
            return

        async with ctx.typing():
            context = self.get_conversation_context()
            full_message = "\n".join(context + [message])

            system = "You are a helpful assistant in a Discord server. Be concise, friendly, and engaging."
            human = "{text}"
            prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

            chain = prompt | self.chat
            response = await asyncio.to_thread(chain.invoke, {"text": full_message})
            text_response = response.content

        new_data = {"input": message, "output": text_response}
        self.data.append(new_data)
        self.save_data()

        await ctx.send(text_response)

    @commands.command(name="cclear", help="Clears the chat history")
    async def clear(self, ctx: commands.Context):
        self.data = []
        self.save_data()
        await ctx.send("Chat history cleared.")

    @commands.command(name="chistory", help="Shows the recent chat history")
    async def history(self, ctx: commands.Context, limit: int = 5):
        limit = min(limit, len(self.data))
        history = self.data[-limit:]
        
        embed = discord.Embed(title="Recent Chat History", color=discord.Color.blue())
        for i, entry in enumerate(history, 1):
            embed.add_field(name=f"Message {i}", value=f"User: {entry['input']}\nBot: {entry['output']}", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name="csetcontext", help="Set the number of previous messages to include in chat context")
    async def set_context(self, ctx: commands.Context, length: int):
        if length < 1 or length > 10:
            await ctx.send("Please choose a context length between 1 and 10.")
            return
        
        self.conversation_length = length
        await ctx.send(f"Conversation context length set to {length} messages.")

    def get_conversation_context(self) -> List[str]:
        context = []
        for entry in self.data[-self.conversation_length:]:
            context.extend([f"User: {entry['input']}", f"Assistant: {entry['output']}"])
        return context

    def load_data(self) -> List[Dict[str, str]]:
        try:
            with open('../data/data.json', 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_data(self) -> None:
        with open('../data/data.json', 'w') as f:
            json.dump(self.data, f)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} has connected to Discord!')
