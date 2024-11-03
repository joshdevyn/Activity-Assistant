# Activity Assistant Discord Bot

## Overview

**Activity Assistant Bot** is an enterprise-grade Discord bot that offers comprehensive server management, event handling, and user engagement tools. It is designed with scalability, security, and performance in mind, making it an excellent addition to any Discord server requiring efficient automation and moderation.

## Key Features

- **Real-Time Event Management**: Handles and processes events dynamically.
- **Dynamic Presence Updates**: Automatically changes the bot's presence at regular intervals.
- **User and Keyword Subscriptions**: Supports channel and keyword-based notifications.
- **Automated Channel Position Management**: Captures, resets, and restores channel positions.
- **Blacklist Management**: Provides commands for managing blacklists for channels, members, and movement restrictions.
- **Comprehensive Help Command**: Displays detailed information and usage examples for all bot commands.
- **Asynchronous Database Integration**: Utilizes MySQL with connection pooling for efficient data handling.
- **Modular Cog Architecture**: Allows seamless expansion and maintenance.
- **Interactive Dashboard**: A built-in Flask-powered web dashboard for monitoring bot status and console output.

## Tech Stack and Requirements

### Core Technologies
- **Python 3.9+**
- **Discord.py**: A robust library for developing Discord bots.
- **Aiomysql**: An asynchronous MySQL client.
- **Aiohttp**: Used for HTTP session management.
- **Flask**: Powers the web-based dashboard for bot monitoring.

### Dependencies
Install the required dependencies by running:

```bash
pip install -r requirements.txt
```

### Additional Tools
- **MySQL**: For persistent database storage.
- **python-dotenv**: To manage environment variables securely.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd activity-assistant-bot
```

### 2. Configure the Environment

Create a `.env` file for environment configurations:

```dotenv
TOKEN="your-discord-bot-token"
MYSQL_HOST="your-mysql-host"
MYSQL_USER="your-mysql-username"
MYSQL_PASSWORD="your-mysql-password"
MYSQL_DB="your-mysql-database"
```

### 3. Set Up the Database

Ensure the MySQL database is set up with the necessary schema (these tables are also automatically created when you first successfully run the bot):

```sql
CREATE TABLE IF NOT EXISTS servers (guildID bigint PRIMARY KEY)
CREATE TABLE IF NOT EXISTS guildLogChannels (guildID bigint PRIMARY KEY, logChannelID bigint)
CREATE TABLE IF NOT EXISTS active (guildID bigint PRIMARY KEY, categoryID bigint, channelID bigint, messages text, timer text, remove text)
CREATE TABLE IF NOT EXISTS categories_channels (guildID bigint, categoryID bigint, channelID bigint, position int, PRIMARY KEY(guildID, categoryID, channelID))
CREATE TABLE IF NOT EXISTS pingME (guildID bigint, channelID bigint, memberID bigint, PRIMARY KEY(guildID, channelID, memberID))
CREATE TABLE IF NOT EXISTS bannedCategories (guildID bigint, categoryID bigint, PRIMARY KEY(guildID, categoryID))
CREATE TABLE IF NOT EXISTS membersBlacklist (guildID bigint, memberID bigint, PRIMARY KEY(guildID, memberID))
CREATE TABLE IF NOT EXISTS channelsBlacklist (guildID bigint, channelID bigint, PRIMARY KEY(guildID, channelID))
CREATE TABLE IF NOT EXISTS moveBlacklist (guildID bigint, channelID bigint, PRIMARY KEY(guildID, channelID))
CREATE TABLE IF NOT EXISTS activeTextChannels (guildID bigint, channelID bigint, categoryID bigint, PRIMARY KEY(guildID, channelID))
CREATE TABLE IF NOT EXISTS activeVoiceChannels (guildID bigint, channelID bigint, categoryID bigint, PRIMARY KEY(guildID, channelID))
CREATE TABLE IF NOT EXISTS reset_paused (guildID bigint PRIMARY KEY, is_paused boolean DEFAULT false)
CREATE TABLE IF NOT EXISTS keywordPings (guildID bigint, memberID bigint, keyword varchar(255), PRIMARY KEY (guildID, memberID, keyword))
```

### 4. Register the Bot with Discord

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.
2. Add a bot to the application and configure the necessary **Privileged Gateway Intents** (e.g., **Presence Intent**, **Server Members Intent**, **Message Content Intent**).
3. Copy the bot token and add it to your `.env` file.
4. Set up an OAuth2 URL in **OAuth2 > URL Generator**, select `bot` and `applications.commands`, assign the appropriate permissions, and use the URL to invite the bot to your server.

### 5. Run the Bot

Start the bot with:

```bash
python main.py
```

A confirmation message will appear in the console once the bot is running:

```plaintext
[Main.on_ready] Activity Assistant Bot has connected to Discord!
```

## Cogs and Functionalities

### Dashboard Integration

The bot includes a **Flask-based web dashboard** that provides a real-time view of console output and command details:

- **Real-Time Console Log**: See live console output with automatic scrolling.
- **Command Overview**: Displays commands grouped by module with descriptions, examples, and arguments.
- **Interactive**: Toggle auto-scroll functionality and navigate commands easily.

Start the dashboard by running:

```bash
python main.py
```

The dashboard will be available at `http://localhost:8106/` by default.

### Cog Descriptions

**Listeners Cog**:
- Monitors messages for keywords and triggers notifications.

**Ping_Commands Cog**:
- Controls pings for channels and keywords.

**Subscription_Commands Cog**:
- Lists user and channel subscriptions.

**Position_Commands Cog**:
- Resets and restores channel positions.

**Reset_Positions_Commands Cog**:
- Manages channel position resets and updates the database.

**Active_Channel_Commands Cog**:
- Lists and manages active channels and cooldowns.

**Blacklist_Management_Commands Cog**:
- Displays and modifies the server's blacklist.

**Events_Management Cog**:
- Centralizes event processing and management.

**Cog_Template Cog**:
- Use this as a template for creating new cogs. They will automatically be picked up by the `load_cogs` method in main when the bot starts.

## Command List

### Active
- **`active`**: Configures settings for active channels. Start here.
  - **Usage**: `!aa active`

### Active_Channel_Commands
- **`active_channels`**: Lists all active channels and their cooldowns.
  - **Usage**: `!aa active-channels`

### Blacklist_Management_Commands
- **`blacklist`**: Displays the current blacklist for the server.
  - **Usage**: `!aa blacklist`
- **`remove_blacklist`**: Removes an entry from the blacklist.
  - **Usage**: `!aa remove-blacklist`

### Events_Management
- **`pause_reset`**: Pauses the resetting of channel positions for the server.
  - **Usage**: `!aa pause`
- **`resume_reset`**: Resumes the resetting of channel positions for the server.
  - **Usage**: `!aa resume`

### Ping_Commands
- **`pingme`**: Subscribe to pings from specified channels.
  - **Usage**: `!aa pingme #channel1 #channel2 ...`
- **`unpingme`**: Unsubscribe from pings in specified channels.
  - **Usage**: `!aa unpingme #channel1 #channel2 ...`
- **`keywordping`**: Subscribe to notifications for a specified keyword or regex.
  - **Usage**: `!aa keywordping <keyword/regex>`
- **`unkeywordping`**: Unsubscribe from keyword notifications.
  - **Usage**: `!aa unkeywordping <keyword/regex>`

### Position_Commands
- **`return_positions`**: Restores channel positions for a specified category, channel, or all channels.
  - **Usage**: `!aa return_positions [ID]`
- **`reset_positions`**: Resets channel positions to their original settings.
  - **Usage**: `!aa reset_positions`

### Subscription_Commands
- **`subscribed_channels`**: Shows all channels a user is subscribed to for ping notifications.
  - **Usage**: `!aa subscribed_channels [member]`
- **`subscribed_keywords`**: Shows all keywords a user is subscribed to for notifications.
  - **Usage**: `!aa subscribed_keywords [member]`
- **`subscribed_members`**: Shows all members subscribed to a specified channel for ping notifications.
  - **Usage**: `!aa subscribed_members <#channel>`

## Initial Setup
Use `!aa active` to set up the bot for the first time.

## Code Design and Architecture

- **Asynchronous Design**: Ensures non-blocking performance.
- **Modular Structure**: Cogs make the codebase scalable and maintainable.
- **Web Dashboard**: Allows easy monitoring of bot activity.
- **Security Measures**: Uses `.env` for sensitive data, avoids hard-coded credentials.

## Security Considerations

- **Environment Variables**: Keep sensitive data secure in a `.env` file. Never commit this to main.
- **Bot Token Safety**: Ensure your token is private and not shared publicly.
- **Database Security**: Use strong credentials and access controls for MySQL.

## Contribution Guidelines

1. **Fork the Repository**.
2. **Create a Branch**: `git checkout -b feature/your-feature`.
3. **Commit Your Changes**: `git commit -m 'Add new feature'`.
4. **Push to Branch**: `git push origin feature/your-feature`.
5. **Open a Pull Request**.

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**. This license allows for viewing and sharing, but prohibits modifications and commercial use.

## Contact and Support

For questions or issues, please open an issue in the repository.
