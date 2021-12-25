import sqlite3
import discord


class DeleteView(discord.ui.View):
    def __init__(self, bot, code: str):
        super().__init__()
        self.add_item(Delete(bot, code))


class Delete(discord.ui.Select):
    def __init__(self, bot, code):
        self.bot = bot
        self.code = code
        select_options = [discord.SelectOption(label='취소', value='cancel', emoji="❌"),
                          discord.SelectOption(label='채널', value='channel', emoji="📺",
                                               description='채널을 삭제합니다.'
                                                           '\n채널에 있는 메시지는 삭제되지만, 데이터베이스에 저장된 데이터는 보존됩니다.'),
                          discord.SelectOption(label='메시지', value='message', emoji="💬",
                                               description="채널의 메시지를 삭제합니다.\n채널과 데이터베이스에 저장된 데이터는 보존됩니다."),
                          discord.SelectOption(label='데이터', value='data', emoji="📊",
                                               description="데이터베이스에 저장된 데이터를 삭제합니다.\n채널과 채널에 있는 메시지는 보존됩니다.")]
        super().__init__(placeholder="삭제 대상을 선택해주세요. (중복선택 가능)",
                         min_values=1, max_values=len(select_options), options=select_options)

    async def callback(self, interaction: discord.Interaction):
        conn = sqlite3.connect('src/data.db')
        cursor = conn.cursor()
        channel = cursor.execute(f'SELECT * FROM channel WHERE code = "{self.code}"').fetchone()

        for v in self.values:
            try:
                if v == 'cancel':
                    await interaction.message.delete()
                    return await interaction.response.send_message("삭제를 취소하였습니다.")
                elif v == 'message':
                    c = self.bot.get_channel(channel[3])
                    await c.purge(limit=None)
                elif v == 'channel':
                    c = self.bot.get_channel(channel[3])
                    await c.delete()
                else:
                    cursor.execute(f'DELETE FROM channel WHERE code = "{self.code}"')
                    cursor.execute(f'DELETE FROM data WHERE code = "{self.code}"')
                    conn.commit()
            except:
                pass

        conn.close()
        options_str = [o.label for o in self.options if o.value in self.values]
        embed = discord.Embed(title="삭제 완료", color=0x5865F2,
                              description=f"선택하신 채널의 {', '.join(options_str)}(을)를 삭제했습니다.")
        return await interaction.response.send_message(embed=embed)
