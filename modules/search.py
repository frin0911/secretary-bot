import discord


class SearchView(discord.ui.View):
    def __init__(self, results: list):
        super().__init__()
        self.result = None
        self.add_item(Search(results))


class Search(discord.ui.Select):
    def __init__(self, results):
        select_options = [discord.SelectOption(label=f"{i}. {results[i - 1][4]}", value=str(i - 1))
                          for i in range(1, len(results) + 1)]
        super().__init__(placeholder="검색 결과를 선택해주세요.",
                         min_values=1, max_values=1, options=select_options)

    async def callback(self, interaction: discord.Interaction):
        view: SearchView = self.view
        view.result = self.values
        self.view.stop()
