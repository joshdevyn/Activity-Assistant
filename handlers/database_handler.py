import aiomysql
from secret import mysql_config

class DatabaseHandler:
    def __init__(self, client):
        self.client = client
        self.db_pool = None

    @classmethod
    async def create(cls, client, mysql_config):
        instance = cls(client)
        instance.db_pool = await aiomysql.create_pool(
            **mysql_config, 
            maxsize=20,  # Adjust maxsize to ensure sufficient connections for high load
            autocommit=True  # Autocommit to avoid uncommitted transactions
        )
        return instance

    async def close_connection(self):
        if self.db_pool:
            self.db_pool.close()
            await self.db_pool.wait_closed()
            self.db_pool = None

    async def reopen_pool(self, mysql_config):
        if self.db_pool is None:
            self.db_pool = await aiomysql.create_pool(
                **mysql_config,
                maxsize=20,
                autocommit=True
            )

    async def setup_db(self):
        # Define the tables to drop (in reverse order of dependency to avoid foreign key constraints issues)
        # Leaving this here just in case you need to drop tables in the future and don't want to have key constraints issues
        # drop_queries = [
        #     "DROP TABLE IF EXISTS keywordPings",
        #     "DROP TABLE IF EXISTS reset_paused",
        #     "DROP TABLE IF EXISTS activeVoiceChannels",
        #     "DROP TABLE IF EXISTS activeTextChannels",
        #     "DROP TABLE IF EXISTS moveBlacklist",
        #     "DROP TABLE IF EXISTS channelsBlacklist",
        #     "DROP TABLE IF EXISTS membersBlacklist",
        #     "DROP TABLE IF EXISTS bannedCategories",
        #     "DROP TABLE IF EXISTS pingME",
        #     "DROP TABLE IF EXISTS categories_channels",
        #     "DROP TABLE IF EXISTS active",
        #     "DROP TABLE IF EXISTS guildLogChannels",
        #     "DROP TABLE IF EXISTS servers",
        # ]

        # Define the tables to create with the correct schema
        create_queries = [
            "CREATE TABLE IF NOT EXISTS servers (guildID bigint PRIMARY KEY)",
            "CREATE TABLE IF NOT EXISTS guildLogChannels (guildID bigint PRIMARY KEY, logChannelID bigint)",
            "CREATE TABLE IF NOT EXISTS active (guildID bigint PRIMARY KEY, categoryID bigint, channelID bigint, messages text, timer text, remove text)",
            "CREATE TABLE IF NOT EXISTS categories_channels (guildID bigint, categoryID bigint, channelID bigint, position int, PRIMARY KEY(guildID, categoryID, channelID))",
            "CREATE TABLE IF NOT EXISTS pingME (guildID bigint, channelID bigint, memberID bigint, PRIMARY KEY(guildID, channelID, memberID))",
            "CREATE TABLE IF NOT EXISTS bannedCategories (guildID bigint, categoryID bigint, PRIMARY KEY(guildID, categoryID))",
            "CREATE TABLE IF NOT EXISTS membersBlacklist (guildID bigint, memberID bigint, PRIMARY KEY(guildID, memberID))",
            "CREATE TABLE IF NOT EXISTS channelsBlacklist (guildID bigint, channelID bigint, PRIMARY KEY(guildID, channelID))",
            "CREATE TABLE IF NOT EXISTS moveBlacklist (guildID bigint, channelID bigint, PRIMARY KEY(guildID, channelID))",
            "CREATE TABLE IF NOT EXISTS activeTextChannels (guildID bigint, channelID bigint, categoryID bigint, PRIMARY KEY(guildID, channelID))",
            "CREATE TABLE IF NOT EXISTS activeVoiceChannels (guildID bigint, channelID bigint, categoryID bigint, PRIMARY KEY(guildID, channelID))",
            "CREATE TABLE IF NOT EXISTS reset_paused (guildID bigint PRIMARY KEY, is_paused boolean DEFAULT false)",
            "CREATE TABLE IF NOT EXISTS keywordPings (guildID bigint, memberID bigint, keyword varchar(255), PRIMARY KEY (guildID, memberID, keyword))"
        ]

        async with self.db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                # Execute drop queries to clean up existing tables
                # for query in drop_queries:
                #     try:
                #         await cursor.execute(query)
                #     except Exception as e:
                #         print(f"An error occurred while dropping tables: {e}")
                
                # Execute create queries to establish fresh tables with correct schema
                for query in create_queries:
                    try:
                        await cursor.execute(query)
                    except Exception as e:
                        print(f"An error occurred while creating tables: {e}")
                await connection.commit()  # Commit changes after all queries 
        
                await self.insert_default_active_rows(self.client)

    async def insert_default_active_rows(self, client):
        default_category_id = 0
        default_messages = "5"
        default_timer = "300"
        default_remove = "900"

        for guild in client.guilds:
            log_channel_id = 0  # Assuming a default or fetched log channel ID

            insert_query = """
            INSERT INTO active (guildID, categoryID, channelID, messages, timer, remove)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                guildID=VALUES(guildID),
                categoryID=categoryID,
                channelID=channelID,
                messages=messages,
                timer=timer,
                remove=remove;
            """

            async with self.db_pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    try:
                        await cursor.execute(insert_query, (guild.id, default_category_id, log_channel_id, default_messages, default_timer, default_remove))
                        await cursor.connection.commit()
                    except Exception as e:
                        print(f"Failed to insert/update active row for guild {guild.id}: {e}")

    async def fetch_log_channel_id(self, guild_id):
        query = "SELECT channelID FROM active WHERE guildID = %s"
        async with self.db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query, (guild_id))
                result = await cursor.fetchone()
                return result[0] if result else None

    async def set_log_channel_id(self, guild_id, log_channel_id):
        query = """
            INSERT INTO active (guildID, channelID)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE channelID = VALUES(channelID)
        """
        async with self.db_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query, (guild_id, log_channel_id))
                await connection.commit()

    async def execute(self, query, params=None):
        try:
            if self.db_pool is None:
                await self.reopen_pool(mysql_config)  # Ensure the pool is open

            async with self.db_pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    print(f"[DatabaseHandler.execute] Preparing to execute query: {query} with params: {params}")
                    await cursor.execute(query, params)
                    if query.strip().upper().startswith("SELECT"):
                        print("[DatabaseHandler.execute] Fetching results from SELECT query...")
                        results = await cursor.fetchall()
                        if not results:  # No results found
                            print("[DatabaseHandler.execute] No results found for SELECT query.")
                            return []  # Or return [] if an empty list is preferable
                        elif len(results) == 1:
                            single_result = results[0]
                            if isinstance(single_result, tuple) and len(single_result) == 1:
                                # Single result, single column (tuple)
                                print(f"[DatabaseHandler.execute] A single result (single column) found: {single_result[0]}")
                                return [single_result[0]]
                            else:
                                # Single result, potentially multiple columns (dict or tuple)
                                print(f"[DatabaseHandler.execute] A single result found: {single_result}")
                                return [single_result]
                        else:
                            print(f"[DatabaseHandler.execute] Multiple results found: {results}")
                            return results
                    else:
                        print("[DatabaseHandler.execute] Non-SELECT query executed, committing changes...")
                        await connection.commit()
        except Exception as e:
            print(f"[DatabaseHandler.execute] An error occurred during database interaction: {e}")
            raise  # Re-raise the exception for further handling

    async def set_reset_paused(self, guild_id, is_paused):
        query = """
        INSERT INTO reset_paused (guildID, is_paused)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE is_paused = VALUES(is_paused)
        """
        await self.execute(query, (guild_id, is_paused))

    async def get_reset_paused(self, guild_id):
        query = "SELECT is_paused FROM reset_paused WHERE guildID = %s"
        result = await self.execute(query, (guild_id,))
        return result[0]['is_paused'] if result else False
