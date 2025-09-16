# Discord Bot

## Overview

Discord bot written in Python using `discord.py`. It provides features for text-to-speech using Eleven Labs, music playback from YouTube, and voice recognition. Users can interact with it using prefixed commands (`^`), interactive buttons and voice.

## Commands

	1.	^say <message>– Convert text to speech and play it in your voice channel (Eleven Labs).
	2.	^leave – Bot leaves the current voice channel.
	3.	^help – Show a help embed listing all commands.
	4.	^userinfo <nickname> – Show information about a user (ID, join date, roles, etc.).
	5.	^serverinfo – Show information about the server (ID, member count, roles, etc.).
	6.	^poll <question>– Create a poll with ✅ and ❌ reactions.
	7.	^meme – Fetch and display a random meme from Reddit.
	8.	^r <num1> <num2> – Make a random number between num1 and num2.
	9.	^define <word> – Look up a dictionary definition.
	10. ^m <title>– Play music from YouTube.
	11. ^join – Join your voice channel and start listening for spoken commands

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
