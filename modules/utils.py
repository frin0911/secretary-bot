import asyncio
import random
import string
import discord
from datetime import datetime


def generate(digits: int = 10):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(digits))


async def get_time(bot, ctx):
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    embed = discord.Embed(title="마감일을 입력해주세요.", color=0x57F287,
                          description="다음 형식 중 하나를 골라 입력해주세요.\n"
                                      "1. `2021/01/01` 또는 `2021/1/1`\n"
                                      "2. `2021년 01월 01일` 또는 `2021년 1월 1일`\n"
                                      "3. `2021.01.01.` 또는 `2021.1.1`\n"
                                      "4. `20210101`\n"
                                      "5. `오늘` (`오늘`만 가능. 내일, 어제 등은 해당안됨.)")
    msg = await ctx.reply(embed=embed)
    try:
        respond = await bot.wait_for('message', timeout=60, check=check)
    except asyncio.TimeoutError:
        await msg.delete()
        return None

    await msg.delete()
    await respond.delete()

    content = respond.content.replace(' ', '')

    if '/' in content:
        y, m, d = content.split('/')
    elif '.' in content:
        y, m, d = content.split('.')
    elif '년' in content:
        y = content.split('년')[0]
        temp = content.replace(f'{y}년', '')
        m = temp.split('월')[0]
        d = temp.replace(f'{m}월', '').split('일')[0]
    elif respond.content == '오늘':
        now = datetime.now()
        y, m, d = now.year, now.month, now.day
    else:
        y, m, d = respond.content[:4], respond.content[4:6], respond.content[6:]

    if len(str(m)) == 1:
        m = f'0{m}'
    if len(str(d)) == 1:
        d = f'0{d}'

    date = f'{y}{m}{d}'
    if len(date) != 8:
        return None

    try:
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:])
    except ValueError:
        return None

    embed = discord.Embed(title="마감 시각을 입력해주세요.", color=0x57F287,
                          description="다음 형식 중 하나를 골라 입력해주세요.\n"
                                      "1. `01:05` 또는 `1:5`/`17:15` \n"
                                      "2. `01시 05분` 또는 `1시 5분`/`17시 15분`\n"
                                      "3. `0105`/`1715`")
    msg = await ctx.reply(embed=embed)
    try:
        respond = await bot.wait_for('message', timeout=60, check=check)
    except asyncio.TimeoutError:
        await msg.delete()
        return None

    await msg.delete()
    await respond.delete()

    content = respond.content.replace(' ', '')

    if ':' in content:
        h, m = content.split(':')
    elif '시' in content:
        h = content.split('시')[0]
        m = content.replace(f'{h}시', '').split('분')[0]
    else:
        h, m = content[:2], content[2:]

    time = f'{h}{m}'
    if len(time) != 4:
        return None

    try:
        hour = int(time[:2])
        minute = int(time[2:])
    except ValueError:
        return None

    return year, month, day, hour, minute
