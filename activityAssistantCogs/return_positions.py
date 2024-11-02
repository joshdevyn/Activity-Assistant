from discord.ext import commands
from discord import Embed
from discord import ChannelType
import random
import asyncio

class Position_Commands(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    def create_embed(self, title, description, color):
        return Embed(title=title, description=description, color=color)

    async def edit_embed_with_channel(self, status_message, embed, channel_name, position):
        embed.add_field(name=channel_name, value=f"Position: {position}", inline=False)
        await status_message.edit(embed=embed)
        if len(embed.fields) >= 25 or len(embed) > 6000:
            await status_message.edit(embed=embed)
            return self.create_embed(embed.title, embed.description, embed.color)
        return embed

    @commands.command(
        aliases=["return-positions"],
        help="Restores channel positions for a specified category, channel, or all channels. Usage: `!aa return_positions [ID]`"
    )
    async def return_positions(self, ctx, ID=None):
        """
        Restores channel positions within a specified category, channel, or all channels to their original settings based on the database.

        :param ctx: The context under which the command is being invoked.
        :param ID: The ID of the category or channel to restore positions for. If not provided, positions will be restored for all channels.
        """
        try:
            print("[Position_Commands.return_positions] Fetching banned categories...")
            banned_categories = await self.client.db_handler.execute(
                "SELECT categoryID FROM bannedCategories WHERE guildID = %s",
                ctx.guild.id
            )
            banned_category_ids = [banned_category['categoryID'] for banned_category in banned_categories]
            print(f"[Position_Commands.return_positions] Banned categories: {banned_category_ids}")
        except Exception as e:
            print(f"[Position_Commands.return_positions] Error fetching banned categories: {e}")
            return

        if ID is None:
            try:
                rearranging_embed = self.create_embed(
                    title="Re-arranging all channels according to the Database...",
                    description="Please wait...",
                    color=random.randint(0, 0xffffff)
                )
                status_message = await ctx.send(embed=rearranging_embed)
                await asyncio.sleep(2)
                
                # Handle channels without a category
                no_category_embed = self.create_embed(
                    title="Re-arranging channels without a category...",
                    description="Updating channel positions...",
                    color=random.randint(0, 0xffffff)
                )
                await status_message.edit(embed=no_category_embed)
                
                no_category_channels = await self.client.db_handler.execute(
                    "SELECT channelID, position FROM categories_channels WHERE categoryID = -1 AND guildID = %s ORDER BY position ASC",
                    ctx.guild.id
                )
                for channel_data in no_category_channels:
                    channel = self.client.get_channel(int(channel_data['channelID']))
                    if channel:
                        print(f"[Position_Commands.return_positions] Updating position for channel without category: {channel.name} to {channel_data['position']}")
                        await channel.edit(position=int(channel_data['position']), category=None)
                        no_category_embed = await self.edit_embed_with_channel(status_message, no_category_embed, channel.name, channel_data['position'])
                        await asyncio.sleep(1)
                
                # Handle categorized channels
                for category in ctx.guild.categories:
                    print(f"[Position_Commands.return_positions] Processing category: {category.name} (ID: {category.id})")
                    if category.id in banned_category_ids:
                        print(f"[Position_Commands.return_positions] Skipping banned category: {category.name}")
                        continue

                    category_embed = self.create_embed(
                        title=f"Re-arranging category {category.name}...",
                        description="Updating channel positions...",
                        color=random.randint(0, 0xffffff)
                    )
                    await status_message.edit(embed=category_embed)
                    
                    category_channels = await self.client.db_handler.execute(
                        "SELECT channelID, position FROM categories_channels WHERE categoryID = %s ORDER BY position ASC",
                        category.id
                    )
                    if not category_channels:
                        print(f"[Position_Commands.return_positions] No positions stored in the database for category: {category.name}")
                        continue

                    channel_positions = [(int(channel['channelID']), int(channel['position'])) for channel in category_channels]
                    for channel_id, position in channel_positions:
                        channel = self.client.get_channel(channel_id)
                        if channel:
                            print(f"[Position_Commands.return_positions] Updating position for channel: {channel.name} to {position}")
                            await channel.edit(position=position, category=category)
                            category_embed = await self.edit_embed_with_channel(status_message, category_embed, channel.name, position)
                            await asyncio.sleep(1)

                    finished_category_embed = self.create_embed(
                        title=f"Finished re-arranging category {category.name}",
                        description="",
                        color=random.randint(0, 0xffffff)
                    )
                    await status_message.edit(embed=finished_category_embed)
                    await asyncio.sleep(2)

                finished_embed = self.create_embed(
                    title="Finished re-arranging all channels",
                    description="",
                    color=random.randint(0, 0xffffff)
                )
                await status_message.edit(embed=finished_embed)
            except Exception as e:
                print(f"[Position_Commands.return_positions] Error re-arranging all channels: {e}")
            return

        try:
            print(f"[Position_Commands.return_positions] Fetching channel or category for ID: {ID}")
            category_or_channel = self.client.get_channel(int(ID))
            print(f"[Position_Commands.return_positions] Found category or channel: {category_or_channel.name} with type {category_or_channel.type} and type is a {type(category_or_channel.type).__name__}")
            if not category_or_channel or (category_or_channel.type == ChannelType.category and category_or_channel.id in banned_category_ids):
                no_category_embed = self.create_embed(
                    title="No category or channel was found with such ID",
                    description="",
                    color=random.randint(0, 0xffffff)
                )
                await ctx.send(embed=no_category_embed)
                print(f"[Position_Commands.return_positions] No category or channel found for ID: {ID}")
                return

            if category_or_channel.type == ChannelType.category:
                print(f"[Position_Commands.return_positions] ID is a category: {category_or_channel.name}")
                rearranging_embed = self.create_embed(
                    title=f"Re-arranging category {category_or_channel.name} according to the Database...",
                    description="Updating channel positions...",
                    color=random.randint(0, 0xffffff)
                )
                status_message = await ctx.send(embed=rearranging_embed)
                await asyncio.sleep(2)

                category_channels = await self.client.db_handler.execute(
                    "SELECT channelID, position FROM categories_channels WHERE categoryID = %s ORDER BY position ASC",
                    category_or_channel.id
                )
                if not category_channels:
                    no_positions_embed = self.create_embed(
                        title="There are no positions stored in the database!",
                        description="",
                        color=random.randint(0, 0xffffff)
                    )
                    await ctx.send(embed=no_positions_embed)
                    print(f"[Position_Commands.return_positions] No positions stored in the database for category: {category_or_channel.name}")
                    return

                channel_positions = [(int(channel['channelID']), int(channel['position'])) for channel in category_channels]
                for channel_id, position in channel_positions:
                    channel = self.client.get_channel(channel_id)
                    if channel:
                        print(f"[Position_Commands.return_positions] Updating position for channel: {channel.name} to {position}")
                        await channel.edit(position=position, category=category_or_channel)
                        rearranging_embed = await self.edit_embed_with_channel(status_message, rearranging_embed, channel.name, position)
                        await asyncio.sleep(1)

                finished_embed = self.create_embed(
                    title=f"Finished re-arranging in {category_or_channel.name}",
                    description="",
                    color=random.randint(0, 0xffffff)
                )
                await status_message.edit(embed=finished_embed)
            else:
                print(f"[Position_Commands.return_positions] ID is a channel: {category_or_channel.name}")
                rearranging_embed = self.create_embed(
                    title=f"Re-arranging channel {category_or_channel.name} according to the Database...",
                    description="Updating channel position...",
                    color=random.randint(0, 0xffffff)
                )
                status_message = await ctx.send(embed=rearranging_embed)
                await asyncio.sleep(2)

                channel_positions = await self.client.db_handler.execute(
                    "SELECT categoryID, position FROM categories_channels WHERE channelID = %s ORDER BY position ASC",
                    category_or_channel.id
                )
                if not channel_positions:
                    no_positions_embed = self.create_embed(
                        title="There are no positions stored in the database!",
                        description="",
                        color=random.randint(0, 0xffffff)
                    )
                    await ctx.send(embed=no_positions_embed)
                    print(f"[Position_Commands.return_positions] No positions stored in the database for channel: {category_or_channel.name}")
                    return

                for channel_position in channel_positions:
                    category_id = channel_position['categoryID']
                    position = channel_position['position']
                    print(f"[Position_Commands.return_positions] Updating position for channel: {category_or_channel.name} to {position}")
                    if category_id == -1:
                        await category_or_channel.edit(position=int(position), category=None)
                    else:
                        await category_or_channel.edit(position=int(position), category=self.client.get_channel(int(category_id)))
                    rearranging_embed = await self.edit_embed_with_channel(status_message, rearranging_embed, category_or_channel.name, position)
                    await asyncio.sleep(1)

                finished_embed = self.create_embed(
                    title=f"Finished re-arranging {category_or_channel.name}",
                    description="",
                    color=random.randint(0, 0xffffff)
                )
                await status_message.edit(embed=finished_embed)
        except Exception as e:
            print(f"[Position_Commands.return_positions] Error re-arranging category or channel {ID}: {e}")

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(Position_Commands(client, db_handler))