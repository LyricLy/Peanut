import asyncio
import subprocess
import traceback
import time
import os
import sys
import re

import discord
from discord.ext import commands

from data import Data


ID = re.compile("([A-HJ-NP-Y0-9]{3}-){2}[A-HJ-NP-Y0-9]{3}")

if not os.getcwd().endswith("Peanut"):
    os.chdir(os.path.dirname(__file__))

bot = commands.Bot(command_prefix=commands.when_mentioned_or("p!"), description="Invoke me with `p!<command>`.")


bot.data = Data("config.json", timer=3600, duration=86400)
bot.theme = None
bot.channel = None
bot.end = None


@bot.event
async def on_ready():
    print(f"Ready on {bot.user}")
    print(f"ID: {bot.user.id}")
    print("---")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send("You messed up writing the command.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        if hasattr(error, "original"):
            error = error.original
        await ctx.send(discord.utils.escape_mentions(
             f"Something went wrong. ``{type(error).__name__}: {discord.utils.escape_markdown(str(error))}``"
        ))
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

@bot.command()
@commands.is_owner()
async def update(ctx):
    subprocess.call(["git", "pull"])
    await bot.close()

@bot.command()
async def join(ctx):
    if not bot.theme:
        return await ctx.send("No jam is running currently.")
    elif ctx.author in bot.players:
        return await ctx.send("You are already participating or have already participated in this jam.")

    try:
        await ctx.author.send(f"The theme is {bot.theme}. Once done, send the level ID in this DM.")
    except discord.Forbidden:
        return await ctx.send("Unable to send DM. Please check your DM settings and try again.")

    bot.players.append(ctx.author)
    try:
        message = await bot.wait_for(
            "message",
            check=lambda m: m.channel.type == discord.ChannelType.private and m.author == ctx.author and re.match(ID, m.content),
            timeout=bot.data.timer
        )
    except asyncio.TimeoutError:
        return await ctx.author.send("You ran out of time. Consult a coordinator of the jam to submit levels after the deadline.")

    await ctx.author.send("Roger that.")
    await bot.channel.send(f"{ctx.author}: {message.content}")

@bot.command()
async def remaining(ctx):
    if not bot.theme:
        return await ctx.send("No jam is running currently.")
    seconds = int(bot.end - time.time())
    await ctx.send(f"{seconds} seconds (about {seconds // 60} minutes) are remaining in the current level jam.")


@bot.group(invoke_without_command=True)
@commands.has_any_role(630717723051032606, 624188805376770059)
async def eventmod(ctx):
    await ctx.send_help(ctx.command)

@eventmod.command()
async def start(ctx, theme):
    await ctx.message.delete()
    bot.players = []
    bot.theme = theme.strip("| ")
    bot.channel = ctx.channel
    await ctx.send(f"Beginning a jam that will end in roughly {bot.data.duration // 60} minutes.")
    bot.end = time.time() + bot.data.duration
    await asyncio.sleep(bot.data.duration)
    if bot.theme:
        await ctx.send("Jam has ended.")
        bot.theme = None

@eventmod.command()
async def stop(ctx):
    if bot.theme:
        bot.theme = None
        for player in bot.players:
            await player.send("The jam has been ended early. Sorry!")
        await ctx.send("Jam has been ended. All participants have been notified.")
    else:
        await ctx.send("No jam is running currently.")

@eventmod.command()
async def timer(ctx, seconds: int):
    bot.data.timer = seconds
    await ctx.send(f"Set time to finish jam to {seconds} seconds (about {seconds // 60} minutes).")

@eventmod.command()
async def duration(ctx, seconds: int):
    bot.data.duration = seconds
    await ctx.send(f"Set total duration of jam to {seconds} seconds (about {seconds // 60} minutes).")


try:
    with open("token.txt") as f:
        bot.run(f.read()[:-1])
finally:
    bot.data.save()
