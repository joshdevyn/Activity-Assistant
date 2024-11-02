import discord
from activityAssistantCogs.Config.activityAssistantConfig import *
from discord.ext import commands
import random
from discord import Embed
from collections import defaultdict
import re
import time

class Listeners(commands.Cog):

    def __init__(self, client, db_handler):
        self.client = client
        self.guild_cooldowns = defaultdict(int)
        self.COOLDOWN_SECONDS = 150  # Default: 150 seconds. Prevents spammers from rate-limiting the bot by activating the listener only after this cooldown.
        self.db_handler = db_handler
        self.rainbow_colors = [
            0xFF0000,  # Red
            0xFF4000,  # Reddish-Orange
            0xFF7F00,  # Orange
            0xFFBF00,  # Yellowish-Orange
            0xFFFF00,  # Yellow
            0xBFFF00,  # Yellowish-Green
            0x7FFF00,  # Greenish-Yellow
            0x00FF00,  # Green
            0x00FF7F,  # Greenish-Cyan
            0x00FFFF,  # Cyan
            0x007FFF,  # Blueish-Cyan
            0x0000FF,  # Blue
            0x4B0082,  # Indigo
            0x8B00FF   # Violet
        ]
        self.color_index = 0
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listens to messages across the server and performs actions based on content.
        - If the message mentions the bot without a command, it triggers the help message.
        - Checks for active channel alerts based on predefined conditions.
        This listener does not need direct invocation and operates in the background.

        No commands are directly associated with this listener.
        """
        print(f"[Listeners.on_message] Message received from {message.author} for guild {message.guild} in {message.channel}:\n{message.content}")
        # Ignore if the message is from a bot or doesn't have content
        if message.author.bot:
            print(f"[Listeners.on_message] Ignoring message from bot: {message.author}")
            return

        # Bot mention with no command triggers help message
        if message.content.strip() in [f"<@!{self.client.user.id}>", f"<@{self.client.user.id}>"]:
            ctx = await self.client.get_context(message)
            if ctx.valid:
                await ctx.invoke(self.client.get_command('help'))
            else:
                # Send a default help prompt if the context isn't valid for some reason
                help_prompt = f"Hi there! Use `{prefix}help` to see what I can do!"
                await message.channel.send(help_prompt)
            return  # Prevent further processing if it's just a bot mention
    
        guild_id = message.guild.id
        print(f"[Listeners.on_message] Guild ID: {guild_id}")
        now = time.time()
        print(f"[Listeners.on_message] Current timestamp: {now}")

        # Fetch the guild-specific cooldown from the database using the 'remove' field
        print(f"[Listeners.on_message] Fetching guild cooldown for guild: {guild_id}...")
        cooldown_seconds = await self.get_guild_cooldown(guild_id)
        print(f"[Listeners.on_message] Fetched guild cooldown: {cooldown_seconds} seconds for guild: {guild_id}")

        # Check if the message is from a bot
        if message.author.bot:
            print(f"[Listeners.on_message] Ignoring message from bot: {message.author}")
            return
        
        # Check for keyword pings
        print(f"[Listeners.on_message] Checking for keyword pings for guild {guild_id}...")
        
        # Fetch all keywords for this guild
        keyword_results = await self.client.db_handler.execute(
            "SELECT memberID, keyword FROM keywordPings WHERE guildID = %s", 
            (guild_id,)
        )
        print(f"[Listeners.on_message] Fetched keyword results: {keyword_results}")
        
        notified_users = set()

        for result in keyword_results:
            member_id = result['memberID']
            keyword = result['keyword']
            try:
                # Check if the keyword matches the message content using regex
                if re.search(keyword, message.content, re.IGNORECASE):
                    print(f"[Listeners.on_message] Keyword match found for member {member_id}: {keyword}")
                    user = message.guild.get_member(member_id)
                    if user and user not in notified_users:
                        notified_users.add(user)
                        embed = Embed(
                            title="Keyword Alert",
                            description=f"Your keyword `{keyword}` was mentioned in {message.channel.mention} by {message.author.mention}.",
                            color=random.choice(self.rainbow_colors)
                        )
                        embed.add_field(name="Message Content", value=message.content, inline=False)
                        await user.send(embed=embed)
                        print(f"[Listeners.on_message] Sent keyword alert to {user.name} ({user.id})")
            except re.error as e:
                print(f"[Listeners.on_message] Invalid regex pattern for keyword '{keyword}': {e}")
        
        # If not in cooldown, process the message and update the timestamp
        self.guild_cooldowns[guild_id] = now
        print("[Listeners.on_message] Global Active Message Check Cooldown expired! Now running commands...")
        print("[Listeners.on_message] Running Active_Alert_Check...")
        await self.active_alert_check(message)

    async def get_guild_cooldown(self, guild_id):
        print(f"[Listeners.on_message.get_guild_cooldown] Fetching guild-specific cooldown for guild ID {guild_id}...")
        result = await self.client.db_handler.execute("SELECT timer FROM active WHERE guildID = %s", (guild_id))
        if result and 'timer' in result:
            try:
                cooldown = int(result['timer'])
            except ValueError:
                cooldown = 150  # Default to 150 seconds if conversion fails
        else:
            cooldown = 150  # Default to 150 seconds if no result found
        return cooldown
    
    async def active_alert_check(self, message):
        """
        Checks if a channel should be marked as active based on recent messages.
        This method evaluates the activity within a channel and decides if it meets
        the criteria for being marked as 'active'. It also handles notifying users
        who have subscribed to activity alerts for specific channels.

        This method is an internal helper and not directly invoked by bot commands.
        """
        # Retrieve log channel ID from the database
        log_channel_id = await self.client.db_handler.fetch_log_channel_id(message.guild.id)
        
        if not log_channel_id:
            print(f"[Listeners.on_message.active_alert_check] No log channel configured for guild ID {message.guild.id}.")
            return
        else:
            print(f"[Listeners.on_message.active_alert_check] Log channel ID for guild {message.guild.name}: {log_channel_id}")

        log_channel = self.client.get_channel(log_channel_id)
        if not log_channel:
            print(f"[Listeners.on_message.active_alert_check] Could not find log channel with ID {log_channel_id} in guild {message.guild.name}.")
            return
        else:
            print(f"[Listeners.on_message.active_alert_check] Log channel with ID {log_channel_id} found in guild {message.guild.name}.")

        embed = Embed(title="Channel Activity Log", color=self.rainbow_colors[self.color_index])
        self.color_index = (self.color_index + 1) % len(self.rainbow_colors)

        chan = self.client.get_channel(message.channel.id)

        print(f"[Listeners.on_message.active_alert_check] Fetching active settings for guild {message.guild.id}...")
        message_check_result = await self.client.db_handler.execute("SELECT messages FROM active WHERE guildID = %s", (message.guild.id))
        print(f"[Listeners.on_message.active_alert_check] Active settings: {message_check_result}")
        message_check = int(message_check_result[0]['messages'])

        print(f"[Listeners.on_message.active_alert_check] Fetching cooldown settings for guild {message.guild.id}...")
        cooldown_check_result = await self.client.db_handler.execute("SELECT timer FROM active WHERE guildID = %s", (message.guild.id))
        cooldown_check = int(cooldown_check_result[0]['timer'])

        print(f"[Listeners.on_message.active_alert_check] Checking if channel {chan} is active based on message event and cooldown ({message_check} messages within {cooldown_check} seconds)...")
        last_message = await chan.fetch_message(chan.last_message_id)
        print(f"[Listeners.on_message.active_alert_check] Last message in channel {chan}: {last_message.content}")

        if last_message is None:
            return
        
        print(f"[Listeners.on_message.active_alerts_check] Fetching channels blacklist for guild {message.guild.id}...")
        channels_blacklist = await self.client.db_handler.execute("SELECT channelID FROM channelsBlacklist WHERE guildID = %s", (message.guild.id))
        print(f"[Listeners.on_message.active_alerts_check] Channels Blacklist: {channels_blacklist} for guild {message.guild.name}")
        
        print(f"[Listeners.on_message.active_alerts_check] Fetching members blacklist for guild {message.guild.id}...")
        members_blacklist = await self.client.db_handler.execute("SELECT memberID FROM membersBlacklist WHERE guildID = %s", (message.guild.id))
        print(f"[Listeners.on_message.active_alerts_check] Members Blacklist: {members_blacklist} for guild {message.guild.name}")

        print(f"[Listeners.on_message.active_alerts_check] Fetching active channels for guild {message.guild.id}...")
        activeChannel = await self.client.db_handler.execute(
            "SELECT * FROM activeTextChannels WHERE guildID = %s AND channelID = %s",
            (message.guild.id, message.channel.id)
        )
        print(f"[Listeners.on_message.active_alerts_check] Active Channel: {activeChannel} for guild {message.guild.name}.")

        if activeChannel:
            print(f"[Listeners.on_message.active_alerts_check] Channel {chan} is already active!\n[Listeners.on_message.active_alerts_check] Exiting Active Alert Check...")
            return

        if message.channel.id in channels_blacklist:
            print(f"[Listeners.on_message.active_alerts_check] Channel {chan} is in the blacklist!\n[Listeners.on_message.active_alerts_check] Exiting Active Alert Check...")
            return
        
        if message.author.id in members_blacklist:
            print(f"[Listeners.on_message.active_alerts_check] Author {message.author} is in the blacklist!\n[Listeners.on_message.active_alerts_check] Exiting Active Alert Check...")
            return

        # Check the non-bot activity in the channel
        messages = [msg async for msg in chan.history(limit=message_check)]
        if len(messages) < message_check:
            print(f"[Listeners.on_message.active_alert_check] Not enough messages in channel {chan}. Required: {message_check}, Found: {len(messages)}")
            return

        time_diffs = [int((messages[i].created_at - messages[i + 1].created_at).total_seconds()) for i in range(len(messages) - 1)]
        max_time_diff = max(time_diffs)

        if max_time_diff <= cooldown_check:
            print(f"[Listeners.on_message.active_alert_check] Channel {chan} meets the activity threshold. Max time difference: {max_time_diff} seconds (Threshold: {cooldown_check} seconds).")
            await self.activate_channel(chan)
        else:
            print(f"[Listeners.on_message.active_alert_check] Channel {chan} does not meet the activity threshold. Max time difference: {max_time_diff} seconds (Threshold: {cooldown_check} seconds).")
            print(f"[Listeners.on_message.active_alert_check] Preparing Activity Level Embed for Channel {chan}...")
            print(f"[Listeners.on_message.active_alert_check] Adding name field to embed for Channel {chan}...")
            if isinstance(chan, discord.Thread):
                embed.add_field(name="Thread Check", value=f"Thread: {chan.mention}", inline=False)
            elif isinstance(chan, discord.TextChannel):
                embed.add_field(name="Text Channel Check", value=f"Text Channel: {chan.mention}", inline=False)
            elif isinstance(chan, discord.VoiceChannel):
                embed.add_field(name="Voice Channel Check", value=f"Voice Channel: {chan.mention}", inline=False)
            elif isinstance(chan, discord.CategoryChannel):
                embed.add_field(name="Category Channel Check", value=f"Category Channel: {chan.mention}", inline=False)
            elif isinstance(chan, discord.StageChannel):
                embed.add_field(name="Stage Channel Check", value=f"Stage Channel: {chan.mention}", inline=False)

            # embed.add_field(name="Channel", value=chan.mention, inline=False)
            print(f"[Listeners.on_message.active_alert_check] Adding last message field to embed for channel {chan}...")
            embed.add_field(name="Last Message", value=last_message.content, inline=False)
            print(f"[Listeners.on_message.active_alert_check] Adding activity level field to embed for channel {chan}...")
            embed.add_field(name="Activity Level", value=f"{message_check} messages within {max_time_diff} seconds (Threshold: {cooldown_check} seconds)", inline=False)
            embed.add_field(name="Max Time Difference", value=f"{max_time_diff} seconds", inline=False)
            embed.add_field(name="Threshold", value=f"{message_check} messages within {cooldown_check} seconds", inline=False)

            # Adding the thumbnail and author info
            print(f"[Listeners.on_message.active_alert_check] Adding thumbnail to embed for channel {chan}...")

            # Try using both methods to ensure compatibility just in case
            try:
                avatar_url = message.author.avatar.url  # Newer versions of discord.py
            except AttributeError:
                avatar_url = message.author.avatar_url  # Older versions of discord.py

            print(f"[Listeners.on_message.active_alert_check] Avatar URL: {avatar_url}")
            embed.set_thumbnail(url=avatar_url)

            print(f"[Listeners.on_message.active_alert_check] Adding author info to embed for channel {chan}...")
            embed.set_author(name=message.author.name, icon_url=avatar_url)

            print(f"[Listeners.on_message.active_alert_check] Adding footer to embed for channel {chan}...")
            embed.set_footer(text=f"Message by {message.author.name}")

            print(f"[Listeners.on_message.active_alert_check] Sending Activity Level Embed to log channel {log_channel}...")
            await log_channel.send(embed=embed)
            print(f"[Listeners.on_message.active_alert_check] Activity Level Embed sent to log channel {log_channel}.")

    async def activate_channel(self, channel):
        """
        Activates a channel by renaming it, updating the database, and notifying users subscribed via pingME.
        """
        old_channel_name = channel.name

        # Insert into activeTextChannels
        print(f"[Listeners.on_message.active_alert_check] Channel {channel.name} meets the activity threshold. Inserting into activeTextChannels...")
        await self.client.db_handler.execute(
            "INSERT INTO activeTextChannels (guildID, channelID, categoryID) VALUES (%s, %s, %s)",
            (channel.guild.id, channel.id, channel.category.id if channel.category else None)
        )
        print(f"[Listeners.on_message.active_alert_check] Channel {channel.name} inserted into activeTextChannels.")
        
        # Check if reset is paused before moving
        print(f"[Listeners.on_message.active_alert_check] Checking if position resetting is paused for guild {channel.guild.id}...")
        is_paused = await self.db_handler.get_reset_paused(channel.guild.id)
        
        # Check if the channel is in the categories_channels table before moving it to the active category
        print(f"[Listeners.on_message.active_alert_check] Checking for channel in categories_channels for guild {channel.guild.id}...")
        channel_id_check = await self.client.db_handler.execute(
            "SELECT channelID FROM categories_channels WHERE guildID = %s AND channelID = %s",
            (channel.guild.id, channel.id)
        )
        print(f"[Listeners.on_message.active_alert_check] Channel ID Check: {channel_id_check} for guild {channel.guild.name}")

        # Rename the channel if applicable
        if isinstance(channel, discord.Thread):
            if not channel.name.endswith("-active") and not channel.name.endswith(" active"):
                new_channel_name = f"{channel.name}-active"
                await channel.edit(name=new_channel_name)
            if not channel.parent.name.endswith("-active") and not channel.parent.name.endswith(" active"):
                new_parent_name = f"{channel.parent.name}-active"
                await channel.parent.edit(name=new_parent_name)
        else:
            if not channel.name.endswith("-active") and not channel.name.endswith(" active"):
                new_channel_name = f"{channel.name}-active"
                await channel.edit(name=new_channel_name)
            print(f"[Listeners.on_message.active_alert_check] Channel {old_channel_name} renamed to {channel.name}.")

        print(f"[Listeners.on_message.active_alert_check] Channel {channel.name} activated successfully.")

        if is_paused:
            print(f"[Listeners.on_message.active_alert_check] Resetting is paused. Skipping the move of channel {channel.name}.")
        elif not channel_id_check:
            print(f"[Listeners.on_message.active_alert_check] Channel {channel.name} is not in the categories_channels table for guild {channel.guild.id}. Skipping the move of channel {channel.name}.")
        else:
            try:
                print(f"[Listeners.on_message.active_alert_check.helper_function] Fetching move blacklist for guild {channel.guild.id}...")
                move_blacklist = await self.client.db_handler.execute(
                    "SELECT channelID FROM moveBlacklist WHERE channelID = %s", 
                    (channel.id,)
                )
                print(f"[Listeners.on_message.active_alert_check.helper_function] Move Blacklist: {move_blacklist}")

                if move_blacklist and channel.id == move_blacklist[0]['channelID']:
                    print(f"[Listeners.on_message.active_alert_check] Channel {channel.name} is in the move blacklist! Exiting...")
                else:
                    print(f"[Listeners.on_message.active_alert_check] Checking for active category for guild {channel.guild}...")
                    active_category_id = await self.client.db_handler.execute(
                        "SELECT categoryID FROM active WHERE guildID = %s",
                        (channel.guild.id,)
                    )
                    active_category_id = active_category_id[0]['categoryID'] if active_category_id else None
                    print(f"[Listeners.on_message.active_alert_check] Active category ID for guild {channel.guild}: {active_category_id}")

                    if active_category_id:
                        try:
                            print(f"[Listeners.on_message.active_alert_check] Moving channel {channel.name} to active category {active_category_id}...")
                            active_category = self.client.get_channel(active_category_id)
                            if active_category:
                                await channel.edit(category=active_category, position=0)
                                print(f"[Listeners.on_message.active_alert_check] Channel {channel.name} moved to active category.")
                        except Exception as e:
                            print(f"[Listeners.on_message.active_alert_check] An error occurred while moving channel {channel.name} to active category: {e}")
            except Exception as e:
                print(f"[Listeners.on_message.active_alert_check.helper_function] An error occurred while checking the move blacklist: {e}")

        # Notify users subscribed via the pingME table
        print(f"[Listeners.on_message.active_alert_check.helper_function] Fetching pingME subscribers for channel {channel.id} in guild {channel.guild.id}...")
        ping_subscribers = await self.client.db_handler.execute(
            "SELECT memberID FROM pingME WHERE guildID = %s AND channelID = %s",
            (channel.guild.id, channel.id)
        )
        print(f"[Listeners.on_message.active_alert_check.helper_function] Subscribers found: {ping_subscribers}")

        # Collect subscribers for a single ping
        subscriber_mentions = []

        for subscriber in ping_subscribers:
            member_id = subscriber['memberID']
            user = channel.guild.get_member(member_id)
            if user:
                subscriber_mentions.append(user.mention)

        if subscriber_mentions:
            try:
                # Create a single notification embed
                embed = Embed(
                    title="Channel Activation Alert",
                    description=f"The channel {channel.mention} has become active!",
                    color=self.rainbow_colors[self.color_index]
                )
                embed.add_field(name="Notified Subscribers", value=', '.join(subscriber_mentions), inline=False)
                await log_channel.send(embed=embed)
                print(f"[Listeners.on_message.active_alert_check.helper_function] Single notification sent to log channel for subscribers.")
                self.color_index = self.color_index + 1
            except Exception as e:
                print(f"[Listeners.on_message.active_alert_check.helper_function] Failed to send notification to log channel: {e}")

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Listeners(client, db_handler))
