from activityAssistantCogs.Config.activityAssistantConfig import *
import random
from discord.ext import commands
from discord import Embed

class Blacklist_Management_Commands(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler
        print("Blacklist_Management_Commands initialized.")

    @commands.command(help="Displays the current blacklist for the server. Usage: `!aa blacklist`")
    @commands.has_permissions(manage_guild=True)
    async def blacklist(self, ctx):
        """
        Displays the current blacklist, including members, channels, and moving restrictions.
        
        Usage:
        - `!blacklist` to display all current blacklists.
          
        Permissions Required: Manage Guild
        """

        print("Blacklist_Management_Commands.blacklist: Starting execution")

        move_blacklists = []
        channels_blacklists = []
        members_blacklists = []

        # Fetch moveBlacklist
        try:
            print("Blacklist_Management_Commands.blacklist: Fetching moveBlacklist from DB")
            listOfAllItems = await self.db_handler.execute(
                "SELECT * FROM moveBlacklist WHERE guildID = %s", (ctx.guild.id,)
            )
            for item in listOfAllItems:
                move_blacklists.append(int(item['channelID']))
            print(f"Blacklist_Management_Commands.blacklist: move_blacklists = {move_blacklists}")
        except Exception as e:
            print(f"Blacklist_Management_Commands.blacklist: Error fetching moveBlacklist - {e}")

        # Fetch channelsBlacklist
        try:
            print("Blacklist_Management_Commands.blacklist: Fetching channelsBlacklist from DB")
            listOfAllItems = await self.db_handler.execute(
                "SELECT * FROM channelsBlacklist WHERE guildID = %s", (ctx.guild.id,)
            )
            for item in listOfAllItems:
                channels_blacklists.append(int(item['channelID']))
            print(f"Blacklist_Management_Commands.blacklist: channels_blacklists = {channels_blacklists}")
        except Exception as e:
            print(f"Blacklist_Management_Commands.blacklist: Error fetching channelsBlacklist - {e}")

        # Fetch membersBlacklist
        try:
            print("Blacklist_Management_Commands.blacklist: Fetching membersBlacklist from DB")
            listOfAllItems = await self.db_handler.execute(
                "SELECT * FROM membersBlacklist WHERE guildID = %s", (ctx.guild.id,)
            )
            for item in listOfAllItems:
                members_blacklists.append(int(item['memberID']))
            print(f"Blacklist_Management_Commands.blacklist: members_blacklists = {members_blacklists}")
        except Exception as e:
            print(f"Blacklist_Management_Commands.blacklist: Error fetching membersBlacklist - {e}")

        members_blacklist = ""
        if len(members_blacklists) == 0:
            members_blacklist = "None"
        else:
            for key in members_blacklists:
                members_blacklist += f"<@{key}>\n"

        channels_blacklist = ""
        if len(channels_blacklists) == 0:
            channels_blacklist = "None"
        else:
            for key in channels_blacklists:
                channels_blacklist += f"<#{key}>\n"

        move_text_blacklist = ""
        move_voice_blacklist = ""
        if len(move_blacklists) == 0:
            move_text_blacklist = "None"
            move_voice_blacklist = "None"
        else:
            for key in move_blacklists:
                channel = self.client.get_channel(int(key))
                if channel is None:
                    print(f"Blacklist_Management_Commands.blacklist: Deleting non-existent channelID {key} from moveBlacklist")
                    await self.db_handler.execute(
                        f'DELETE FROM moveBlacklist WHERE channelID = %s', (key,)
                    )
                elif channel is not None and str(channel.type) == "voice":
                    move_voice_blacklist += f"{channel.name}\n"
                else:
                    move_text_blacklist += f"<#{key}>\n"

        embed = Embed(title="Active Blacklists", color=random.randint(0, 0xffffff))
        embed.add_field(name="Members",
                        value=members_blacklist or "None",
                        inline=True)
        embed.add_field(name="Channels",
                        value=channels_blacklist or "None",
                        inline=True)
        embed.add_field(name="Moving Text Channels",
                        value=move_text_blacklist or "None",
                        inline=False)
        embed.add_field(name="Moving Voice Channels",
                        value=move_voice_blacklist or "None",
                        inline=True)

        print("Blacklist_Management_Commands.blacklist: Sending embed message")
        await ctx.send(embed=embed)
        print("Blacklist_Management_Commands.blacklist: Execution completed")
        return

    @commands.command(aliases=["remove-blacklist"], help="Removes an entry from the blacklist. Usage: `!aa remove-blacklist`")
    @commands.has_permissions(manage_guild=True)
    async def remove_blacklist(self, ctx, first_thing=None, second_thing=None):
      """
      Removes a specified member, channel, or moving restriction from the blacklist.
      
      Usage:
      - `!remove-blacklist members @Member` to remove a member from the blacklist.
      - `!remove-blacklist channels #Channel` to remove a channel from the blacklist.
      - `!remove-blacklist move #Channel` to remove a moving restriction.
      
      Aliases: remove-blacklist
      Permissions Required: Manage Guild
      """
      if first_thing == None:
        embed = Embed(title="How to use this command?",
                      color=random.randint(0, 0xffffff))
        embed.add_field(name="__Members__",
                        value=f"{ctx.message.content} members <@member>",
                        inline=False)
        embed.add_field(name="__Channels__",
                        value=f"{ctx.message.content} channels <#channel>",
                        inline=False)
        embed.add_field(name="__Move__",
                        value=f"{ctx.message.content} move <#channel>",
                        inline=False)
        embed.add_field(
          name="__Note__",
          value="You can either mention the member/channel or use their ID",
          inline=False)
        await ctx.send(embed=embed)
        return
      else:
        if first_thing == "members":
          if second_thing == None:
            embed = Embed(title="How to use this command?",
                          color=random.randint(0, 0xffffff))
            embed.add_field(name="__Member__",
                            value=f"{ctx.message.content} member <@member>`",
                            inline=False)
            embed.add_field(
              name="__Note__",
              value="You can either mention the member/channel or use their ID",
              inline=False)
            await ctx.send(embed=embed)
            return
          else:
  
            member_ID = ""
            for m in second_thing:
              if m.isdigit():
                member_ID += m
            member = ctx.guild.get_member(int(member_ID))
            if member == None:
              embed0 = Embed(
                description=f"No member was found with this ID, `{member_ID}`",
                color=random.randint(0, 0xffffff))
              await ctx.send(embed=embed0)
              return
            else:
              memberBlackListed = await self.client.db_handler.execute(
                  "SELECT * FROM membersBlacklist WHERE guildID = %s AND memberID = %s",
                  (ctx.guild.id, member.id)
              )
                
              if memberBlackListed != []:
  
                await self.client.db_handler.execute(
                  f'DELETE FROM membersBlacklist WHERE memberID = %s AND guildID = %s',
                  (member.id, ctx.guild.id))
                embed = Embed(
                  description=
                  f"I have removed {member.mention} from the blacklist",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed)
                return
  
              else:
                embed0 = Embed(
                  description=f"This member is not in the blacklist",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed0)
                return
        elif first_thing == "channels":
          if second_thing == None:
            embed = Embed(title="How to use this command?",
                          color=random.randint(0, 0xffffff))
            embed.add_field(name="__Channels__",
                            value=f"{ctx.message.content} channels <#channel>`",
                            inline=False)
            embed.add_field(
              name="__Note__",
              value="You can either mention the member/channel or use their ID",
              inline=False)
            await ctx.send(embed=embed)
            return
          else:
            channel_ID = ""
            is_in = "False"
            for m in second_thing:
              if m.isdigit():
                channel_ID += m
            channel = self.client.get_channel(int(channel_ID))
            if channel == None:
              embed0 = Embed(
                description=f"No channel was found with this ID, `{channel_ID}`",
                color=random.randint(0, 0xffffff))
              await ctx.send(embed=embed0)
              return
            else:
              channels_blacklist = []

              channelBlackisted = await self.client.db_handler.execute(
                f"SELECT * FROM channelsBlacklist WHERE channelID = %s AND guildID = %s",
              (channel.id, ctx.guild.id))
  
              if channelBlackisted != []:
                await self.client.db_handler.execute(
                  f'DELETE FROM channelsBlacklist WHERE channelID = %s AND guildID = %s',
                  (channel.id, ctx.guild.id))
                embed = Embed(
                  description=
                  f"I have removed {channel.mention} from the blacklist",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed)
                return
              else:
                embed0 = Embed(
                  description=f"This channel is not in the blacklist",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed0)
                return
        elif first_thing == "move":
          if second_thing == None:
            embed = Embed(title="How to use this command?",
                          color=random.randint(0, 0xffffff))
            embed.add_field(name="__Move__",
                            value=f"{ctx.message.content} move <#channel>`",
                            inline=False)
            embed.add_field(
              name="__Note__",
              value="You can either mention the member/channel or use their ID",
              inline=False)
            await ctx.send(embed=embed)
            return
          else:
            channel_ID = ""
            is_in = "False"
            for m in second_thing:
              if m.isdigit():
                channel_ID += m
            channel = self.client.get_channel(int(channel_ID))
            if channel == None:
              embed0 = Embed(
                description=f"No channel was found with this ID, `{channel_ID}`",
                color=random.randint(0, 0xffffff))
              await ctx.send(embed=embed0)
              return
            else:
              channels_blacklist = []
              moveBlacklisted = await self.client.db_handler.execute(
                  f"SELECT * FROM moveBlacklist WHERE channelID = %s AND guildID = %s",
                (channel.id, ctx.guild.id))
  
              if moveBlacklisted != []:
                await self.client.db_handler.execute(
                  f'DELETE FROM moveBlacklist WHERE channelID = {channel.id}')
                embed = Embed(
                  description=
                  f"I have removed {channel.mention} from the blacklist",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed)
                return
              else:
                embed0 = Embed(
                  description=f"This channel is not in the blacklist",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed0)
                return

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Blacklist_Management_Commands(client, db_handler))
