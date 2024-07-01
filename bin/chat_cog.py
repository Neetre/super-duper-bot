import getpass
import os
import pathlib
import textwrap

import discord
from discord.ext import commands
import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API Key")

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

GOOGLE_API_KEY=os.environ["GOOGLE_API_KEY"]

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')


response = model.generate_content("What is the meaning of life?")
to_markdown(response.text)