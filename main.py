import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import random


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

players = []

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')

@bot.command()
async def add(ctx, *, args):
    new_players = []

    # Include mentioned users' display names
    for member in ctx.message.mentions:
        name = member.display_name
        if name not in players:
            players.append(name)
            new_players.append(name)

    # Handle comma-separated names not mentioned
    names_from_text = [
        name.strip() for name in args.split(',') if name.strip()
    ]
    for name in names_from_text:
        if name.startswith('<@') and name.endswith('>'):
            continue  # Already processed mentions
        if name not in players:
            players.append(name)
            new_players.append(name)

    if new_players:
        await ctx.send("Added: " + ", ".join(f"**{n}**" for n in new_players))
    else:
        await ctx.send("No new players were added.")

@bot.command()
async def list(ctx):
    if not players:
        await ctx.send("No players added yet.")
    else:
        await ctx.send(f"{len(players)} player(s):\n" + "\n".join(f"- {p}" for p in players))

@bot.command()
async def clear(ctx):
    players.clear()
    await ctx.send("Player list cleared.")

@bot.command(name="del")
async def delete_players(ctx, *, names):
    to_remove = [name.strip() for name in names.split(',') if name.strip()]
    removed = []
    not_found = []

    for name in to_remove:
        if name in players:
            players.remove(name)
            removed.append(name)
        else:
            not_found.append(name)

    msg = ""
    if removed:
        msg += "Removed: " + ", ".join(f"**{n}**" for n in removed) + "\n"
    if not_found:
        msg += "Not found: " + ", ".join(f"**{n}**" for n in not_found)

    await ctx.send(msg if msg else "No valid names provided.")
@bot.command()
async def teams(ctx, num_teams: int):
    if not players:
        await ctx.send("No players to split.")
        return

    if num_teams <= 0:
        await ctx.send("Number of teams must be positive.")
        return

    if num_teams > len(players):
        await ctx.send("Number of teams exceeds number of players.")
        return

    shuffled = players.copy()
    random.shuffle(shuffled)

    # Distribute players into teams
    teams = [[] for _ in range(num_teams)]
    for i, player in enumerate(shuffled):
        teams[i % num_teams].append(player)

    # Format response
    msg = f"**{num_teams} Teams:**\n"
    for idx, team in enumerate(teams, start=1):
        rep = random.choice(team)
        team_list = ", ".join(team)
        msg += f"**Team {idx} ({len(team)}):** {team_list} | Leader: **{rep}**\n"

    await ctx.send(msg)


bot.run(TOKEN)
