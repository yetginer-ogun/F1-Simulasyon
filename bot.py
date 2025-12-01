import os
import asyncio
import discord
from discord.ext import commands
from logic import F1db, monte_carlo_championship


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
db = F1db()

@bot.event
async def on_ready():
    print(f"{bot.user} ready")

@bot.command()
async def help(ctx): #embedding
    await ctx.send("!drivers --> Tüm sürücülerin puanlarını gösterir")


@bot.command()
async def get_drivers(ctx):
    x = db.get_all_drivers()
    for i,driver in enumerate(x):
        await ctx.send(f"{i}.{driver[0]} -- {driver[1]}")


@bot.command()
async def get_races(ctx):
    x = db.get_all_races_names()
    for i,race in enumerate(x):
        await ctx.send(f"{i}.{race}")


@bot.command()
async def driver_ekle(ctx):
    await ctx.send("Eklemek isteiğiniz yarışçının adını girin")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    name = await bot.wait_for('message', check=check)
    name = name.content

    await ctx.send("Eklemek isteiğiniz yarışçının puanını girin")
    points = await bot.wait_for('message', check=check)
    points = points.content

    await ctx.send("Eklemek isteiğiniz yarışçının dnf'ini girin")
    dnf = await bot.wait_for('message', check=check)
    dnf = dnf.content

    db.add_driver(name,points,dnf)
    await ctx.send("Yarışçı eklendi")

@bot.command()
async def race_ekle(ctx):
    await ctx.send("Eklemek isteiğiniz yarışın adını girin")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    name = await bot.wait_for('message', check=check)
    name = name.content

    await ctx.send("Eklemek isteiğiniz yarış sprint mi?")
    cevap = await bot.wait_for('message', check=check)
    cevap = cevap.content
    if cevap == "evet":
        cevap = 1
    else:
        cevap = 0

    db.add_race(name,cevap)
    await ctx.send("Yarış eklendi")


if __name__ == '__main__':
    bot.run("")