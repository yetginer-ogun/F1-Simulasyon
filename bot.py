import os
import asyncio
import discord
from discord.ext import commands
from logic import F1db, monte_carlo_championship

# CONFIG: set DISCORD_TOKEN env var before running
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN environment variable (Windows: set DISCORD_TOKEN=your_token)")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# single DB instance shared by bot
db = F1db()

@bot.event
async def on_ready():
    print(f"Discord bot ready — logged in as {bot.user} (id: {bot.user.id})")

@bot.command(name='simulate', help='Run championship simulation. Usage: !simulate [num_simulations]')
async def simulate(ctx, num_simulations: int = 2000):
    if num_simulations <= 0:
        await ctx.reply("Number of simulations must be > 0.", mention_author=False)
        return

    msg = await ctx.reply(f"Running {num_simulations} simulations — this may take a while...", mention_author=False)

    loop = asyncio.get_running_loop()
    # run CPU-bound simulation in executor to avoid blocking event loop
    try:
        result = await loop.run_in_executor(
            None,
            monte_carlo_championship,
            db.get_drivers(),
            db.get_remaining_races(),
            num_simulations
        )
    except Exception as e:
        await msg.edit(content=f"Simulation failed: {e}")
        return

    # result values are fractions (0..1) -> convert to percent and sort
    items = sorted(result.items(), key=lambda kv: -kv[1])[:15]
    lines = [f"{name}: {prob*100:.2f}%" for name, prob in items]
    out = "**Simulation results (top 15):**\n" + "\n".join(lines)
    # if message too long, send as file
    if len(out) <= 1900:
        await msg.edit(content=out)
    else:
        await msg.edit(content="Results too long, sending as file...")
        await ctx.send(file=discord.File(fp=io.BytesIO(out.encode('utf-8')), filename='simulation_results.txt'))

@bot.command(name='drivers', help='List drivers and current points')
async def drivers_cmd(ctx):
    drv = db.get_drivers()
    lines = [f"{d['name']} — {d['points']} pts (dnf {d.get('dnf_prob',0):.2f})" for d in drv]
    await ctx.reply("Drivers:\n" + "\n".join(lines), mention_author=False)

@bot.command(name='races', help='List remaining races')
async def races_cmd(ctx):
    races = db.get_remaining_races()
    lines = [f"{r['id']}: {r['name']} {'(Sprint)' if r.get('is_sprint') else ''}" for r in races]
    await ctx.reply("Remaining races:\n" + "\n".join(lines), mention_author=False)

if __name__ == '__main__':
    bot.run(TOKEN)