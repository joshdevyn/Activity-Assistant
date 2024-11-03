from activityAssistantCogs.Config.activityAssistantConfig import * # Cog-wide configurations go here
import discord # Client requires this
from discord.ext import commands # Commands require this
from handlers.database_handler import DatabaseHandler # Interactions with the database are handled here
### Add/Remove imports as needed ###

class <YourCogHere>(commands.Cog):
    def __init__(self, client, db_handler):
        self.client = client
        self.db_handler = db_handler

    @commands.Cog.listener()
    async def on_ready(self):
        print('<YourCogHere> is ready!')

    async def setup(client):
        db_handler = await DatabaseHandler.create(client, mysql_config)
        await client.add_cog(Utility(client, db_handler))

    ### Write your implementation here ###

async def setup(client):
    db_handler = client.db_handler
    await client.add_cog(<YourCogHere>(client, db_handler))
