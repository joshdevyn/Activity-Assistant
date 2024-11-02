from activityAssistantCogs.Config.activityAssistantConfig import *
import discord
from discord.ext import commands
from handlers.database_handler import DatabaseHandler
import numpy as np
from secret import mysql_config

class Utility(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    @commands.Cog.listener()
    async def on_ready(self):
        print('Utility is ready!')

    async def setup(client):
        db_handler = await DatabaseHandler.create(client, mysql_config)
        await client.add_cog(Utility(client, db_handler))

    def create_progress_bar(current, total, bar_length=20):
        progress = float(current) / float(total)
        # Use the Unicode spade symbol directly without the emoji presentation
        arrow = '\u2660' * int(round(progress * bar_length) - 1)
        spaces = '-' * (bar_length - len(arrow))
        return f"[{arrow}{spaces}]"