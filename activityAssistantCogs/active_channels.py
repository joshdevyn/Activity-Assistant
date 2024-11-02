from activityAssistantCogs.Config.activityAssistantConfig import *
from discord.ext import commands
from discord import Embed
import discord
import random
from datetime import datetime

class Active_Channel_Commands(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    @commands.command(aliases=["active-channels"], help="Lists all active channels and their cooldowns. Usage: `!aa active-channels`")
    @commands.has_permissions(manage_guild=True)
    async def active_channels(self, ctx):
        """
        This command lists all channels marked as 'active' along with their remaining cooldowns before becoming inactive.
        Usage: !active-channels
        Aliases: !active-channels
        Permissions: Manage Guild
        """
        channels = ""

        print(f"[Active_Channel_Commands.active_channels] Fetching active channels for guild {ctx.guild.id} [{ctx.guild.name}]")
        listOfAllItems = await self.client.db_handler.execute(
                "SELECT * FROM activeTextChannels WHERE guildID = %s",
                (ctx.guild.id))
        print(f"[Active_Channel_Commands.active_channels] Fetched active channels for guild {ctx.guild.id} [{ctx.guild.name}]: {listOfAllItems}")

        print(f"[Active_Channel_Commands.active_channels] Fetching remove value for guild {ctx.guild.id} [{ctx.guild.name}]...")
        remove_value_check = await self.client.db_handler.execute("SELECT remove FROM active WHERE guildID = %s", (ctx.guild.id))
        print(f"[Active_Channel_Commands.active_channels] Fetched remove value for guild {ctx.guild.id} [{ctx.guild.name}]: {remove_value_check}")

        print(f"[Active_Channel_Commands.active_channels] Checking if remove value is empty for guild {ctx.guild.id} [{ctx.guild.name}]...")
        for item in remove_value_check:
            remove_value = int(item['remove'])
        print(f"[Active_Channel_Commands.active_channels] Remove value for guild {ctx.guild.id} [{ctx.guild.name}]: {remove_value}")
        
        if remove_value == []:
            print(f"[Active_Channel_Commands.active_channels] Remove value is empty for guild {ctx.guild.id} [{ctx.guild.name}]. Setting remove value to 900...")
            remove_value = 900

        activeChannelsList = []
        if len(listOfAllItems) > 0:
            print(f"[Active_Channel_Commands.active_channels] Creating active channels list for guild {ctx.guild.id} [{ctx.guild.name}]...")
            for activeChannel in listOfAllItems:
                activeChannelsList.append(activeChannel['channelID'])
            print(f"[Active_Channel_Commands.active_channels] Active channels list for guild {ctx.guild.id} [{ctx.guild.name}]: {activeChannelsList}")

            for channelID in activeChannelsList:
                x = 0
                print(f"[Active_Channel_Commands.active_channels] Fetching channel {channelID}...")
                channel = self.client.get_channel(int(channelID))
                print(f"[Active_Channel_Commands.active_channels] Fetched channel {channelID}: {channel}")

                if channel != [] and not isinstance(channel, discord.CategoryChannel) and channel != None:                    
                    try:
                        print(f"[Active_Channel_Commands.active_channels] Fetching last message from channel {channelID}...")
                        message = await self.client.get_channel(channel.id).fetch_message(channel.last_message_id)
                        print(f"[Active_Channel_Commands.active_channels] Fetched last message from channel {channelID}: {message}")
                    except discord.errors.NotFound:
                        print(f"[Active_Channel_Commands.active_channels] Fetching last message from channel {channelID} failed. Message not found.")
                        continue  # Skip to the next iteration if the message was not found

                    print(f"[Active_Channel_Commands.active_channels] Calculating cooldown for channel {channelID}...")
                    if message != []:
                        print(f"[Active_Channel_Commands.active_channels] Calculating cooldown for channel {channelID}... Message: {message}")
                        minutes = message.created_at.strftime('%M')
                        seconds = message.created_at.strftime('%S')
                        hours = message.created_at.strftime("%H")
                        days = message.created_at.strftime("%d")
                        month = message.created_at.strftime("%m")
                        year = message.created_at.strftime("%Y")
                        a = datetime(int(year), int(month), int(days), int(hours), int(minutes), int(seconds))
                        today = datetime.utcnow()
                        today_second = today.strftime("%S")
                        today_year = today.strftime("%Y")
                        today_month = today.strftime("%m")
                        today_day = today.strftime("%d")
                        today_hour = today.strftime("%H")
                        today_minute = today.strftime("%M")
                        b = datetime(int(today_year), int(today_month), int(today_day), int(today_hour),
                                     int(today_minute), int(today_second))
                        c = b - a
                        x = c.total_seconds()
                        print(f"[Active_Channel_Commands.active_channels] Calculated cooldown for channel {channelID}: {x}")

                    channels += f'{channel.name} | {str(channel.type)} | Cooldown: {remove_value - x}s\n'
                    print(f"[Active_Channel_Commands.active_channels] Added channel {channelID} to the list: {channels}")

            print(f"[Active_Channel_Commands.active_channels] Sending active channels list embed for guild {ctx.guild.id} [{ctx.guild.name}]...")
            embed = Embed(title="Active channels",
                          description=channels,
                          color=random.randint(0, 0xffffff))
            await ctx.send(embed=embed)
            print(f"[Active_Channel_Commands.active_channels] Sent active channels list embed for guild {ctx.guild.id} [{ctx.guild.name}]")
            return
        else:
            print(f"[Active_Channel_Commands.active_channels] Sending no active channels found embed for guild {ctx.guild.id} [{ctx.guild.name}]")
            embed0 = Embed(
                description=f"No Active Channels in\n**{ctx.guild.name}**",
                color=random.randint(0, 0xffffff))
            await ctx.send(embed=embed0)
            print(F"[Active_Channel_Commands.active_channels] Sent no active channels found embed for guild {ctx.guild.id} [{ctx.guild.name}]")
            return

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Active_Channel_Commands(client, db_handler))
