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
async def add(ctx, *, args: str = ""):
    try:
        if not ctx.message.mentions:
            await ctx.send("Please mention users to add. Example: `!add @user1 @user2`")
            return
        new_players = []
        # Only include mentioned users' display names
        for member in ctx.message.mentions:
            name = member.display_name
            if name not in players:
                players.append(name)
                new_players.append(name)
        if new_players:
            await ctx.send("Added: " + ", ".join(f"**{n}**" for n in new_players))
        else:
            await ctx.send("No new players were added.")
    except Exception as e:
        await ctx.send(f"An error occurred in add: {e}")

@bot.command()
async def list(ctx):
    try:
        if not players:
            await ctx.send("No players added yet.")
        else:
            await ctx.send(f"{len(players)} player(s):\n" + "\n".join(f"- {p}" for p in players))
    except Exception as e:
        await ctx.send(f"An error occurred in list: {e}")

@bot.command()
async def clear(ctx):
    try:
        players.clear()
        await ctx.send("Player list cleared.")
    except Exception as e:
        await ctx.send(f"An error occurred in clear: {e}")

@bot.command(name="del")
async def delete_players(ctx, *, names: str = ""):
    try:
        if not names.strip():
            await ctx.send("Please provide player names to delete. Example: `!del user1, user2`")
            return
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
    except Exception as e:
        await ctx.send(f"An error occurred in del: {e}")
@bot.command()
async def teams(ctx, num_teams: int = None):
    try:
        if not players:
            await ctx.send("No players to split.")
            return

        if num_teams is None:
            await ctx.send("Please specify the number of teams. Example: `!teams 2`")
            return

        if not isinstance(num_teams, int) or num_teams <= 0:
            await ctx.send("Number of teams must be a positive integer.")
            return

        if num_teams > len(players):
            await ctx.send("Number of teams exceeds number of players.")
            return

        shuffled = players.copy()
        random.shuffle(shuffled)

        teams = [[] for _ in range(num_teams)]
        for i, player in enumerate(shuffled):
            teams[i % num_teams].append(player)

        msg = f"**{num_teams} Teams:**\n"
        for idx, team in enumerate(teams, start=1):
            if not team:
                msg += f"**Team {idx} (0):** _No players_\n"
                continue
            rep = random.choice(team)
            team_list = ", ".join(team)
            msg += f"**Team {idx} ({len(team)}):** {team_list} | Leader: **{rep}**\n"

        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@bot.command()
@commands.has_guild_permissions(move_members=True)
async def move(ctx, *, args: str = ""):
    try:
        if not args.strip():
            await ctx.send("Usage: !move @user1 @user2 #roomx @user3 #roomy ...")
            return
        tokens = args.split()
        teams = []
        current_team = {'members': [], 'channel': None}
        for token in tokens:
            if token.startswith('<#') and token.endswith('>'):
                if not current_team['members']:
                    await ctx.send("Malformed command: No users specified before channel. Usage: !move @user1 @user2 #roomx ...")
                    return
                if current_team['channel'] is not None:
                    await ctx.send("Malformed command: Multiple channels specified for one team.")
                    return
                current_team['channel'] = token
                teams.append(current_team)
                current_team = {'members': [], 'channel': None}
            elif token.startswith('<@') and token.endswith('>'):
                current_team['members'].append(token)
            else:
                continue
        # If last team is not added
        if current_team['members'] and current_team['channel']:
            teams.append(current_team)
        elif current_team['members'] and not current_team['channel']:
            await ctx.send("Malformed command: Team without a channel at the end. Usage: !move @user1 @user2 #roomx ...")
            return
        if not teams:
            await ctx.send("No valid teams or channels found. Usage: !move @user1 @user2 #roomx ...")
            return
        moved = []
        not_in_voice = []
        not_found = []
        not_voice_channel = []
        for team in teams:
            try:
                channel_id = int(team['channel'][2:-1])
                channel = ctx.guild.get_channel(channel_id)
                if not channel:
                    not_voice_channel.append(team['channel'])
                    continue
                if not isinstance(channel, discord.VoiceChannel):
                    not_voice_channel.append(f"<#{channel_id}>")
                    continue
                for mention in team['members']:
                    try:
                        user_id = int(mention[2:-1])
                        member = ctx.guild.get_member(user_id)
                        if not member:
                            not_found.append(mention)
                            continue
                        if not member.voice or not member.voice.channel:
                            not_in_voice.append(member.display_name)
                            continue
                        await member.move_to(channel)
                        moved.append(member.display_name)
                    except discord.errors.Forbidden:
                        await ctx.send(f"Missing permissions to move {mention}.")
                    except Exception as e:
                        await ctx.send(f"Failed to move {mention}: {e}")
            except Exception as e:
                await ctx.send(f"Failed to process channel {team['channel']}: {e}")
        msg = ""
        if moved:
            msg += "Moved: " + ", ".join(f"**{n}**" for n in moved) + "\n"
        if not_in_voice:
            msg += "Not in voice: " + ", ".join(f"**{n}**" for n in not_in_voice) + "\n"
        if not_found:
            msg += "Not found: " + ", ".join(not_found) + "\n"
        if not_voice_channel:
            msg += "Not a valid voice channel: " + ", ".join(not_voice_channel) + "\n"
        await ctx.send(msg if msg else "No valid users or channels provided.")
    except Exception as e:
        await ctx.send(f"An error occurred in move: {e}")
@bot.command()
async def myperms(ctx):
    """Print the bot's permissions in this server."""
    perms = ctx.guild.me.guild_permissions
    msg = "**Bot Permissions:**\n"
    for perm, value in perms:
        msg += f"{perm}: {'✅' if value else '❌'}\n"
    await ctx.send(msg)
@move.error
async def move_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need the 'Move Members' permission to use this command.")
    else:
        await ctx.send(f"An error occurred: {error}")
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown command. Please use a valid command.")
    else:
        # Let specific error handlers (like @move.error) handle their own errors
        raise error
bot.run(TOKEN)
