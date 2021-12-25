import asyncio
import sqlite3
import time

import discord
from discord.ext import commands, tasks
from datetime import datetime
from modules import get_time, Confirm, generate


class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check.start()

    @tasks.loop(minutes=1)
    async def check(self):
        await self.bot.wait_until_ready()

        conn = sqlite3.connect('src/data.db')
        cursor = conn.cursor()
        reminders = cursor.execute('SELECT * FROM reminder').fetchall()

        now = time.time()
        for r in reminders:
            try:
                channel = self.bot.get_channel(r[2])
                msg = await channel.fetch_message(r[4])
            except AttributeError:
                cursor.execute(f'DELETE FROM reminder WHERE id = "{r[0]}"')
                conn.commit()
                continue

            convert = {
                300: '5분',
                1800: '30분',
                3600: '1시간',
                21600: '6시간',
                86400: '1일',
                259200: '3일',
            }

            if r[3] - now <= 0:
                await msg.delete()

                embed = discord.Embed(title=f"`{r[5]}` 일정 마감 안내", color=0x5865F2,
                                      description=f"`{r[0]}` 일정이 마감되었습니다.")
                embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
                await channel.send(embed=embed)

                cursor.execute(f'DELETE FROM reminder WHERE id = "{r[0]}"')
                conn.commit()

            for t in [300, 1800, 3600, 21600, 86400, 259200]:
                if t - 30 < r[3] - now < t + 30:
                    embed = discord.Embed(title=f"`{r[5]}` 일정 안내", color=0x5865F2,
                                          description=f"`{r[0]}` 일정 마감까지 약 {convert[t]} 남았습니다.")
                    embed.add_field(name="마감 시각", value=f"<t:{r[3]}>")
                    embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
                    embed.set_thumbnail(url=self.bot.user.avatar.url)
                    await channel.send(embed=embed)

    @commands.group(name='일정')
    async def reminder(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.reply("사용법: `!일정 {생성/삭제/목록}`")

    @reminder.command(name='생성')
    async def create(self, ctx, channel: str = None):
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        if not channel:
            return await ctx.reply("사용법: `!일정 생성 [채널]`")

        channels = [c for c in ctx.guild.channels if str(c.id) == channel.strip('<#>')]
        if not channels:
            return await ctx.reply("존재하지 않는 채널입니다.")

        embed = discord.Embed(description="일정의 제목을 입력해주세요.", color=0x5865F2)
        msg = await ctx.reply(embed=embed)
        try:
            title = await self.bot.wait_for('message', timeout=60, check=check)
        except asyncio.TimeoutError:
            return await msg.delete()

        await msg.delete()
        await title.delete()

        try:
            year, month, day, hour, minute = await get_time(self.bot, ctx)
        except:
            return await ctx.reply("마감 시각을 올바르게 입력해주세요.")

        embed = discord.Embed(title="일정을 등록하시겠습니까?", color=0x5865F2,
                              description=f"마감일: `{year}년 {month}월 {day}일`\n"
                                          f"마감 시각: `{hour}시 {minute}분`\n"
                                          f"등록 채널: {channels[0].mention}")
        confirm = Confirm(ctx)
        msg = await ctx.reply(embed=embed, view=confirm)
        await confirm.wait()
        if confirm.value is False:
            return await ctx.reply("일정 생성이 취소되었습니다.")
        if confirm.value is None:
            return await ctx.reply("시간이 초과되었습니다.")

        await msg.delete()
        await ctx.reply("일정을 추가합니다.")

        try:
            until = datetime.strptime(f'{year}-{month}-{day} {hour}:{minute}', "%Y-%m-%d %H:%M")
        except ValueError:
            return await ctx.reply("오류가 발생하였습니다. 값을 제대로 입력하였는지 확인해주세요.")
        timestamp = datetime.timestamp(until)
        remain = timestamp - time.time()

        if remain <= 0:
            return await ctx.reply("일정 마감 시각이 이미 지났습니다.")

        conn = sqlite3.connect('src/data.db')
        cursor = conn.cursor()
        codes = [c[0] for c in cursor.execute(f'SELECT * FROM reminder').fetchall()]

        code = generate(5)
        while code in codes:
            code = generate(5)

        c = channels[0]

        embed = discord.Embed(title=f"{title.content}", color=0x5865F2)
        embed.add_field(name="마감 시각", value=f"`{year}년 {month}월 {day}일 {hour}시 {minute}분`", inline=False)
        embed.add_field(name="남은 시간", value=f"<t:{int(timestamp)}:R>", inline=False)
        embed.add_field(name="고유 코드", value=f"`{code}`")
        embed.add_field(name="생성", value=ctx.author.mention)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        msg = await c.send(embed=embed)
        await msg.pin()

        cursor.execute('INSERT INTO reminder VALUES (?, ?, ?, ?, ?, ?, ?)', [code, ctx.guild.id, c.id, timestamp, msg.id, title.content, ctx.author.id])
        conn.commit()
        conn.close()

        embed = discord.Embed(color=0x5865F2, description=f"일정 생성이 완료되었습니다. [바로가기]({msg.jump_url})")
        return await ctx.reply(embed=embed)

    @reminder.command(name='삭제')
    async def delete(self, ctx, code: str = None):
        if not code:
            return await ctx.reply("사용법: `!일정 삭제 [코드]`")

        conn = sqlite3.connect('src/data.db')
        cursor = conn.cursor()
        c = cursor.execute(f'SELECT * FROM reminder WHERE id = "{code}"').fetchone()

        if not c:
            return await ctx.reply("코드와 일치하는 일정이 존재하지 않습니다.")

        channel = self.bot.get_channel(c[2])
        msg = await channel.fetch_message(c[4])
        user = ctx.guild.get_member(c[6])

        if user.id != ctx.author.id:
            return await ctx.reply("이 일정을 삭제할 권한이 없습니다.")

        await msg.delete()
        cursor.execute(f'DELETE FROM reminder WHERE id = "{code}"')
        conn.commit()
        conn.close()

        return await ctx.reply(f"`{code}` 일정이 삭제되었습니다.")

    @reminder.command(name='목록')
    async def _list(self, ctx):
        cursor = sqlite3.connect('src/data.db').cursor()
        reminders = cursor.execute(f'SELECT * FROM reminder WHERE guild = "{ctx.guild.id}" ORDER BY timestamp ASC').fetchall()

        if len(reminders) == 0:
            return await ctx.reply("일정이 없습니다.")

        content = ''
        for r in reminders:
            channel = self.bot.get_channel(r[2])
            msg = await channel.fetch_message(r[4])
            content += f'{r[5]}(`{r[0]}`): {channel.mention} - [바로가기]({msg.jump_url})\n'

        embed = discord.Embed(title="일정 목록", description=content, color=0x5865F2)
        return await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Reminder(bot))
