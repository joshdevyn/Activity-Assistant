from activityAssistantCogs.Config.activityAssistantConfig import *
from dashboard.dashboard import run_dashboard
import discord
import os
from discord.ext import commands, tasks
from handlers.database_handler import DatabaseHandler
from activityAssistantCogs.event_management import Events_Management
import aiohttp
from secret import TOKEN, mysql_config
import asyncio
import random

intents = discord.Intents.all()
client = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), intents=intents)

# Initialize DatabaseHandler as None first
client.db_handler = None

async def initialize_database():
    # Instantiate DatabaseHandler using the class method 'create'
    client.db_handler = await DatabaseHandler.create(client, mysql_config)
    await client.db_handler.setup_db()

activities = [
    lambda: discord.Game(name="with event-driven architecture 👷🏿‍♂️"),
    lambda: discord.Activity(type=discord.ActivityType.listening, name="your commands 🤖"),
    lambda: discord.Activity(type=discord.ActivityType.watching, name="over server activity levels ❤️‍🔥"),
    lambda: discord.Game(name="in multiple dimensions 🌌"),
    lambda: discord.Game(name="with async databases 📦"),
    lambda: discord.Activity(type=discord.ActivityType.competing, name="coding marathons 👨🏿‍💻"),
]

@tasks.loop(minutes=10)
async def change_bot_presence():
    try:
        # Randomly select an activity from the list
        current_activity = random.choice(activities)()
        await client.change_presence(activity=current_activity)
        print(f"[change_bot_presence] Changed presence to: {current_activity}")
    except Exception as e:
        print(f"[change_bot_presence] An error occurred: {e}")

@client.event
async def on_ready():
    print(f'[Main.on_ready] {client.user} has connected to Discord!')

    # Start the task to change bot presence periodically
    change_bot_presence.start()
    print("[Main.on_ready] Started change_bot_presence task.")

    # Initialize database
    await initialize_database()
    print("[Main.on_ready] Initialized database.")

    # Create an HTTP session for the client
    client.http_session = aiohttp.ClientSession()

    # Log that the bot has successfully logged in
    print(f"[Main.on_ready] We have logged in as {client.user.name}")

    # Start the main event loop for processing guilds
    EventLoop.start()
    print("[Main.on_ready] Started EventLoop task.")

@client.event
async def on_disconnect():
    # Properly close the database connection when the bot disconnects
    await client.db_handler.close_connection()

@tasks.loop(seconds=300)
async def EventLoop():
    try:
        print("[EventLoop] Running Main Event Loop...")
        # Retrieve the Events_Management cog instance
        events_management = client.get_cog("Events_Management")
        if events_management is not None:
            print("[EventLoop] Retrieved Events_Management cog.")
            # Create a list of coroutine objects for each guild
            tasks_to_run = [events_management.process_guild(guild) for guild in client.guilds]
            if tasks_to_run:  # Ensure there are tasks to run
                print(f"[EventLoop] Processing {len(tasks_to_run)} guilds in parallel...")
                await asyncio.gather(*tasks_to_run)
            else:
                print("[EventLoop] No guilds to process.")
        else:
            print("[EventLoop] Events_Management cog is not loaded or found.")
            # Attempt to reload the cog if not found
            await client.load_extension("activityAssistantCogs.event_management")
            print("[EventLoop] Attempted to reload Events_Management cog.")
    except Exception as e:
        print(f"[EventLoop] An error occurred: {e}")

@client.event
async def on_guild_join(guild):
    # Insert guild ID into the servers table
    servers_query = "INSERT INTO servers (guildID) VALUES (%s) ON DUPLICATE KEY UPDATE guildID = VALUES(guildID)"
    await client.db_handler.execute(servers_query, (guild.id))

client.remove_command("help")

@client.command()
async def help(ctx, *, word=None):
    if word is None:
        embed = discord.Embed(title="Bot Commands", description="Here are the commands you can use:", color=0xeee657)

        # Sort cogs alphabetically by name and commands within cogs by name
        sorted_cogs = sorted(client.cogs.items(), key=lambda cog: cog[0]) # Sort cogs alphabetically by name
        for cog_name, cog in sorted_cogs:
            commands_list = sorted(cog.get_commands(), key=lambda cmd: cmd.name)  # Sort commands alphabetically by name
            commands_info = "\n".join([
                "**{cmd_name}** - {desc}".format(
                    cmd_name=cmd.name,
                    desc=cmd.help.partition(". Usage:")[0] if cmd.help else 'No description available.',
                ) + ("\nUsage: `{}`".format(cmd.help.partition(". Usage: ")[2]) if ". Usage:" in cmd.help else "")
                for cmd in commands_list if not cmd.hidden
            ])
            if commands_info:
                embed.add_field(name=cog_name, value=commands_info, inline=False)
        embed.set_footer(text="Use !aa active to set up the bot if this is your first time using it.")
        await ctx.send(embed=embed)
    else:
        command = client.get_command(word)
        if command:
            embed = discord.Embed(title=f"{command.name.capitalize()} Command", color=0x22ee66)
            description = command.help.partition(". Usage:")[0] if command.help else "No description available."
            embed.add_field(name="Description", value=description, inline=False)
            usage = command.help.partition(". Usage: ")[2] if ". Usage:" in command.help else "No specific usage."
            embed.add_field(name="Usage", value="\nUsage: `{}`".format(usage) if usage else "No specific usage provided.", inline=False)
            if command.aliases:
                embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
            embed.set_footer(text="Use !aa active to set up the bot")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No information found for command: {word}")

async def load_cogs():
    print("[Main.on_ready.load_cogs] Loading cogs!\n")
    for root, dirs, files in os.walk('./activityAssistantCogs'):
        for filename in files:
            if filename.endswith('.py'):
                if filename.endswith('Config.py'):
                    continue
                else:
                    try:
                        await client.load_extension(f'activityAssistantCogs.{filename[:-3]}')
                        print(f'[Main.on_ready.load_cogs] {filename} is ready!')
                    except Exception as e:
                        print(f"[Main.on_ready.load_cogs] Failed to load {filename}: {e}")
                        import traceback
                        traceback.print_exc()  # This will print the full traceback
    print("\n[Main.on_ready.load_cogs] Cogs loaded!\n")

async def main():
    await initialize_database()
    await load_cogs()
    run_dashboard()
    await client.start(TOKEN) # If you're running this yourself, replace TOKEN with your bot token from .env, or wherever you store it

if __name__ == "__main__":
    asyncio.run(main())
