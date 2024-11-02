from activityAssistantCogs.Config.activityAssistantConfig import *
from discord.ext import commands
from discord import Embed
from discord import ChannelType
import random
import asyncio

class Reset_Positions_Commands(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    async def collect_categories_channels(self, ctx, e):
        categories_channels = {}
        banned_categories = await self.client.db_handler.execute(
            "SELECT * FROM bannedCategories WHERE guildID = %s",
            (ctx.guild.id))
        bannedCategories = [bCategory[1] for bCategory in banned_categories]
        
        # Handle channels without a category
        no_category_channels = {}
        for channel in ctx.guild.channels:
            if channel.category is None and channel.type != ChannelType.category:
                no_category_channels[channel.id] = channel.position
        
        if no_category_channels:
            categories_channels[-1] = no_category_channels  # Use -1 for channels without category
            m = "\n".join([f"{self.client.get_channel(ch_id).name} - {self.client.get_channel(ch_id).type} - #{pos}" for ch_id, pos in no_category_channels.items()])
            embed2 = Embed(title="Resetting channels without category",
                           description=m[:2000],  # Limit to 2000 characters based on discord limit
                           color=random.randint(0, 0xffffff))
            await e.edit(embed=embed2)
            await asyncio.sleep(2)  # Give time for users to see the embed

        for category in ctx.guild.categories:
            if category.id not in bannedCategories:
                category_channels = {}
                m = ""
                for channel in category.channels:
                    if channel.type != ChannelType.category:
                        category_channels[channel.id] = channel.position
                        m += f"{channel.name} - {channel.type} - #{channel.position}\n"
                        if len(m) >= 2000:
                            m = m[:1997] + "..."  # Truncate if too long
                categories_channels[category.id] = category_channels
                embed2 = Embed(title=f"Resetting {category.name}",
                               description=m,
                               color=random.randint(0, 0xffffff))
                await e.edit(embed=embed2)
                await asyncio.sleep(2)  # Give time for users to see the embed
        
        await e.delete()
        return categories_channels

    async def display_summary(self, ctx, categories_channels):
        total_char_count = len("Finished resetting all categories")
        
        embed = Embed(title="Finished resetting all categories", color=random.randint(0, 0xffffff))
        
        for category_id, channels in categories_channels.items():
            category_name = "No Category" if category_id == -1 else self.client.get_channel(category_id).name
            messages = []
            current_message = ""
            for channel_id, position in channels.items():
                channel = self.client.get_channel(channel_id)
                channel_name = channel.name
                channel_type = channel.type
                new_line = f"{channel_name} - {channel_type} - #{position}\n"
                
                if len(current_message) + len(new_line) > 1024:
                    messages.append(current_message)
                    current_message = new_line
                else:
                    current_message += new_line
            
            if current_message:
                messages.append(current_message)
            
            for i, m in enumerate(messages):
                field_name = category_name if i == 0 else category_name + f" (cont. {i})"
                if total_char_count + len(m) + len(field_name) > 6000 - 20:  # Leaving some buffer
                    # Send the current embed and create a new one
                    await ctx.send(embed=embed)
                    embed = Embed(title="Finished resetting all categories (continued)", color=random.randint(0, 0xffffff))
                    total_char_count = len("Finished resetting all categories (continued)")
                    
                total_char_count += len(m) + len(field_name)
                embed.add_field(name=field_name, value=m, inline=True)
        
        await ctx.send(embed=embed)

    async def get_user_choice(self, ctx):
        embed3 = Embed(title="Do you want to save these new positions?",
                       color=random.randint(0, 0xffffff))
        embed3.add_field(name="Yes", value=f"React with {approve}", inline=True)
        embed3.add_field(name="No", value=f"React with {deny}", inline=True)
        a = await ctx.send(ctx.author.mention, embed=embed3)
        await a.add_reaction(approve)
        await a.add_reaction(deny)
        def check(reaction, user):
            return user == ctx.author and (str(reaction) == approve or str(reaction) == deny)
        flag = True
        choice = ""
        while flag:
            try:
                reaction, user = await self.client.wait_for("reaction_add", timeout=6000, check=check)
            except asyncio.TimeoutError:
                embed0 = Embed(title="Time out", color=random.randint(0, 0xffffff))
                await ctx.send(embed=embed0)
                return None
            else:
                if str(reaction) == approve:
                    choice = "yes"
                    await a.delete()
                    flag = False
                elif str(reaction) == deny:
                    choice = "no"
                    await a.delete()
                    flag = False
                else:
                    continue
        return choice

    async def save_positions(self, ctx, categories_channels, total_channels):
        await self.client.db_handler.execute(
            "DELETE FROM categories_channels WHERE guildID = %s",
            (ctx.guild.id))
        embed5 = Embed(title="Saving the new positions",
                       description="Please wait...",
                       color=random.randint(0, 0xffffff))
        f = await ctx.send(embed=embed5)
        await asyncio.sleep(5)
        processed_channels = 0
        time_per_channel = 2  # seconds
        for category_id, channels in categories_channels.items():
            for channel_id, position in channels.items():
                chan = self.client.get_channel(int(channel_id))
                if category_id == -1:
                    await chan.edit(position=position, category=None)
                else:
                    cate = self.client.get_channel(int(category_id))
                    await chan.edit(position=position, category=cate)
                await self.client.db_handler.execute(
                    'INSERT INTO categories_channels VALUES (%s, %s, %s, %s)',
                    (ctx.guild.id, category_id, channel_id, position))
                await asyncio.sleep(time_per_channel)
                processed_channels += 1
                remaining_time = (total_channels - processed_channels) * time_per_channel
                minutes, seconds = divmod(remaining_time, 60)
                progress_bar_length = 20
                progress_blocks = int((processed_channels / total_channels) * progress_bar_length)
                progress_bar = f"{'♠' * progress_blocks}{'-' * (progress_bar_length - progress_blocks)}"
                embed5.description = f"Saving the new positions:\n`[{progress_bar}] {processed_channels}/{total_channels}`\nEstimated time remaining: {minutes}m {seconds}s"
                await f.edit(embed=embed5)
        embed4 = Embed(title="New positions have been saved", color=random.randint(0, 0xffffff))
        await f.edit(embed=embed4)
        return

    @commands.command(
        aliases=["reset-positions"],
        help="Resets channel positions to their original settings. Usage: `!aa reset_positions`"
    )
    async def reset_positions(self, ctx):
        """
        Initiates the process to reset channel positions within the guild based on previously saved configurations.
        
        This command will first collect the current categories and channels, display a summary,
        and then prompt the user for confirmation before applying the changes.
        
        :param ctx: The context under which the command is being invoked.
        """
        print("Running reset positions command")
        embed1 = Embed(title="Collecting Channels & Categories", color=random.randint(0, 0xffffff))
        e = await ctx.send(embed=embed1)
        await asyncio.sleep(5)
        categories_channels = await self.collect_categories_channels(ctx, e)
        await self.display_summary(ctx, categories_channels)
        choice = await self.get_user_choice(ctx)
        if choice == "yes":
            total_channels = sum(len(channels) for category, channels in categories_channels.items())
            await self.save_positions(ctx, categories_channels, total_channels)
        elif choice == "no":
            embed4 = Embed(title="New positions were not saved", color=random.randint(0, 0xffffff))
            await ctx.send(embed=embed4)
        else:
            embed0 = Embed(title="Resetting has been cancelled", color=random.randint(0, 0xffffff))
            await ctx.send(embed=embed0)

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Reset_Positions_Commands(client, db_handler))