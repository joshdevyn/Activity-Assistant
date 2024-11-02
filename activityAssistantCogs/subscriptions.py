from discord.ext import commands
from discord import Embed, Member, TextChannel
import random

class Subscription_Commands(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    @commands.command(
        aliases=["subscribed-channels", "subscribed"],
        help="Shows all channels a user is subscribed to for ping notifications. Usage: `!aa subscribed_channels [member]`"
    )
    async def subscribed_channels(self, ctx, member: Member = None):
      """
      Displays a list of channels the specified member (or the command invoker if no member is specified) is subscribed to for notifications.
      
      :param ctx: The context in which the command was called.
      :param member: The member whose subscriptions are to be displayed. Defaults to the command invoker.
      """
      if member == None:
        member = ctx.author
  
      listOfAllItems = await self.client.db_handler.execute(
          f"SELECT * FROM pingME WHERE memberID = %s AND guildID = %s",
        (ctx.author.id, ctx.guild.id))
  
      if len(listOfAllItems) == 0:
        if member.id == ctx.author.id:
          text = "You haven't subscribed to any channel yet!"
        else:
          text = f"{member.mention} hasn't subscribed to any channel yet!"
        embed0 = Embed(title=text, color=random.randint(0, 0xffffff))
        await ctx.send(embed=embed0)
        return
      PingMeInThere = []
  
      for i in listOfAllItems:
        PingMeInThere.append(int(i['channelID']))
      else:
        channels = ""
        for key in PingMeInThere:
          channel = self.client.get_channel(int(key))
          if channel != []:
  
            channels += f"{channel.mention} - "
        if len(channels) > 2000:
          if member.id == ctx.author.id:
            channels = f"You are subscribed to **{len(channels)}** channels"
          else:
            channels = f"{member.mention} is subscribed to **{len(channels)}** channels"
        else:
          channels = channels[:-3]
        embed = Embed(title="Subscribed Channels",
                      description=channels,
                      color=random.randint(0, 0xffffff))
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        if member.id != ctx.author.id:
          embed.set_footer(text=f"Requested by {ctx.author.name}",
                           icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
        return

    @commands.command(
        aliases=["subscribed-members"],
        help="Shows all members subscribed to a specified channel for ping notifications. Usage: `!aa subscribed_members <#channel>`"
    )
    async def subscribed_members(self, ctx, channel: TextChannel = None):
      """
      Lists all members subscribed to notifications for the specified text channel.
      
      :param ctx: The context in which the command was called.
      :param channel: The text channel to check subscriptions for.
      """
      if channel == None:
        embed0 = Embed(title="How to use this command?",
                       description=f"{ctx.message.content} <#channel>`",
                       color=random.randint(0, 0xffffff))
        await ctx.send(embed=embed0)
        return
      try:
        listOfAllItems = await self.client.db_handler.execute(
            f"SELECT * FROM pingME WHERE channelID = %s AND guildID = %s",
          (channel.id, ctx.guild.id))
      except Exception:
        pass
  
      if len(listOfAllItems) == 0:
        embed0 = Embed(title="This channel has no subscribers!",
                       color=random.randint(0, 0xffffff))
        await ctx.send(embed=embed0)
        return
      PingMeInThere = []
      list_of_members = []
      for i in listOfAllItems:
        PingMeInThere.append((int(i['memberID']), int(i['channelID'])))
      for key, value in PingMeInThere:
        member = ctx.guild.get_member(int(key))
        if member != []:
  
          list_of_members.append(member.id)
  
      if len(list_of_members) == 1:
        msg = f"Only {len(list_of_members)} member is subscribed to {channel.mention}"
      else:
        msg = f"A total of {len(list_of_members)} members are subscribed to {channel.mention}"
      embed = Embed(description=msg, color=random.randint(0, 0xffffff))
      await ctx.send(embed=embed)
      return
  
    @commands.command(
        aliases=["subscribed-keywords", "keywords"],
        help="Shows all keywords a user is subscribed to for notifications. Usage: `!aa subscribed_keywords [member]`"
    )
    async def subscribed_keywords(self, ctx, member: Member = None):
        """
        Displays a list of keywords the specified member (or the command invoker if no member is specified) is subscribed to.
        
        :param ctx: The context in which the command was called.
        :param member: The member whose keyword subscriptions are to be displayed. Defaults to the command invoker.
        """
        if member is None:
            member = ctx.author

        try:
            subscribed_keywords = await self.client.db_handler.execute(
                "SELECT keyword FROM keywordPings WHERE memberID = %s AND guildID = %s",
                (member.id, ctx.guild.id)
            )
        except Exception as e:
            print(f"Error fetching subscribed keywords: {e}")
            embed = Embed(title="Error", description="An error occurred while fetching the keywords.", color=random.randint(0, 0xffffff))
            await ctx.send(embed=embed)
            return

        if not subscribed_keywords:
            text = "You haven't subscribed to any keywords yet!" if member == ctx.author else f"{member.mention} hasn't subscribed to any keywords yet!"
            embed = Embed(title=text, color=random.randint(0, 0xffffff))
            await ctx.send(embed=embed)
            return

        keyword_list = [item['keyword'] for item in subscribed_keywords]
        keywords_display = ", ".join(keyword_list)

        embed = Embed(
            title="Subscribed Keywords",
            description=keywords_display,
            color=random.randint(0, 0xffffff)
        )
        embed.set_author(name=member.display_name, icon_url=member.avatar.url)
        if member.id != ctx.author.id:
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)  

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Subscription_Commands(client, db_handler))
