import discord


class KeypadButton(discord.ui.Button):
    def __init__(self, label: str, row: int, style: discord.ButtonStyle, custom_id: str = None):
        super().__init__(label=label, row=row, style=style, custom_id=custom_id)
        self.custom_id = custom_id

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: Keypad = self.view
        embed = interaction.message.embeds[0]
        if self.custom_id == 'delete':
            view.pin = view.pin[:-1]
            if not view.pin:
                embed.description = "```\n암호를 입력해주세요.```"
            else:
                embed.description = f"```\n{'*' * (len(view.pin))}```"

        elif self.custom_id == 'complete':
            if not view.pin or len(view.pin) < 4:
                return await interaction.response.send_message("4자리 이상의 PIN 암호를 입력해주세요.", ephemeral=True)
            view.stop()
            embed.description = f"```\n{'*' * 10}```"

        else:
            if view.pin is None:
                view.pin = ""
            view.pin += self.label
            view.current = self.label
            embed.description = f"```\n{'*' * (len(view.pin) - 1)}{view.current}```"

        try:
            return await interaction.response.edit_message(embed=embed, view=view)
        except:
            return


class Keypad(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.pin = None
        self.current = ""

        for i in range(0, 3):
            for j in range(1, 4):
                self.add_item(KeypadButton(label=str(i * 3 + j), style=discord.ButtonStyle.gray, row=i, custom_id=str(i * 3 + j)))
        self.add_item(KeypadButton(label="완료", custom_id="complete", style=discord.ButtonStyle.primary, row=3))
        self.add_item(KeypadButton(label="0", style=discord.ButtonStyle.gray, row=3, custom_id="0"))
        self.add_item(KeypadButton(label="⌫", custom_id="delete", style=discord.ButtonStyle.red, row=3))
