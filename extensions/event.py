import time
import sqlite3
from discord.ext import commands


class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.content.startswith('!'):
            return None

        conn = sqlite3.connect('src/data.db')
        cursor = conn.cursor()
        channels = cursor.execute(f'SELECT * FROM channel').fetchall()
        if message.channel.id not in [x[3] for x in channels]:
            return conn.close()

        channel = cursor.execute(f'SELECT * FROM channel WHERE cid = "{message.channel.id}"').fetchone()
        cursor.execute('INSERT INTO data VALUES (?, ?, ?, ?, ?, ?)',
                       [channel[0], channel[1], message.author.id, message.id, message.content, time.time()])
        conn.commit()
        return conn.close()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return None

        conn = sqlite3.connect('src/data.db')
        cursor = conn.cursor()
        channels = cursor.execute(f'SELECT * FROM channel').fetchall()
        if message.channel.id not in [x[3] for x in channels]:
            return conn.close()

        cursor.execute(f'DELETE FROM data WHERE content = "{message.content}"')
        conn.commit()
        return conn.close()

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return None

        if str(before.content) != str(after.content):
            conn = sqlite3.connect('src/data.db')
            cursor = conn.cursor()
            channels = cursor.execute(f'SELECT * FROM channel').fetchall()
            if before.channel.id not in [x[3] for x in channels]:
                return conn.close()

            cursor.execute(f'UPDATE data SET content = "{after.content}" WHERE content = "{before.content}"'
                           f'AND mid = "{after.id}"')
            conn.commit()
            return conn.close()

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        cursor = sqlite3.connect('src/data.db').cursor()
        channels = cursor.execute(f'SELECT * FROM channel WHERE type = "private" AND uid = "{before.id}"').fetchall()
        if not channels:
            return None

        if str(before.status) != str(after.status) and str(after.status) == "offline":
            for c in channels:
                try:
                    channel = self.bot.get_channel(c[3])
                    await channel.delete()
                except:
                    pass


def setup(bot):
    bot.add_cog(Event(bot))
