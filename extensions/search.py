import sqlite3
import discord
from discord.ext import commands
from modules import SearchView


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="검색")
    async def notepad(self, ctx, *, search: str = None):
        if not search:
            return await ctx.reply("사용법: `!검색 {검색어}`")

        cursor = sqlite3.connect("src/data.db").cursor()
        results = cursor.execute(f'SELECT * FROM data WHERE content LIKE "%{search}%"'
                                 f' AND uid = "{ctx.author.id}"').fetchall()

        if not results:
            return await ctx.reply("검색 결과가 없습니다.")

        if len(results) == 1:
            result = results[0]
        else:
            content = ""
            count = 1
            for r in results:
                channel = cursor.execute(f'SELECT * FROM channel WHERE code = "{r[0]}"').fetchone()
                content += f"{count}. {channel[2]}(`{r[0]}`) - {r[4]}\n"
                count += 1

            embed = discord.Embed(title="검색 결과", description=content, color=0x5865F2)
            select = SearchView(results)
            msg = await ctx.reply(embed=embed, view=select)
            await select.wait()
            await msg.delete()

            if select.result is None:
                return None

            result = results[int(select.result[0])]

        types = {
            'notepad': '메모장',
            'private': '비공개 채널'
        }
        c = cursor.execute(f'SELECT * FROM channel WHERE code = "{result[0]}"').fetchone()
        ch = self.bot.get_channel(int(c[3]))
        if not ch:
            ch = c[2]
        else:
            ch = ch.mention

        embed = discord.Embed(title="검색 결과", description=f"**{types[result[1]]}**: {ch}(`{result[0]}`)", color=0x5865F2)
        embed.add_field(name="내용", value=result[4], inline=False)
        embed.add_field(name="작성자", value=f'<@{result[2]}>', inline=True)
        embed.add_field(name="작성 시각", value=f'<t:{int(result[5])}>', inline=True)
        embed.set_footer(icon_url=self.bot.user.avatar.url, text=self.bot.user.name)
        return await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Search(bot))
