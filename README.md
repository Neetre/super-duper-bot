# super-duper-bot

## Description

This is a bot that offers a variety of features, such as:

- Music player;
- Chatbot, implemented with a real AI;

It is built using the [Discord API](https://discord.com/developers/docs/intro) and the [Groq API](https://groq.com).

Coming soon:

- Playlist management;

### Note

dotenv might be added in the future to store the API keys.

## Requirements

python >= 3.9

**Setting Up the Environment**

* Windows: `./setup_Windows.bat`
* Linux/macOS: `./setup_Linux.sh`

These scripts will install required dependencies, and build a virtual environment for you if you don't have one.

For the Discord API:

1. Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications)

2. Copy the bot token

3. Invite the bot to your server

For the Groq API:

1. Create an account on the [Groq API](https://groq.com)

2. Copy the API key

3. Run the program

## Running the Program

### CLI

1. Navigate to the `bin` directory: `cd bin`

2. Execute `python main.py` (use `python3` on Linux/macOS) in your terminal

3. Input your bot token and the Groq API key.

Here is the working example for the music player:
![music](/data/readme/music.png)

Here is the working example for the chatbot:
![chatbot](/data/readme/chatbot.png)


## Author

Neetre 2024
