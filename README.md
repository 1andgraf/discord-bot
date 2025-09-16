# Discord Bot

## Overview

Discord bot written in Python using `discord.py`. It provides features for text-to-speech using Eleven Labs, music playback from YouTube, and voice channel management. Users can interact with it using prefixed commands (`^`) and interactive buttons.

## Commands

- `^say <message>`: Converts text to speech via Eleven Labs and plays it in your voice channel.
- `^join`: Bot joins your current voice channel.
- `^leave`: Bot leaves the voice channel.
- `^m <song name>`: Plays music from YouTube. If some song is already playing, new one is added to the queue.
- `^help`: Sends an embedded message listing all commands and controls.
- `^serverinfo`: Gives info about server
- `^poll <question>`: Creates a poll with reactions
- `^meme`: Sends a random meme
- `^r <num1> <num2>`: Gives a random number from num1 to num2
- `^define <word>`: Gives a word definition from dictionary

## Setup

1. Clone the repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with the following:
   ```env
   BOT_TOKEN=your_discord_bot_token
   ELEVEN_LABS_API_KEY=your_eleven_labs_api_key
   TTS_VOICE_ID=your_voice_id
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Notes

- Make sure the bot has **privileged intents** enabled in the Discord developer portal (members, message content, and voice states).
- Ensure `ffmpeg` and `opus` libraries are installed for voice playback.
