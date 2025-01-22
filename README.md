# Discord Music Bot

A feature-rich Discord music bot built with discord.py that allows you to play music from YouTube in your Discord server. The bot includes features like queue management, volume control, and basic playback controls.

## Features

- Play music from YouTube URLs or search terms
- Queue system for managing multiple songs
- Basic playback controls (play, pause, resume, skip)
- Volume control
- Auto-disconnect after inactivity
- Rich embed messages for better visual feedback
- Support for high-quality audio streaming

## Prerequisites

Before running the bot, you'll need to install several dependencies. Here's how to set them up on different operating systems:

### Windows

1. Install Python 3.8 or higher:
   - Download the latest Python version from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"

2. Install FFmpeg:
   - Download FFmpeg from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
   - Download the "ffmpeg-git-full.7z" package
   - Extract the archive and rename the folder to "ffmpeg"
   - Move the folder to `C:\`
   - Add `C:\ffmpeg\bin` to your system's PATH:
     - Open System Properties > Advanced > Environment Variables
     - Under System Variables, find and select "Path"
     - Click "Edit" and add `C:\ffmpeg\bin`
     - Click "OK" to save

### macOS

1. Install Python 3.8 or higher:
   ```bash
   brew install python
   ```

2. Install FFmpeg:
   ```bash
   brew install ffmpeg
   ```

### Linux (Ubuntu/Debian)

1. Install Python 3.8 or higher:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. Install FFmpeg and additional dependencies:
   ```bash
   sudo apt update
   sudo apt install ffmpeg python3-dev libffi-dev libnacl-dev
   ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/discord-music-bot.git
   cd discord-music-bot
   ```

2. Create a virtual environment (recommended):
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a Discord Bot:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and give it a name
   - Go to the "Bot" section and click "Add Bot"
   - Copy the bot token

2. Configure the bot:
   - Open `discord_music_bot.py`
   - Replace `'your_bot_token'` with your actual bot token
   - Save the file

3. Invite the bot to your server:
   - Go to OAuth2 > URL Generator in the Discord Developer Portal
   - Select the following scopes:
     - bot
     - applications.commands
   - Select the following bot permissions:
     - Send Messages
     - Embed Links
     - Connect
     - Speak
   - Copy and open the generated URL to invite the bot

## Usage

Start the bot:
```bash
# Windows
python discord_music_bot.py

# macOS/Linux
python3 discord_music_bot.py
```

### Available Commands

- `!play` or `!p`: Play a song (URL or search term)
- `!pause` or `!ps`: Pause the current song
- `!resume` or `!r`: Resume playback
- `!skip` or `!s`: Skip the current song
- `!queue` or `!q`: Show the current queue
- `!clear` or `!c`: Clear the queue
- `!volume` or `!v`: Set volume (0-100)
- `!leave` or `!l`: Disconnect the bot
- `!now` or `!n`: Show currently playing song
- `!commands` or `!cmd`: Show all available commands

## Troubleshooting

1. FFmpeg not found:
   - Make sure FFmpeg is properly installed and added to PATH
   - Try running `ffmpeg -version` in terminal/command prompt
   - Restart your system after installing FFmpeg

2. Audio not playing:
   - Ensure the bot has proper permissions in the voice channel
   - Check if your Discord voice region is compatible
   - Verify that the bot token is correct

3. Dependencies issues:
   - Try reinstalling dependencies: `pip install -r requirements.txt --force-reinstall`
   - Make sure you're using Python 3.8 or higher
   - Check if your virtual environment is activated

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
