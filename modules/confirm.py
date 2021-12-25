import discord


class Confirm(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.value = None
        self.ctx = ctx

    @discord.ui.button(label='예', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.ctx.author and interaction.channel == interaction.message.channel:
            self.value = True
            self.stop()

    @discord.ui.button(label='아니오', style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.ctx.author and interaction.channel == interaction.message.channel:
            self.value = False
            self.stop()
