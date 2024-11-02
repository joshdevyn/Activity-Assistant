from discord.ext import commands
from discord import Embed
import random
import re

class Ping_Commands(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    @commands.command(
        help="Subscribe to pings from specified channels. Usage: `!aa pingme #channel1 #channel2 ...`"
    )
    async def pingme(self, ctx, *, channels=None):
      """
      Subscribes the user to pings from the specified channels.
      
      If no channels are specified, the command will return a usage message.
      Channels must be mentioned (e.g., #general) for the command to recognize them.
      
      :param ctx: The context under which the command is being invoked.
      :param channels: A space-separated list of channel mentions to subscribe to.
      """
      if channels == None:
        print(f"[Ping_Commands_pingme] No channels specified")
        embed0 = Embed(
          title="How to use this command?",
          description=
          f"{ctx.message.content} <#channel1> [#channel2] [#channel3]",
          color=random.randint(0, 0xffffff))
        embed0.add_field(
          name="Note",
          value="Please make sure to separate the channels with spaces",
          inline=False)
        await ctx.send(embed=embed0)
        return
      else:
        print(f"[Ping_Commands.pingme] Channels specified and not []: {channels}")
        list_of_channels = channels.split(" ")
        failed = ""
        success = ""
        already_subscribed_to = ""
        print(f"[Ping_Commands.pingme] list_of_channels: {list_of_channels}")
        try:
          print(f"[Ping_Commands.pingme] Trying to get list of all items...")
          listOfAllItems = await self.client.db_handler.execute(
              "SELECT * FROM pingME WHERE memberID = %s AND guildID = %s",
            (ctx.author.id, ctx.guild.id))
          print(f"[Ping_Commands.pingme] listOfAllItems: {listOfAllItems}")
        except Exception:
          print(f"Error: {Exception}")
          pass
        PingMeInThere = []
        print(f"[Ping_Commands.pingme] PingMeInThere: {PingMeInThere}")
        
        if len(listOfAllItems) > 0:
          for i in listOfAllItems:
            PingMeInThere.append(int(i['channelID']))
  
        print(f"[Ping_Commands.pingme] PingMeInThere: {PingMeInThere}")
        for channel_name in list_of_channels:
          channel_ID = re.sub('[<>&!@#$]', '', channel_name)
          channel = self.client.get_channel(int(channel_ID))
          print(f"[Ping_Commands.pingme] Processing pingme for channel: {channel}...")
  
          if channel == None:
            failed += f"{channel_name}\n"
          else:
  
            if channel.id not in PingMeInThere:
              await self.client.db_handler.execute(
                'INSERT INTO pingME VALUES (%s, %s, %s)',
                (ctx.guild.id, channel.id, ctx.author.id))
              success += f"{channel.mention}\n"
            else:
  
              already_subscribed_to += f"{channel.mention}\n"
  
        embed = Embed(color=random.randint(0, 0xffffff))
        if success == "":
          success = "None"
        embed.add_field(name="Success", value=success or "None", inline=True)
        if failed == "":
          failed = "None"
        embed.add_field(name="Failed", value=failed or "None", inline=True)
        if already_subscribed_to == "":
          already_subscribed_to = "None"
        embed.add_field(name="Already Subscribed to",
                        value=already_subscribed_to,
                        inline=False)
        await ctx.send(embed=embed)
  
    @commands.command(
        help="Unsubscribe from pings in specified channels. Usage: `!aa unpingme #channel1 #channel2 ...`"
    )
    async def unpingme(self, ctx, *, channels=None):
      """
      Unsubscribes the user from pings in the specified channels.
      
      If no channels are specified, the command will return a usage message.
      Channels must be mentioned (e.g., #general) for the command to recognize them.
      
      :param ctx: The context under which the command is being invoked.
      :param channels: A space-separated list of channel mentions to unsubscribe from.
      """
      if channels == None:
        embed0 = Embed(
          title="How to use this command?",
          description=
          f"{ctx.message.content} <#channel1> [#channel2] [#channel3]",
          color=random.randint(0, 0xffffff))
        embed0.add_field(
          name="Note",
          value="Please make sure to separate the channels with spaces",
          inline=False)
        await ctx.send(embed=embed0)
        return
      else:
        list_of_channels = channels.split(" ")
        failed = ""
        success = ""
        not_subscribed_to = ""
        try:
          listOfAllItems = await self.client.db_handler.execute(
              "SELECT * FROM pingME WHERE memberID = %s AND guildID = %s",
            (ctx.author.id, ctx.guild.id))
        except Exception:
          pass
  
        if len(listOfAllItems) == 0:
          text = "You haven't subscribed to any channel yet!"
  
          embed0 = Embed(title=text, color=random.randint(0, 0xffffff))
          await ctx.send(embed=embed0)
          return
        PingMeInThere = []
        for i in listOfAllItems:
          PingMeInThere.append(int(i['channelID']))
  
        for channel_name in list_of_channels:
          channel_ID = re.sub('[<>&!@#$]', '', channel_name)
          channel = self.client.get_channel(int(channel_ID))
          if channel == None:
            failed += f"{channel_name}\n"
          else:
  
            if channel.id not in PingMeInThere:
              not_subscribed_to += f"{channel.mention}\n"
  
            else:
              exists = False
              for key in PingMeInThere:
                if key == channel.id:
                  exists = True
              if exists == True:
                await self.client.db_handler.execute(
                  'DELETE FROM pingME WHERE memberID = %s AND channelID = %s AND guildID = %s',
                  (ctx.author.id, channel.id, ctx.guild.id))
  
                success += f"{channel.mention}\n"
              else:
                not_subscribed_to += f"{channel.mention}\n"
        embed = Embed(color=random.randint(0, 0xffffff))
        if success == "":
          success = "None"
        embed.add_field(name="Success", value=success or "None", inline=True)
        if failed == "":
          failed = "None"
        embed.add_field(name="Failed", value=failed or "None", inline=True)
        if not_subscribed_to == "":
          not_subscribed_to = "None"
        embed.add_field(name="Not Subscribed to",
                        value=not_subscribed_to,
                        inline=False)
        await ctx.send(embed=embed)
        
    @commands.command(
        help="Subscribe to notifications for a specified keyword or regex. Usage: `!aa keywordping <keyword/regex>`"
    )
    async def keywordping(self, ctx, *, keyword=None):
        """
        Subscribes the user to notifications for a specified keyword or regex.
        
        :param ctx: The context under which the command is being invoked.
        :param keyword: The keyword or regex pattern to subscribe to.
        """
        if not keyword:
            print(f"[Ping_Commands.keywordping] No keyword specified")
            embed = Embed(
                title="How to use this command?",
                description="`!aa keywordping <keyword/regex>`",
                color=random.randint(0, 0xffffff)
            )
            embed.add_field(
                name="Note",
                value="Please provide a keyword or regex pattern to set up notifications.",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        try:
            print(f"[Ping_Commands.keywordping] Checking existing keyword subscriptions for user {ctx.author.id} in guild {ctx.guild.id}...")
            existing_keyword = await self.client.db_handler.execute(
                "SELECT * FROM keywordPings WHERE memberID = %s AND guildID = %s AND keyword = %s",
                (ctx.author.id, ctx.guild.id, keyword)
            )

            if existing_keyword:
                print(f"[Ping_Commands.keywordping] User {ctx.author.id} is already subscribed to keyword: {keyword}")
                embed = Embed(
                    title="Already Subscribed",
                    description=f"You are already subscribed to the keyword/regex: `{keyword}`",
                    color=random.randint(0, 0xffffff)
                )
            else:
                print(f"[Ping_Commands.keywordping] Subscribing user {ctx.author.id} to keyword: {keyword}")
                await self.client.db_handler.execute(
                    "INSERT INTO keywordPings (guildID, memberID, keyword) VALUES (%s, %s, %s)",
                    (ctx.guild.id, ctx.author.id, keyword)
                )
                embed = Embed(
                    title="Subscription Successful",
                    description=f"You have subscribed to the keyword/regex: `{keyword}`",
                    color=random.randint(0, 0xffffff)
                )
            
            await ctx.send(embed=embed)

        except Exception as e:
            print(f"[Ping_Commands.keywordping] Error occurred: {e}")
            embed = Embed(
                title="Error",
                description="An error occurred while processing your request.",
                color=random.randint(0, 0xffffff)
            )
            embed.add_field(name="Details", value=str(e), inline=False)
            await ctx.send(embed=embed)
            raise e

    @commands.command(
        help="Unsubscribe from keyword notifications. Usage: `!aa unkeywordping <keyword/regex>`"
    )
    async def unkeywordping(self, ctx, *, keyword=None):
        """
        Unsubscribes the user from notifications for a specified keyword or regex.
        
        :param ctx: The context under which the command is being invoked.
        :param keyword: The keyword or regex pattern to unsubscribe from.
        """
        if not keyword:
            print(f"[Ping_Commands.unkeywordping] No keyword specified")
            embed = Embed(
                title="How to use this command?",
                description="`!aa unkeywordping <keyword/regex>`",
                color=random.randint(0, 0xffffff)
            )
            embed.add_field(
                name="Note",
                value="Please provide a keyword or regex pattern to unsubscribe.",
                inline=False
            )
            await ctx.send(embed=embed)
            return
        
        try:
            print(f"[Ping_Commands.unkeywordping] Removing keyword {keyword} for user {ctx.author.id} in guild {ctx.guild.id}...")
            result = await self.client.db_handler.execute(
                "SELECT * FROM keywordPings WHERE memberID = %s AND guildID = %s AND keyword = %s",
                (ctx.author.id, ctx.guild.id, keyword)
            )

            if not result:
                print(f"[Ping_Commands.unkeywordping] User {ctx.author.id} was not subscribed to keyword: {keyword}")
                embed = Embed(
                    title="Not Subscribed",
                    description=f"You were not subscribed to the keyword/regex: `{keyword}`",
                    color=random.randint(0, 0xffffff)
                )
            else:
                await self.client.db_handler.execute(
                    "DELETE FROM keywordPings WHERE memberID = %s AND guildID = %s AND keyword = %s",
                    (ctx.author.id, ctx.guild.id, keyword)
                )
                print(f"[Ping_Commands.unkeywordping] User {ctx.author.id} unsubscribed from keyword: {keyword}")
                embed = Embed(
                    title="Unsubscription Successful",
                    description=f"You have unsubscribed from the keyword/regex: `{keyword}`",
                    color=random.randint(0, 0xffffff)
                )

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"[Ping_Commands.unkeywordping] Error occurred: {e}")
            embed = Embed(
                title="Error",
                description="An error occurred while processing your request.",
                color=random.randint(0, 0xffffff)
            )
            embed.add_field(name="Details", value=str(e), inline=False)
            await ctx.send(embed=embed)
            raise e
    
async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Ping_Commands(client, db_handler))
