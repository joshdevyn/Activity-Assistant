from activityAssistantCogs.Config.activityAssistantConfig import *
from discord.ext import commands
from discord import Embed
import asyncio
from datetime import datetime, timedelta
import random
import re

class Active(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    @commands.command(help="Configures settings for active channels. Start here. Usage: `!aa active`")
    @commands.has_permissions(manage_guild=True)
    async def active(self, ctx, first_thing=None, second_thing=None, *, third_thing=None):
        """
        Configures settings for active channels, including categories, channels, messages, timer, and remove settings.
        
        Usage:
        - `!aa active` to show current settings.
        - `!aa active category <categoryID>` to set the category for active channels.
        - `!aa active channel <channelID>` to set the channel for notifications.
        - `!aa active timer <time>` to set the cooldown timer for active channel status.
        - `!aa active messages <number>` to set the number of messages within the timer period to activate the channel.
        - `!aa active remove <time>` to set the time after which an active channel is considered inactive.
        - `!aa active blacklist <type> <target>` to add a target to the blacklist. Type can be 'members', 'channels', or 'move'.
        
        Aliases: None
        Permissions Required: Manage Guild
        """
        print(f"[Active.active] Entered 'active' command with first_thing={first_thing}, second_thing={second_thing}, third_thing={third_thing}")
        if first_thing is None:
            print("[Active.active] first_thing is None, proceeding to fetch current settings.")
            # Fetch current settings from the database
            current_settings = await self.db_handler.execute(
                "SELECT categoryID, channelID, messages, timer, remove FROM active WHERE guildID = %s",
                ctx.guild.id
            )

            print(f"[Active.active] Fetched current_settings={current_settings}")

            if current_settings:
                for item in current_settings:
                  category_id = int(item['categoryID'])
                  channel_id = int(item['channelID'])
                  messages = int(item['messages'])
                  timer = int(item['timer'])
                  remove = int(item['remove'])
            else:
                category_id = channel_id = messages = timer = remove = None

            settings_summary = f"Category: {category_id or 'None'}, Channel: {channel_id or 'None'}, Messages: {messages or 'None'}, Timer: {timer or 'None'}, Remove: {remove or 'None'}"

            # Safely handle if no categories are available
            random_category = random.choice(ctx.guild.categories) if ctx.guild.categories else None
            category_example_id = random_category.id if random_category else '123456789'         
                
            embed = Embed(title="How to use this command?", color=random.randint(0, 0xffffff))
            embed.add_field(
                name="__Category__",
                value=f"{usage}`{pre}active category <categoryID>`\nTo set where the active channels will be moved to\n{example}{pre}active category {random_category.id}",
                inline=False)
            embed.add_field(
                name="__Channel__",
                value=f"{usage}`{pre}active channel <channelID>`\nTo set up where to mention the subscribed members when a channel becomes active\n{example}{pre}active channel {random_category.id}",
                inline=False)
            embed.add_field(
              name="__Timer__ ",
              value=
              f"{usage}`{pre}active timer <time>`\nTo set up the cooldown between a group of `messages` before a channel becomes activated (minimum: 5 minutes)\n{example}{pre}active timer 5m\n{note}\n`s` -> seconds\n`m` -> minutes\n`h` -> hours\n`d` -> days",
              inline=False)
            embed.add_field(
              name="__Messages__",
              value=
              f"{usage}`{pre}active messages <# of messages>`\nTo set how many messages need to be set within `time` to activate a channel (minimum: 2)\n{example}{pre}active messages 5",
              inline=False)
            embed.add_field(
              name="__Remove__",
              value=
              f"{usage}`{pre}active remove <time>`\nTo set up how long it takes a channel to not have any new messages before it's deactivated (minimum 5 minutes)\n{example}{pre}active remove 3m\n{note}\n`s` -> seconds\n`m` -> minutes\n`h` -> hours\n`d` -> days",
              inline=False)
      
            embed.add_field(name="__Blacklist__",
                            value=f"React with {forward} to see more details\nReact with {cancel_emoji} to stop",
                            inline=False)
            embed.set_footer(text=f"Current settings: {settings_summary}")
      
            print("[Active.active] Sending embed...")
            try:
                e = await ctx.send(embed=embed)
                await e.add_reaction(backward)
                await e.add_reaction(forward)
                await e.add_reaction(cancel_emoji)
            except Exception as error:
                print(f"[Active.active] Failed to send embed: {error}")

    
            embed1 = Embed(
              title="Blacklist",
              description=
              "Use this command to add blacklists whether members or channels",
              color=random.randint(0, 0xffffff))
            embed1.add_field(
              name="__Members__",
              value=
              f"{usage}`{pre}active blacklist members <@member>`\n{example}{pre}active blacklist members {ctx.author.mention}",
              inline=False)
            embed1.add_field(
              name="__Channels__",
              value=
              f"{usage}`{pre}active blacklist channels <#channel>`\n{example}{pre}active blacklist channels {ctx.channel.mention}",
              inline=False)
            embed1.add_field(
              name="__Move__",
              value=
              f"{usage}`{pre}active blacklist move <#channel>`\n{example}{pre}active blacklist move {ctx.channel.mention}",
              inline=False)
            embed1.add_field(
              name="__Note__",
              value=
              "You can either mention the member/channel or use their ID instead",
              inline=False)
            embed1.set_footer(text=f"React with {cancel_emoji} to stop (this setup times out after 5 minutes)")
            embed_dict = {1: embed, 2: embed1}
            flag = True
            pn = 1
      
            def check(reaction, user):
              return user == ctx.author and (str(reaction) == forward
                                            or str(reaction) == backward
                                            or str(reaction) == cancel_emoji)
      
            while flag:
              try:
                reaction, user = await self.client.wait_for("reaction_add",
                                                            timeout=300,
                                                            check=check)
              except asyncio.TimeoutError:
                embed0 = Embed(description="Time out",
                              color=random.randint(0, 0xffffff))
                # Remove reactions after timeout
                # await ctx.send(embed=embed0)
                # await e.clear_reactions()
                # return
                continue
              else:
                if str(reaction) == forward:
                  a = embed_dict.get(pn + 1)
                  await e.remove_reaction(reaction, ctx.author)
                  if a:
                    pn += 1
                    await e.edit(embed=a)
      
                elif str(reaction) == backward:
      
                  a = embed_dict.get(pn - 1)
                  await e.remove_reaction(reaction, ctx.author)
                  if a:
                    pn -= 1
                    await e.edit(embed=a)
      
                elif str(reaction) == cancel_emoji:
                  await e.clear_reactions()
                  return
      
        else:
          if second_thing == None:
            random_category = random.choice(ctx.guild.categories)
            embed = Embed(title="How to use this command?",
                          color=random.randint(0, 0xffffff))
            embed.add_field(
              name="__Category__",
              value=
              f"{usage}`{pre}active category <categoryID>`\n{example}{pre}active category {random_category.id}\n{note}To set where the active channels will be moved to",
              inline=False)
            embed.add_field(
              name="__Messages__",
              value=
              f"{usage}`{pre}active messages <time>`\n{example}{pre}active messages 5",
              inline=False)
            embed.add_field(
              name="__Remove__",
              value=
              f"{usage}`{pre}active remove <time>`\n{example}{pre}active remove 3m\n{note}\n`s` -> seconds\n`m` -> minutes\n`h` -> hours\n`d` -> days",
              inline=False)
            embed.add_field(name="__Blacklist__",
                            value=f"react with {forward} to see more details",
                            inline=False)
            embed.set_footer(text=f"React with {cancel_emoji} to stop (this setup times out after 5 minutes)")
    
            e = await ctx.send(embed=embed)
            await e.add_reaction(backward)
            await e.add_reaction(forward)
            await e.add_reaction(cancel_emoji)
    
            embed1 = Embed(
              title="Blacklist",
              description=
              "Use this command to add blacklists whether members or channels",
              color=random.randint(0, 0xffffff))
            embed1.add_field(
              name="__Members__",
              value=
              f"{usage}`{pre}active blacklist members <@member>`\n{example}{pre}active blacklist members {ctx.author.mention}",
              inline=False)
            embed1.add_field(
              name="__Channels__",
              value=
              f"{usage}`{pre}active blacklist channels <#channel>`\n{example}{pre}active blacklist channels {ctx.channel.mention}",
              inline=False)
            embed1.add_field(
              name="__Move__",
              value=
              f"{usage}`{pre}active blacklist move <#channel>`\n{example}{pre}active blacklist move {ctx.channel.mention}",
              inline=False)
    
            embed1.add_field(
              name="__Note__",
              value=
              "You can either mention the member/channel or use their ID instead",
              inline=False)
            embed1.set_footer(text=f"React with {cancel_emoji} to stop (this setup times out after 5 minutes)")
            embed_dict = {1: embed, 2: embed1}
            flag = True
            pn = 1
    
            def check(reaction, user):
              return user == ctx.author and (str(reaction) == forward
                                            or str(reaction) == backward
                                            or str(reaction) == cancel_emoji)
    
            while flag:
              try:
                reaction, user = await self.client.wait_for("reaction_add",
                                                            timeout=300,
                                                            check=check)
              except asyncio.TimeoutError:
                embed0 = Embed(description="Time out",
                              color=random.randint(0, 0xffffff))
                # Remove reactions after timeout
                # await ctx.send(embed=embed0)
                # await e.clear_reactions()
                # return
                continue
              else:
                if str(reaction) == forward:
                  a = embed_dict.get(pn + 1)
                  await e.remove_reaction(reaction, ctx.author)
                  if a:
                    pn += 1
                    await e.edit(embed=a)
    
                elif str(reaction) == backward:
    
                  a = embed_dict.get(pn - 1)
                  await e.remove_reaction(reaction, ctx.author)
                  if a:
                    pn -= 1
                    await e.edit(embed=a)
                elif str(reaction) == cancel_emoji:
                  embed0 = Embed(description="Cancelled",
                                color=random.randint(0, 0xffffff))
                  await ctx.send(embed=embed0)
                  await e.clear_reactions()
                  return
    
          else:
            if first_thing == "remove":
    
              times = ""
              if third_thing != None:
                times = second_thing + third_thing
              else:
                times = second_thing
              if times.endswith(("d", "h", "m", "s")):
                time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
                total_time = 0
                tim = times.split()
                ti = [int(''.join(i for i in t if i.isdigit())) for t in tim]
                tl = [(''.join(i for i in t if i.isdigit() == False)) for t in tim]
                for t in range(0, len(tl)):
                  total_time += ti[t] * int(time_convert[tl[t]])
                if total_time < 300:
                  embed0 = Embed(description="Minimum is **5 minutes**")
                  await ctx.send(ctx.author.mention, embed=embed0)
                  return
                tomorrow = datetime.utcnow() + timedelta(seconds=total_time)
                future_day = tomorrow.strftime("%d")
                future_hour = tomorrow.strftime("%H")
                future_minute = tomorrow.strftime("%M")
                future_year = tomorrow.strftime("%Y")
                future_month = tomorrow.strftime("%m")
                future_second = tomorrow.strftime("%S")
                today = datetime.utcnow()
                today_second = today.strftime("%S")
                today_year = today.strftime("%Y")
                today_month = today.strftime("%m")
                today_day = today.strftime("%d")
                today_hour = today.strftime("%H")
                today_minute = today.strftime("%M")
                a = datetime(int(future_year), int(future_month), int(future_day),
                            int(future_hour), int(future_minute),
                            int(future_second))
                b = datetime(int(today_year), int(today_month), int(today_day),
                            int(today_hour), int(today_minute), int(today_second))
                c = a - b
                d = str(c).split()
                expire_in = ""
                try:
                  v = str(d[2]).split(":")
                except Exception:
                  v = str(d[0]).split(":")
    
                  if int(v[0]) == 0 and int(v[1]) == 00 and int(v[2]) <= 10:
                    expire_in = "`10 seconds`"
                    pass
    
                  else:
    
                    if int(v[0]) == 0:
                      expire_in = f"`{v[1]} minutes`"
                      pass
                    if int(v[0]) != 0 and int(v[1]) > 0:
                      expire_in = f"`{v[0]} hours {v[1]} minutes`"
                      pass
                    if int(v[0]) != 0 and int(v[1]) == 0:
                      expire_in = f"`{v[0]} hours`"
                      pass
    
                else:
                  if int(d[0]) == 0:
                    if int(v[0]) == 0:
                      expire_in = f"`{v[1]} minutes`"
                      pass
                    elif int(v[0]) != 0 and int(v[1]) != 0:
                      expire_in = f"`{v[0]} hours {v[1]} minutes`"
                      pass
                    elif int(v[0]) != 0 and int(v[1]) == 0:
                      expire_in = f"`{v[0]} hours`"
                      pass
                  else:
                    if int(v[0]) == 0 and int(v[1]) != 0:
                      expire_in = f"`{d[0]} days, {v[1]} minutes`"
                      pass
                    elif int(v[0]) == 0 and int(v[0]) == 0:
                      expire_in = f"`{d[0]} days`"
                    elif int(v[0]) != 0 and int(v[1]) != 0:
                      expire_in = f"`{d[0]} days, {v[0]} hours {v[1]} minutes`"
                      pass
                    elif int(v[0]) != 0 and int(v[1]) == 0:
                      expire_in = f"`{d[0]} days, {v[0]} hours`"
                      pass
                    else:
                      expire_in = f"`{d[0]} days`"
                      pass
                await self.client.db_handler.execute(
                  'UPDATE active SET remove = %s WHERE guildID = %s',
                  (total_time, ctx.guild.id))
                embed = Embed(
                  description=
                  f"The channel will go back to normal every `{expire_in}`",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed)
                return
    
              else:
                embed = Embed(title="How to use this command?",
                              color=random.randint(0, 0xffffff))
                embed.add_field(
                  name="__Remove__",
                  value=f"{usage}`{pre} remove <time>`\n{example}{pre} remove 3m",
                  inline=False)
    
                embed.add_field(
                  name="__Note__",
                  value=f"`s` -> seconds\n`m` -> minutes\n`h` -> hours\n`d` -> days"
                )
                await ctx.send(embed=embed)
                return
    
            elif first_thing == "category":
              if second_thing.isdigit():
                category = self.client.get_channel(int(second_thing))
                if category != []:
                  if str(category.type) == "category":
                    embed = Embed(
                      description=
                      f"All active channels will be moved to {category.name}",
                      color=random.randint(0, 0xffffff))
                    await ctx.send(embed=embed)
                    await self.client.db_handler.execute(
                      "UPDATE active SET categoryID = %s WHERE guildID = %s",
                      (category.id, ctx.guild.id))
                    return
                  else:
                    embed0 = Embed(title="Please send a valid category ID",
                                  color=random.randint(0, 0xffffff))
                    await ctx.send(ctx.author.mention, embed=embed0)
                    return
                else:
                  embed0 = Embed(
                    description=
                    f"No category was found with this ID `{second_thing}`",
                    color=random.randint(0, 0xffffff))
                  await ctx.send(ctx.author.mention, embed=embed0)
                  return
              else:
                embed0 = Embed(title="Please provide a valid category ID",
                              color=random.randint(0, 0xffffff))
                await ctx.send(ctx.author.mention, embed=embed0)
                return
    
            elif first_thing == "channel":
              channelID = ""
              for i in second_thing:
                if i.isdigit():
                  channelID += i
    
              channel = self.client.get_channel(int(channelID))
              if channel != []:
                if str(channel.type) == "text":
                  embed = Embed(
                    description=
                    f"Set up {channel.mention} as active alerts channel",
                    color=random.randint(0, 0xffffff))
                  await ctx.send(embed=embed)
                  await self.client.db_handler.execute(
                    "UPDATE active SET channelID = %s WHERE guildID = %s",
                    (channel.id, ctx.guild.id))
                  return
                else:
                  embed0 = Embed(title="Please send a valid channel ID",
                                color=random.randint(0, 0xffffff))
                  await ctx.send(ctx.author.mention, embed=embed0)
                  return
              else:
                embed0 = Embed(
                  description=f"No channel was found with this ID `{second_thing}`",
                  color=random.randint(0, 0xffffff))
                await ctx.send(ctx.author.mention, embed=embed0)
                return
    
            elif first_thing == "timer":
    
              times = ""
              if third_thing != None:
                times = second_thing + third_thing
              else:
                times = second_thing
              if times.endswith(("d", "h", "m", "s")):
                time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
                total_time = 0
    
                tim = times.split()
    
                ti = [int(''.join(i for i in t if i.isdigit())) for t in tim]
    
                tl = [(''.join(i for i in t if i.isdigit() == False)) for t in tim]
    
                for t in range(0, len(tl)):
                  total_time += ti[t] * int(time_convert[tl[t]])
                if total_time < 300:
                  embed0 = Embed(description="Minimum is **5 minutes**")
                  await ctx.send(ctx.author.mention, embed=embed0)
                  return
                tomorrow = datetime.utcnow() + timedelta(seconds=total_time)
    
                future = tomorrow.strftime('%Y-%m-%d %H-%M-%S %p')
                future_day = tomorrow.strftime("%d")
                future_hour = tomorrow.strftime("%H")
                future_minute = tomorrow.strftime("%M")
                future_year = tomorrow.strftime("%Y")
                future_month = tomorrow.strftime("%m")
                future_second = tomorrow.strftime("%S")
                today = datetime.utcnow()
                today_second = today.strftime("%S")
                today_year = today.strftime("%Y")
                today_month = today.strftime("%m")
                today_day = today.strftime("%d")
                today_hour = today.strftime("%H")
                today_minute = today.strftime("%M")
                a = datetime(int(future_year), int(future_month), int(future_day),
                            int(future_hour), int(future_minute),
                            int(future_second))
                b = datetime(int(today_year), int(today_month), int(today_day),
                            int(today_hour), int(today_minute), int(today_second))
                c = a - b
                d = str(c).split()
                expire_in = ""
                try:
                  v = str(d[2]).split(":")
                except Exception:
                  v = str(d[0]).split(":")
    
                  if int(v[0]) == 0 and int(v[1]) == 00 and int(v[2]) <= 10:
                    expire_in = "`10 seconds`"
                    pass
    
                  else:
    
                    if int(v[0]) == 0:
                      expire_in = f"`{v[1]} minutes`"
                      pass
                    if int(v[0]) != 0 and int(v[1]) > 0:
                      expire_in = f"`{v[0]} hours {v[1]} minutes`"
                      pass
                    if int(v[0]) != 0 and int(v[1]) == 0:
                      expire_in = f"`{v[0]} hours`"
                      pass
    
                else:
                  if int(d[0]) == 0:
                    if int(v[0]) == 0:
                      expire_in = f"`{v[1]} minutes`"
                      pass
                    elif int(v[0]) != 0 and int(v[1]) != 0:
                      expire_in = f"`{v[0]} hours {v[1]} minutes`"
                      pass
                    elif int(v[0]) != 0 and int(v[1]) == 0:
                      expire_in = f"`{v[0]} hours`"
                      pass
                  else:
                    if int(v[0]) == 0 and int(v[1]) != 0:
                      expire_in = f"`{d[0]} days, {v[1]} minutes`"
                      pass
                    elif int(v[0]) == 0 and int(v[0]) == 0:
                      expire_in = f"`{d[0]} days`"
                    elif int(v[0]) != 0 and int(v[1]) != 0:
                      expire_in = f"`{d[0]} days, {v[0]} hours {v[1]} minutes`"
                      pass
                    elif int(v[0]) != 0 and int(v[1]) == 0:
                      expire_in = f"`{d[0]} days, {v[0]} hours`"
                      pass
                    else:
                      expire_in = f"`{d[0]} days`"
                      pass
                await self.client.db_handler.execute(
                  'UPDATE active SET timer = %s WHERE guildID = %s',
                  (total_time, ctx.guild.id))
                embed = Embed(
                  description=
                  f"I have set the difference between messages to be `{expire_in}`",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed)
                return
    
              else:
                embed = Embed(title="How to use this command?",
                              color=random.randint(0, 0xffffff))
                embed.add_field(
                  name="__Timer__",
                  value=f"{usage}`{pre} timer <time>`\n{example}{pre} timer 3m",
                  inline=False)
    
                embed.add_field(
                  name="__Note__",
                  value=f"`s` -> seconds\n`m` -> minutes\n`h` -> hours\n`d` -> days"
                )
                await ctx.send(embed=embed)
                return
    
            elif first_thing == "messages":
    
              if second_thing.isdigit():
    
                await self.client.db_handler.execute(
                  'UPDATE active SET messages = %s WHERE guildID = %s',
                  (second_thing, ctx.guild.id))
                embed = Embed(
                  description=
                  f"I have set up the number of messages to `{second_thing}`",
                  color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed)
                return
    
              else:
                embed = Embed(title="How to use this command?",
                              color=random.randint(0, 0xffffff))
    
                embed.add_field(
                  name="__Messages__",
                  value=
                  f"{usage}`{pre} messages <time>`\n{example}{pre} messages 5",
                  inline=False)
    
                await ctx.send(embed=embed)
                return
    
            elif first_thing == "blacklist":
              if second_thing == None:
                embed1 = Embed(
                  title="Blacklist",
                  description=
                  "Use this command to add blacklists whether members or channels",
                  color=random.randint(0, 0xffffff))
                embed1.add_field(
                  name="__Members__",
                  value=
                  f"{usage}`{pre}active blacklist members <@member>`\n{example}{pre}active blacklist members {ctx.author.mention}",
                  inline=False)
                embed1.add_field(
                  name="__Channels__",
                  value=
                  f"{usage}`{pre}active blacklist channels <#channel>`\n{example}{pre}active blacklist channels {ctx.channel.mention}",
                  inline=False)
                embed1.add_field(
                  name="__Move__",
                  value=
                  f"{usage}`{pre}active blacklist move <#channel>`\n{example}{pre}active blacklist move {ctx.channel.mention}",
                  inline=False)
    
                embed1.add_field(
                  name="__Note__",
                  value=
                  "You can either mention the member/channel or use their ID instead",
                  inline=False)
                await ctx.send(embed=embed1)
                return
              elif third_thing == None:
                embed1 = Embed(
                  title="Blacklist",
                  description=
                  "Use this command to add blacklists whether members or channels",
                  color=random.randint(0, 0xffffff))
                embed1.add_field(
                  name="__Members__",
                  value=
                  f"{usage}`{pre}active blacklist members <@member>`\n{example}{pre}active blacklist members {ctx.author.mention}",
                  inline=False)
                embed1.add_field(
                  name="__Channels__",
                  value=
                  f"{usage}`{pre}active blacklist channels <#channel>`\n{example}{pre}active blacklist channels {ctx.channel.mention}",
                  inline=False)
                embed1.add_field(
                  name="__Move__",
                  value=
                  f"{usage}`{pre}active blacklist move <#channel>`\n{example}{pre}active blacklist move {ctx.channel.mention}",
                  inline=False)
    
                embed1.add_field(
                  name="__Note__",
                  value=
                  "You can either mention the member/channel or use their ID instead",
                  inline=False)
                await ctx.send(embed=embed1)
                return
              else:
                if second_thing == "members":
                  member_ID = ""
                  for m in third_thing:
                    if m.isdigit():
                      member_ID += m
    
                  member = ctx.guild.get_member(int(member_ID))
                  if member == None:
                    await ctx.send(f"No member was found with this ID {member_ID}")
                    return
                  else:
                    memberBlacklisted = await self.client.db_handler.execute(
                        f"SELECT * FROM membersBlacklist WHERE memberID = %s AND guildID = %s",
                      (member.id, ctx.guild.id))
    
                    if memberBlacklisted != []:
    
                      embed0 = Embed(
                        description=f"This member is already blacklisted",
                        color=random.randint(0, 0xffffff))
                      await ctx.send(embed=embed0)
                      return
    
                    await self.client.db_handler.execute(
                      'INSERT INTO membersBlacklist VALUES (?, ?)',
                      (ctx.guild.id, member.id))
    
                    embed = Embed(
                      description=
                      f"I have added {member.mention} to the members blacklist",
                      color=random.randint(0, 0xffffff))
                    await ctx.send(embed=embed)
                    return
                elif second_thing == "channels":
                  channel_ID = ""
                  for m in third_thing:
                    if m.isdigit():
                      channel_ID += m
    
                  channel = self.client.get_channel(int(channel_ID))
                  if channel == None:
                    await ctx.send(
                      f"No channel was found with this ID {channel_ID}")
                    return
                  else:
                    channelBlacklisted = await self.client.db_handler.execute(
                        f"SELECT * FROM channelsBlacklist WHERE channelID = %s AND guildID = %s",
                      (channel.id, ctx.guild.id))
    
                    if channelBlacklisted != []:
                      embed0 = Embed(
                        description=f"This channel is already blacklisted",
                        color=random.randint(0, 0xffffff))
                      await ctx.send(embed=embed0)
                      return
    
                    await self.client.db_handler.execute(
                      'INSERT INTO channelsBlacklist VALUES (?, ?)',
                      (ctx.guild.id, channel.id))
    
                    embed = Embed(
                      description=
                      f"I have added {channel.mention} to the channels blacklist",
                      color=random.randint(0, 0xffffff))
                    await ctx.send(embed=embed)
                    return
                elif second_thing == "move":
                  channel_ID = ""
                  for m in third_thing:
                    if m.isdigit():
                      channel_ID += m
    
                  channel = self.client.get_channel(int(channel_ID))
                  if channel == None:
                    await ctx.send(
                      f"No channel was found with this ID {channel_ID}")
                    return
                  else:
                    moveBlacklisted = await self.client.db_handler.execute(
                        f"SELECT * FROM moveBlacklist WHERE channelID = %s AND guildID = %s",
                      (channel.id, ctx.guild.id))
    
                    if moveBlacklisted != []:
                      embed0 = Embed(
                        description=f"This channel is already blacklisted",
                        color=random.randint(0, 0xffffff))
                      await ctx.send(embed=embed0)
                      return
    
                    await self.client.db_handler.execute(
                        'INSERT INTO moveBlacklist (guildID, channelID) VALUES (%s, %s)',
                        (int(ctx.guild.id), int(channel.id))
                    )
    
                    embed = Embed(
                      description=
                      f"I have added {channel.mention} to the move blacklist",
                      color=random.randint(0, 0xffffff))
                    await ctx.send(embed=embed)
                    return
                elif second_thing == "category":
                  channel_ID = ""
                  for m in third_thing:
                    if m.isdigit():
                      channel_ID += m
    
                  category = self.client.get_channel(int(channel_ID))
                  if category == None:
                    await ctx.send(
                      f"No category was found with this ID {channel_ID}")
                    return
                  else:
                    if str(category.type) != "category":
                      embed0 = Embed(title=f"Please use a valid category ID",
                                    color=random.randint(0, 0xffffff))
                      await ctx.send(embed=embed0)
                      return
    
                    moveBlacklisted = await self.client.db_handler.execute(
                        f"SELECT * FROM bannedCategories WHERE categoryID = %s AND guildID = %s",
                      (category.id, ctx.guild.id))
    
                    if moveBlacklisted != []:
                      embed0 = Embed(
                        description=f"This category is already blacklisted",
                        color=random.randint(0, 0xffffff))
                      await ctx.send(embed=embed0)
                      return
    
                    await self.client.db_handler.execute(
                      'INSERT INTO bannedCategories VALUES (?, ?)',
                      (ctx.guild.id, category.id))
    
                    embed = Embed(
                      description=
                      f"I have added {category.name} to the category blacklist",
                      color=random.randint(0, 0xffffff))
                    await ctx.send(embed=embed)
                    return

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Active(client, db_handler))