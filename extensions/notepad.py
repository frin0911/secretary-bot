import sqlite3
import discord
from discord.ext import commands
from modules import Confirm, generate, DeleteView


class Notepad(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="메모장")
    async def notepad(self, ctx):
        if ctx.invoked_subcommand is None:
            return await ctx.reply("사용법: `!메모장 {생성/삭제/병합/로드}`")

    @notepad.command(name="생성")
    async def create(self, ctx, *, name: str = None):
        if name is None:
            name = "이름 없는 메모장"

        embed = discord.Embed(title="메모장을 생성하시겠습니까?", color=0x5865F2,
                              description=f"확인 버튼을 누르시면 이 카테고리에 `{name}`(이)라는 이름의 채널이 개설됩니다.\n"
                                          "해당 채널에서 작성하신 모든 메시지는 데이터베이스에 저장됩니다.")
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        confirm = Confirm(ctx)
        msg = await ctx.reply(embed=embed, view=confirm)
        await confirm.wait()
        await msg.delete()

        if confirm.value is False:
            return await ctx.reply("메모장 생성이 취소되었습니다.")
        if confirm.value is None:
            return await ctx.reply("시간이 초과되었습니다.")

        category = ctx.channel.category or ctx.guild

        conn = sqlite3.connect("src/data.db")
        cursor = conn.cursor()

        code = generate(5)
        while cursor.execute('SELECT * FROM channel WHERE code = "{}"').fetchone():
            code = generate(5)

        try:
            channel = await category.create_text_channel(name, topic=f"고유 식별 코드: {code}")
        except discord.Forbidden:
            conn.close()
            return await ctx.reply("권한이 부족합니다.")

        cursor.execute('INSERT INTO channel VALUES (?, ?, ?, ?, ?, ?)', [code, 'notepad', name, channel.id, ctx.author.id, None])
        conn.commit()
        conn.close()

        embed = discord.Embed(title="메모장 생성 완료", color=0x5865F2,
                              description=f"`{name}` 메모장이 생성되었습니다.\n채널: {channel.mention}.\n")
        await ctx.reply(embed=embed)

        embed = discord.Embed(title="메모장 생성 완료", color=0x5865F2,
                              description=f"`{name}` 메모장이 생성되었습니다.\n이 채널에서 작성하는 메시지는 기록됩니다.\n"
                                          f"고유 식별 코드: `{code}`")
        return await channel.send(ctx.author.mention, embed=embed)

    @staticmethod
    async def memo_list(ctx):
        conn = sqlite3.connect("src/data.db")
        cursor = conn.cursor()
        channels = cursor.execute(f'SELECT * FROM channel WHERE uid = "{ctx.author.id}" AND type = "notepad"').fetchall()
        content = ""
        for c in channels:
            content += f"- **{c[2]}**: `{c[0]}`\n"

        if content == "":
            await ctx.reply("메모장이 존재하지 않습니다.")
            return ()
        conn.close()
        return content

    @notepad.command(name="삭제")
    async def delete(self, ctx, code: str = None):
        content = await self.memo_list(ctx)
        if not content:
            return None

        if not code:
            embed = discord.Embed(title="사용법: `!메모장 삭제 [코드]`", color=0x5865F2, description=content)
            return await ctx.reply(embed=embed)

        cursor = sqlite3.connect("src/data.db").cursor()
        channel = cursor.execute(f'SELECT * FROM channel WHERE code = "{code}" AND type = "notepad"').fetchone()
        if not channel:
            return await ctx.reply("존재하지 않는 코드입니다.")

        embed = discord.Embed(title="메모장을 삭제하시겠습니까?", color=0x5865F2,
                              description="메시지 하단의 드롭다운으로 삭제할 데이터를 선택해주세요.(중복선택 가능)")
        embed.add_field(name="📺 채널", value="채널을 삭제합니다.\n채널에 있는 메시지는 삭제되지만, 데이터베이스에 저장된 데이터는 보존됩니다.")
        embed.add_field(name="💬 메시지", value="채널의 메시지를 삭제합니다.\n채널과 데이터베이스에 저장된 데이터는 보존됩니다.", inline=False)
        embed.add_field(name="📊 데이터", value="데이터베이스에 저장된 데이터를 삭제합니다.\n채널과 채널에 있는 메시지는 보존됩니다.")
        return await ctx.reply(embed=embed, view=DeleteView(self.bot, code))

    @notepad.command(name="병합")
    async def combine(self, ctx, code_a: str = None, code_b: str = None):
        content = await self.memo_list(ctx)
        if not content:
            return None

        if not code_a or not code_b:
            embed = discord.Embed(title="사용법: `!메모장 병합 [코드 A] [코드 B]`", color=0x5865F2, description=content)
            return await ctx.reply(embed=embed)

        conn = sqlite3.connect('src/data.db')
        cursor = conn.cursor()

        channel_a = cursor.execute(f'SELECT * FROM channel WHERE code = "{code_a}" AND type = "notepad"').fetchone()
        channel_b = cursor.execute(f'SELECT * FROM channel WHERE code = "{code_b}" AND type = "notepad"').fetchone()
        if not channel_a or not channel_b:
            return await ctx.reply("존재하지 않는 코드입니다.")

        if code_a == code_b:
            return await ctx.reply("동일한 코드를 입력할 수 없습니다.")

        embed = discord.Embed(title="메모장을 병합하시겠습니까?", color=0x5865F2,
                              description=f"{channel_a[2]}(`{channel_a[0]}`)(을)를 {channel_b[2]}(`{channel_b[0]}`)에 병합합니다.")
        confirm = Confirm(ctx)
        msg = await ctx.reply(embed=embed, view=confirm)
        await confirm.wait()
        if confirm.value is False:
            conn.close()
            return await ctx.reply("메모장 병합이 취소되었습니다.")
        if confirm.value is None:
            conn.close()
            return await ctx.reply("시간이 초과되었습니다.")

        await msg.delete()
        embed = discord.Embed(title="기존 데이터를 삭제하시겠습니까?", color=0x5865F2,
                              description=f"{channel_a[2]}(`{channel_a[0]}`)에 있는 데이터가 병합됨에 따라 영구히 삭제됩니다.\n"
                                          "유지를 선택하시면 데이터가 백업됩니다.")
        backup = Confirm(ctx)
        msg = await ctx.reply(embed=embed, view=backup)
        await backup.wait()

        if backup.value is not None:
            existing = cursor.execute(f'SELECT * FROM data WHERE code = "{code_a}"').fetchall()
            cursor.execute(f'UPDATE data SET code = "{code_b}" WHERE code = "{code_a}"')
            if backup.value is False:
                cursor.executemany("INSERT INTO data VALUES (?, ?, ?, ?, ?, ?)", existing)
            else:
                cursor.execute(f'DELETE FROM channel WHERE code = "{code_a}"')
        else:
            conn.close()
            return await ctx.reply("시간이 초과되었습니다.")
        conn.commit()
        conn.close()

        await msg.delete()
        embed = discord.Embed(title="메모장 병합 완료", color=0x5865F2,
                              description=f"{channel_a[2]}(`{channel_a[0]}`)(을)를 {channel_b[2]}(`{channel_b[0]}`)에 병합하였습니다.")
        return await ctx.reply(embed=embed)

    @notepad.command(name="로드")
    async def load(self, ctx, code: str = None):
        content = await self.memo_list(ctx)
        if not content:
            return None

        if not code:
            embed = discord.Embed(title="사용법: `!메모장 로드 [코드]`", color=0x5865F2, description=content)
            return await ctx.reply(embed=embed)

        conn = sqlite3.connect("src/data.db")
        cursor = conn.cursor()
        channel = cursor.execute(f'SELECT * FROM channel WHERE code = "{code}" AND type = "notepad"').fetchone()
        if not channel:
            return await ctx.reply("존재하지 않는 코드입니다.")

        cursor.execute(f'UPDATE channel SET cid = "{ctx.channel.id}" WHERE code = "{code}"')
        conn.commit()

        webhook = await ctx.channel.create_webhook(name=self.bot.user.name)

        for d in cursor.execute(f'SELECT * FROM data WHERE code = "{code}"').fetchall():
            user = self.bot.get_user(d[2])
            await webhook.send(d[4], username=user.name, avatar_url=user.avatar.url)

        conn.close()
        embed = discord.Embed(title="메모장 로드 완료", color=0x5865F2,
                              description=f"{channel[2]}(`{channel[0]}`)(을)를 불러왔습니다.\n"
                                          f"이제 이 채널에서 작성하는 메시지는 기록됩니다.")
        return await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Notepad(bot))
