from discord.ext import commands
from discord import Embed
from discord.abc import GuildChannel
from datetime import datetime, timezone, timedelta
import asyncio
import discord

class Events_Management(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    @commands.command(
        aliases=["pause"],
        help="Pauses the resetting of channel positions for the server. Usage: `!aa pause`"
    )
    async def pause_reset(self, ctx):
        guild_id = ctx.guild.id
        await self.db_handler.set_reset_paused(guild_id, True)
        await ctx.send("Channel position reset has been paused for this server.")
        print(f"[Events_Management.pause_reset] Channel position reset has been paused for guild {guild_id}.")

    @commands.command(
        aliases=["resume"],
        help="Resumes the resetting of channel positions for the server. Usage: `!aa resume`"
    )
    async def resume_reset(self, ctx):
        guild_id = ctx.guild.id
        is_paused = await self.db_handler.get_reset_paused(guild_id)
        if is_paused:
            await self.db_handler.set_reset_paused(guild_id, False)
            await ctx.send("Channel position reset has been resumed for this server.")
            print(f"[Events_Management.resume_reset] Server position reset has been resumed for guild {guild_id}.")
        else:
            await ctx.send("Channel position reset was not paused for this server.")
            print(f"[Events_Management.resume_reset] Tried to resume but channel position reset was not paused for guild {guild_id}.")

    async def process_guild(self, guild):
        print(f"[Events_Management.process_guild] Processing guild {guild}...")
        log_channel_id = await self.db_handler.fetch_log_channel_id(guild.id)
        log_channel = self.client.get_channel(log_channel_id) if log_channel_id else None
        print(f"[Events_Management.process_guild] Log channel: {log_channel}")

        await self.check_active_channels(guild, log_channel)

    async def check_active_channels(self, guild, log_channel):
        print(f"[Events_Management.check_active_channels] Checking active channels in guild {guild}...")
        active_channels = await self.db_handler.execute("SELECT * FROM activeTextChannels WHERE guildID = %s", (guild.id))
        print(f"[Events_Management.check_active_channels] Active channels found: {active_channels}")

        if not active_channels:
            print("[Events_Management.check_active_channels] No active channels found. Potentially resetting positions...")
            if isinstance(log_channel, GuildChannel):
                embed = Embed(
                    title="Activity Assistant: Channel Check",
                    description=f"No active channels found in **{guild}**. Resetting positions to defaults...",
                    color=0x00ff00
                )
                embed.add_field(name="Timestamp", value=str(datetime.now()), inline=False)
                await log_channel.send(embed=embed)
                print(f"[Events_Management.check_active_channels] Sent No Active Channels embed for guild {guild} to guild channel {log_channel}")
            else:
                print(f"[Events_Management.check_active_channels] No log channel for guild: {guild}, skipping log message for reset positions.")
            await self.reset_positions(guild, log_channel)
            return

        print(f"[Events_Management.check_active_channels] Active channels found for guild {guild}: {active_channels}")
        cooldown_check_result = await self.db_handler.execute("SELECT remove FROM active WHERE guildID = %s", (guild.id))
        cooldown_check = int(cooldown_check_result[0]['remove']) if cooldown_check_result else 0

        channels_info = ""
        channels_to_deactivate = []

        for record in active_channels:
            channel_id = record['channelID']
            channel = self.client.get_channel(channel_id)
            if channel:
                try:
                    messages = [msg async for msg in channel.history(limit=10) if not msg.author.bot]
                    last_message = messages[0] if messages else None
                    now = datetime.now(timezone.utc)
                    if last_message:
                        time_since_last_message = (now - last_message.created_at).total_seconds()
                        cooldown_remaining = max(0, cooldown_check - time_since_last_message)
                    else:
                        cooldown_remaining = cooldown_check

                    cooldown_expires_at = now + timedelta(seconds=cooldown_remaining)
                    cooldown_expires_timestamp = int(cooldown_expires_at.timestamp())
                    cooldown_display = f"<t:{cooldown_expires_timestamp}:R>"

                    if cooldown_remaining <= 0:
                        channels_to_deactivate.append(channel)
                    
                    channel_name = channel.name if channel else 'Unknown Channel'
                    channels_info += f'Channel: <#{channel.id}>\nCooldown: {cooldown_display}\n'
                    print(f"[Events_Management.check_active_channels] Added channel {channel_name} with cooldown {int(cooldown_remaining)}s to the list.")
                except Exception as e:
                    print(f"[Events_Management.check_active_channels] Error fetching last message for channel {channel}: {e}")

            else:
                print(f"[Events_Management.check_active_channels] Channel object not available for ID {channel_id}. Removing channel {channel} from activeTextChannels table...")
                await self.db_handler.execute("DELETE FROM activeTextChannels WHERE channelID = %s", (channel_id))
                print(f"[Events_Management.check_active_channels] Removed channel {channel} from activeTextChannels table.")

        embed_description = channels_info if channels_info else "No active channels found."

        embed = Embed(
            title="Active Channels",
            color=0x00ff00
        )
        embed.add_field(name="Timestamp", value=str(datetime.now(timezone.utc)), inline=False)
        embed.add_field(name="Log Details", value=embed_description, inline=False)
        embed.set_image(url="https://media.discordapp.net/attachments/1177862338259460147/1257425292776046642/Active_Alerts_Embed_Image.gif?ex=66845c0f&is=66830a8f&hm=d818ab7829b09d07644631d050d056940f55fee116cd47d022603efa5d7ea754&=")

        if isinstance(log_channel, GuildChannel):
            await log_channel.send(embed=embed)
            print(f"[Events_Management.check_active_channels] Sent Active Channels embed for guild {guild} to guild channel {log_channel}")
        else:
            print(f"[Events_Management.check_active_channels] No log channel for guild: {guild}, unable to send Active Channels embed.")

        inactive_threshold = await self.fetch_inactive_threshold(guild.id)
        for record in active_channels:
            channel_id = record['channelID']
            await self.handle_active_channel(channel_id, guild, log_channel, inactive_threshold)

    async def fetch_inactive_threshold(self, guild_id):
        print(f"[Events_Management.fetch_inactive_threshold] Fetching inactive threshold for guild {guild_id}...")
        result_check = await self.db_handler.execute("SELECT remove FROM active WHERE guildID = %s", (guild_id))
        threshold = int(result_check[0]['remove']) if result_check else 900
        print(f"[Events_Management.fetch_inactive_threshold] Inactive threshold for guild {guild_id}: {threshold}")
        return threshold
    
    async def handle_active_channel(self, channel_id, guild, log_channel, inactive_threshold):
        print(f"[Events_Management.handle_active_channel] Handling active channel {channel_id} in guild {guild}...")

        channel = self.client.get_channel(channel_id)
        if not channel:
            print(f"[Events_Management.handle_active_channel] Channel ID {channel_id} not found in guild {guild}.")
            return

        message = None
        try:
            async for last_message in channel.history(limit=10):
                if not last_message.author.bot:
                    message = last_message
                    break
        except Exception as error:
            print(f"[Events_Management.handle_active_channel] Error fetching last message in channel {channel.name}: {error}")
            message = None

        if message:
            # Ensure the channel is in the correct active category
            print(f"[Events_Management.handle_active_channel] Ensuring channel {channel.name} is in the correct active category...")
            
            # Check if the channel is in the categories_channels table
            categories_channels_result = await self.client.db_handler.execute(
                "SELECT 1 FROM categories_channels WHERE guildID = %s AND channelID = %s",
                (guild.id, channel.id)
            )
            
            # Check if the channel is in the moveBlacklist
            blacklist_result = await self.client.db_handler.execute(
                "SELECT 1 FROM moveBlacklist WHERE guildID = %s AND channelID = %s",
                (guild.id, channel.id)
            )

            if not categories_channels_result:
                print(f"[Events_Management.handle_active_channel] Channel {channel.name} is not stored in the database. Not moving.")
            elif not blacklist_result:
                # If the channel is not in the blacklist, proceed with moving
                active_category_id_result = await self.client.db_handler.execute(
                    "SELECT categoryID FROM active WHERE guildID = %s",
                    (guild.id)
                )
                active_category_id = active_category_id_result[0]['categoryID'] if active_category_id_result else None

                if active_category_id and active_category_id != 0:
                    active_category = self.client.get_channel(active_category_id)
                    if active_category and isinstance(channel, discord.TextChannel) and channel.category != active_category:
                        # Check if reset is paused before moving
                        is_paused = await self.db_handler.get_reset_paused(guild.id)
                        if not is_paused:
                            print(f"[Events_Management.handle_active_channel] Moving channel {channel.name} to active category {active_category.name}")
                            await channel.edit(category=active_category)
                        else:
                            print(f"[Events_Management.reset_positions] Resetting positions is paused for guild {guild}. Cannot move channels back to their default inactive positions. Use `!aa resume` to resume position resets.")
                            if log_channel:
                                embed = Embed(
                                    title="Reset Positions Paused",
                                    description=f"Position reset is currently paused for **{guild}**. Cannot move <#{channel.id}> back to the active category {active_category}. Use `!aa resume` to resume active position resets.",
                                    color=0xffa500
                                )
                                await log_channel.send(embed=embed)
                    print(f"[Events_Management.handle_active_channel] Ensured channel {channel.name} is in the correct active category.")
                else:
                    print(f"[Events_Management.handle_active_channel] No active category set or categoryID is 0 for guild {guild.id}. Leaving channel {channel.name} in its current category.")
            else:
                print(f"[Events_Management.handle_active_channel] Channel {channel.name} is in the blacklist. Not moving.")

            time_difference = int(self.calculate_time_difference(message.created_at))
            print(f"[Events_Management.handle_active_channel] Time difference for {channel.name}: {time_difference} seconds (Threshold: {inactive_threshold} seconds)")
            if time_difference > inactive_threshold:
                print(f"[Events_Management.handle_active_channel] Time difference is above activation threshold, deactivating channel {channel.name}...")
                await self.deactivate_channel(channel, guild, log_channel)
                print(f"[Events_Management.handle_active_channel] Channel {channel.name} has been successfully deactivated.")
        else:
            await self.deactivate_channel(channel, guild, log_channel)

    async def reset_positions(self, guild, log_channel):
        guild_id = guild.id
        is_paused = await self.db_handler.get_reset_paused(guild_id)
        if is_paused:
            print(f"[Events_Management.reset_positions] Resetting positions is paused for guild {guild_id}. Cannot move channels back to their default inactive positions. Use `!aa resume` to resume position resets.")
            if log_channel:
                embed = Embed(
                    title="Reset Positions Paused",
                    description=f"Position reset is currently paused for **{guild}**.",
                    color=0xffa500
                )
                await log_channel.send(embed=embed)
            return

        print("[Events_Management.reset_positions] Now resetting positions to defaults...")
        original_positions = await self.db_handler.execute("SELECT * FROM categories_channels WHERE guildID = %s", (guild.id))
        original_positions = sorted(original_positions, key=lambda x: x['position'])
        move_blacklist = await self.db_handler.execute("SELECT channelID FROM moveBlacklist WHERE guildID = %s", (guild.id))
        move_blacklist_ids = {int(item['channelID']) for item in move_blacklist}

        for item in original_positions:
            channel_id, category_id, desired_position = int(item['channelID']), int(item['categoryID']), int(item['position'])
            
            if channel_id in move_blacklist_ids:
                print(f"[Events_Management.reset_positions] Skipping channel ID {channel_id} as it is in the move blacklist.")
                continue
            
            channel = self.client.get_channel(channel_id)
            if channel and channel.type in [discord.ChannelType.forum, discord.ChannelType.news, discord.ChannelType.text, discord.ChannelType.voice]:
                try:
                    if category_id == -1:
                        if channel.position != desired_position or channel.category is not None:
                            await channel.edit(position=desired_position, category=None)
                            print(f"[Events_Management.reset_positions] Channel '{channel.name}' updated to position {desired_position} without a category.")
                    else:
                        if channel.position != desired_position or channel.category_id != category_id:
                            await channel.edit(position=desired_position, category=self.client.get_channel(category_id))
                            print(f"[Events_Management.reset_positions] Channel '{channel.name}' updated to position {desired_position} in category {category_id}.")
                        else:
                            print(f"[Events_Management.reset_positions] Channel '{channel.name}' is already in the correct position and category.")
                except Exception as e:
                    print(f"[Events_Management.reset_positions] Failed to update channel '{channel.name}': {e}")
                    
            asyncio.sleep(1) # Sleep after updating each channel in a category to avoid hitting the rate limit

        print("[Events_Management.reset_positions] Positions are now reset to their defaults.")
        if isinstance(log_channel, discord.abc.GuildChannel):
            embed = discord.Embed(
                title="Activity Assistant: Reset Positions",
                description=f"All channels in **{guild}** have been reset to their default positions.",
                color=0x00ff00
            )
            await log_channel.send(embed=embed)

    async def deactivate_channel(self, channel, guild, log_channel):
        print(f"[Events_Management.deactivate_channel] Starting deactivation process for channel: {channel.name} (ID: {channel.id}) in guild: {guild.name} (ID: {guild.id}).")

        print("[Events_Management.deactivate_channel] Checking if the channel is blacklisted.")
        try:
            blacklisted_channel_record = await self.db_handler.execute(
                "SELECT channelID FROM channelsBlacklist WHERE channelID = %s AND guildID = %s",
                (channel.id, guild.id)
            )
        except Exception as e:
            print(f"[Events_Management.deactivate_channel] Error checking if channel {channel.name} is blacklisted: {e}")
        else:
            if blacklisted_channel_record:
                print(f"[Events_Management.deactivate_channel] Channel {channel.name} is blacklisted. Skipping deactivation.")
                return
            print(f"[Events_Management.deactivate_channel] Channel {channel.name} is not blacklisted. Proceeding with deactivation.")

        print("[Events_Management.deactivate_channel] Removing the channel from activeTextChannels in the database.")
        try:
            await self.db_handler.execute(
                "DELETE FROM activeTextChannels WHERE channelID = %s AND guildID = %s",
                (channel.id, guild.id)
            )
        except Exception as e:
            print(f"[Events_Management.deactivate_channel] Error removing channel {channel.name} from activeTextChannels: {e}")
        else:
            print(f"[Events_Management.deactivate_channel] Successfully removed channel {channel.name} from activeTextChannels in the database.")

        if isinstance(channel, discord.Thread):
            print(f"[Events_Management.deactivate_channel] Detected that {channel.name} is a thread.")
            
            if channel.name.endswith("-active"):
                print(f"[Events_Management.deactivate_channel] Removing '-active' suffix from thread name: {channel.name}.")
                try:
                    new_name = channel.name.rsplit("-active", 1)[0]
                    await channel.edit(name=new_name)
                except Exception as e:
                    print(f"[Events_Management.deactivate_channel] Error updating thread name: {e}")
                else:
                    print(f"[Events_Management.deactivate_channel] Successfully updated thread name from {channel.name} to {new_name}.")
                    
            # Check if any other channels in parent channel are active in the activeTextTextChannels table
            # If they are, do not reset the parent channel
            parent_category_records = await self.db_handler.execute(
                "SELECT * FROM activeTextChannels WHERE categoryID = %s AND guildID = %s",
                (channel.parent.id, guild.id)
            )
            for record in parent_category_records:
                if record['channelID'].parent.id == channel.parent.id:
                    print(f"For parent channel {channel.parent.name}, found active thread channel {record['channelID'].name}. Skipping resetting parent channel for thread channel.")
                    return

            if channel.parent.name.endswith("-active"):
                print(f"[Events_Management.deactivate_channel] Removing '-active' suffix from parent channel name: {channel.parent.name}.")
                try:
                    new_name = channel.parent.name.rsplit("-active", 1)[0]
                    await channel.parent.edit(name=new_name)
                except Exception as e:
                    print(f"[Events_Management.deactivate_channel] Error updating parent channel name: {e}")
                else:
                    print(f"[Events_Management.deactivate_channel] Successfully updated parent channel name from {channel.parent.name} to {new_name}.")

            # Archive threads. Might not be desired because it will remove them from the channel explorer pane.
            # print(f"[Events_Management.deactivate_channel] Archiving thread: {channel.name}.")
            # try:
            #     await channel.edit(archived=True)
            # except Exception as e:
            #     print(f"[Events_Management.deactivate_channel] Error archiving thread {channel.name}: {e}")
            # else:
            #     print(f"[Events_Management.deactivate_channel] Successfully archived thread {channel.name}.")

            # Move the parent channel back to its original position along with all channels in its category
            parent_channel = channel.parent
            if parent_channel:
                print(f"[Events_Management.deactivate_channel] Fetching original position and category for parent channel {parent_channel.name}.")
                try:
                    parent_category_records = await self.db_handler.execute(
                        "SELECT channelID, categoryID, position FROM categories_channels WHERE categoryID = (SELECT categoryID FROM categories_channels WHERE channelID = %s AND guildID = %s) AND guildID = %s ORDER BY position",
                        (parent_channel.id, guild.id, guild.id)
                    )
                except Exception as e:
                    print(f"[Events_Management.deactivate_channel] Error fetching original position and category for parent channel {parent_channel.name}: {e}")
                    print(f"[Events_Management.deactivate_channel] Cannot fetch category for channel {channel.name} in guild {guild.id}. Cannot move channel back its their default inactive positions. Use `!aa reset-positions` to add new channel positions.")
                    if log_channel:
                        embed = Embed(
                            title="Unknown Category Channel",
                            description=f"Unknown category for thread channel {channel.name} in **{guild}**. Leaving thread channel in current position.",
                            color=0xffa500
                        )
                        await log_channel.send(embed=embed)
                    return
                else:
                    if parent_category_records:
                        print(f"[Events_Management.deactivate_channel] Found {len(parent_category_records)} channels in the original category of parent channel {parent_channel.name}. Moving them back to their original positions.")

                        for record in parent_category_records:
                            channel_id = record['channelID']
                            original_category_id = record['categoryID']
                            original_position = record['position']
                            channel_to_move = self.client.get_channel(channel_id)

                            if channel_to_move:
                                print(f"[Events_Management.deactivate_channel] Moving channel {channel_to_move.name} back to its original position.")
                                try:
                                    await self.move_channel_to_original_position(channel_to_move, original_category_id, original_position)
                                except Exception as e:
                                    print(f"[Events_Management.deactivate_channel] Error moving channel {channel_to_move.name} back to original position: {e}")
                                else:
                                    print(f"[Events_Management.deactivate_channel] Successfully moved channel {channel_to_move.name} back to its original position.")
                    else:
                        print(f"[Events_Management.deactivate_channel] No original position and category found for parent channel {parent_channel.name}.")
            else:
                print(f"[Events_Management.deactivate_channel] No parent channel found for thread {channel.name}.")


        else:
            print(f"[Events_Management.deactivate_channel] Handling regular channel: {channel.name}.")
            
            if channel.name.endswith("-active"):
                print(f"[Events_Management.deactivate_channel] Removing '-active' suffix from channel name: {channel.name}.")
                try:
                    new_name = channel.name.rsplit("-active", 1)[0]
                    await channel.edit(name=new_name)
                except Exception as e:
                    print(f"[Events_Management.deactivate_channel] Error updating channel name: {e}")
                    return
                else:
                    print(f"[Events_Management.deactivate_channel] Successfully updated channel name to {channel.name}.")

            print("[Events_Management.deactivate_channel] Fetching category ID for the channel.")
            try:
                category_id_record = await self.db_handler.execute(
                    "SELECT categoryID FROM categories_channels WHERE channelID = %s AND guildID = %s",
                    (channel.id, guild.id)
                )
            except Exception as e:
                print(f"[Events_Management.deactivate_channel] Error fetching category ID for channel {channel.name}: {e}")
                print(f"[Events_Management.deactivate_channel] Cannot fetch category for channel {channel.name} in guild {guild.id}. Cannot move channel back its their default inactive positions. Use `!aa reset-positions` to add new channel positions.")
                if log_channel:
                    embed = Embed(
                        title="Unknown Category Channel",
                        description=f"Unknown category for channel {channel.name} in **{guild}**. Leaving channel in current position.",
                        color=0xffa500
                    )
                    await log_channel.send(embed=embed)
                return
            else:
                if category_id_record:
                    category_id = int(category_id_record[0]['categoryID'])
                    print(f"[Events_Management.deactivate_channel] Found category ID {category_id} for channel {channel.name}.")
                else:
                    category_id = None
                    print(f"[Events_Management.deactivate_channel] No category ID record found for channel {channel.name}. Proceeding without category ID.")

            print("[Events_Management.deactivate_channel] Fetching channels positions for the category.")
            try:
                channels_positions = await self.db_handler.execute(
                    "SELECT categoryID, channelID, position FROM categories_channels WHERE guildID = %s AND categoryID = %s",
                    (guild.id, category_id)
                )
                channels_positions = sorted(channels_positions, key=lambda x: x['position'])
            except Exception as e:
                print(f"[Events_Management.deactivate_channel] Error fetching channels positions: {e}")
                channels_positions = []
            else:
                print(f"[Events_Management.deactivate_channel] Successfully retrieved and sorted channel positions for category ID {category_id}.")

            print("[Events_Management.deactivate_channel] Fetching list of active channels.")
            try:
                active_channels = await self.db_handler.execute(
                    "SELECT channelID FROM activeTextChannels WHERE guildID = %s",
                    (guild.id)
                )
                active_channel_ids = set(record['channelID'] for record in active_channels)
            except Exception as e:
                print(f"[Events_Management.deactivate_channel] Error fetching active channels: {e}")
                active_channel_ids = set()
            else:
                print(f"[Events_Management.deactivate_channel] Successfully retrieved list of active channels for guild {guild.name}.")

            for record in channels_positions:
                channel_id = record['channelID']
                original_category_id = record['categoryID']
                original_position = record['position']
                channel_to_move = self.client.get_channel(channel_id)

                if channel_to_move and channel_id not in active_channel_ids:
                    print(f"[Events_Management.deactivate_channel] Checking if channel {channel_to_move.name} is blacklisted for moving.")
                    try:
                        move_blacklisted_channel_record = await self.db_handler.execute(
                            "SELECT channelID FROM moveBlacklist WHERE channelID = %s AND guildID = %s",
                            (channel_to_move.id, guild.id)
                        )
                    except Exception as e:
                        print(f"[Events_Management.deactivate_channel] Error checking if channel {channel_to_move.name} is move blacklisted: {e}")
                        continue
                    else:
                        if move_blacklisted_channel_record:
                            print(f"[Events_Management.deactivate_channel] Channel {channel_to_move.name} is blacklisted for moving. Skipping move.")
                            continue

                    print(f"[Events_Management.deactivate_channel] Moving channel {channel_to_move.name} back to original position.")
                    try:
                        await self.move_channel_to_original_position(channel_to_move, original_category_id, original_position)
                        await asyncio.sleep(2)  # Avoid rate limiting
                    except Exception as e:
                        print(f"[Events_Management.deactivate_channel] Error moving channel {channel_to_move.name} back to original position: {e}")
                    else:
                        print(f"[Events_Management.deactivate_channel] Successfully moved channel {channel_to_move.name} back to original position.")

        if log_channel:
            print("[Events_Management.deactivate_channel] Sending log message to the log channel.")
            try:
                embed = Embed(
                    title="Channel Deactivated",
                    description=f"Channel {channel.mention} has been deactivated due to not meeting Activation Threshold (use `!aa active` to view).",
                    color=0xff0000
                )
                embed.add_field(name="Guild", value=guild.name, inline=True)
                embed.add_field(name="Channel", value=channel.name, inline=True)
                await log_channel.send(embed=embed)
            except Exception as e:
                print(f"[Events_Management.deactivate_channel] Error sending log message to {log_channel.name}: {e}")
            else:
                print(f"[Events_Management.deactivate_channel] Successfully sent Deactivate Channel embed to log channel {log_channel.name} for guild {guild.name}.")

        print(f"[Events_Management.deactivate_channel] Completed deactivation process for channel: {channel.name} (ID: {channel.id}).")

    async def move_channel_to_original_position(self, channel, original_category_id, original_position):
        try:
            if original_category_id == -1:
                if channel.category is not None or channel.position != original_position:
                    await channel.edit(category=None, position=original_position)
                    print(f"[Events_Management.move_channel_to_original_position] Moved channel {channel} to no category and position: {original_position}.")
            else:
                original_category = self.client.get_channel(original_category_id)
                if not original_category:
                    print(f"[Events_Management.move_channel_to_original_position] Original category {original_category_id} not found. Setting category to None.")
                    original_category = None

                if channel.category_id != original_category_id or channel.position != original_position:
                    await channel.edit(category=original_category, position=original_position)
                    print(f"[Events_Management.move_channel_to_original_position] Moved channel {channel} to its original category [{original_category_id}] and position: {original_position}.")
        except Exception as e:
            print(f"[Events_Management.move_channel_to_original_position] Error moving channel {channel}: {e}")

    async def fetch_cooldown_threshold(self, guild_id):
        print(f"[Events_Management.fetch_cooldown_threshold] Fetching cooldown threshold for guild {guild_id}...")
        cooldown_info = await self.db_handler.execute("SELECT timer FROM active WHERE guildID = %s", (guild_id))
        cooldown = int(cooldown_info[0]['timer']) if cooldown_info else 900
        print(f"[Events_Management.fetch_cooldown_threshold] Cooldown threshold for guild {guild_id}: {cooldown}")
        return cooldown
        
    def calculate_time_difference(self, created_at):
        a = created_at.replace(tzinfo=None)
        b = datetime.utcnow()
        c = b - a
        time_difference = c.total_seconds()
        print(f"[Events_Management.calculate_time_difference] Time difference calculated: {time_difference} seconds")
        return time_difference

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Events_Management(client, db_handler))
