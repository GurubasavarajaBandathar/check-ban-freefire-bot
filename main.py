import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
import threading
import aiohttp
import asyncio
from utils import check_ban, is_user_banned

# Load environment variables from .env file
load_dotenv()
APPLICATION_ID = os.getenv("APPLICATION_ID")
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Error: Missing TOKEN environment variable. Please add TOKEN in your .env file.")
    exit(1)

app = Flask(__name__)
nomBot = "None"

@app.route('/')
def home():
    global nomBot
    return f"Bot {nomBot} is working"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DEFAULT_LANG = "en"
user_languages = {}

@bot.event
async def on_ready():
    global nomBot
    nomBot = f"{bot.user}"
    print(f"Bot is connected as {bot.user}")

@bot.command(name="guilds")
async def show_guilds(ctx):
    guild_names = [f"{i+1}. {guild.name}" for i, guild in enumerate(bot.guilds)]
    guild_list = "\n".join(guild_names)
    await ctx.send(f"Bot is in the following guilds:\n{guild_list}")

@bot.command(name="lang")
async def change_language(ctx, lang_code: str):
    lang_code = lang_code.lower()
    if lang_code not in ["en", "fr"]:
        await ctx.send("❌ Invalid language. Available options: `en`, `fr`")
        return
    user_languages[ctx.author.id] = lang_code
    message = "✅ Language set to English." if lang_code == 'en' else "✅ Langue définie sur le français."
    await ctx.send(f"{ctx.author.mention} {message}")

@bot.command(name="ID")
async def check_ban_command(ctx):
    # Place your original !ID command code here with correct indentation
    pass

@bot.command(name="checkban")
async def checkban(ctx, user_id: int):
    # Place your original !checkban command code here with correct indentation
    pass

@bot.command()
async def listbans(ctx):
    # Place your original !listbans command code here with correct indentation
    pass

@bot.command(name="check_freefire_id")
@commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
async def check_freefire_id(ctx, ff_id: str):
    url = f"http://raw.thug4ff.com/check_ban/check_ban/{ff_id}"
    async with aiohttp.ClientSession() as session:
        data = None
        for attempt in range(3):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        break
            except Exception:
                pass
            await asyncio.sleep(2)
        if data is None:
            await ctx.send("❌ Could not reach the Free Fire ban API. Please try again later.")
            return
        if data.get("is_banned", 0) == 1:
            await ctx.send(f"✅ Free Fire ID `{ff_id}` is **BANNED**.")
        else:
            await ctx.send(f"✅ Free Fire ID `{ff_id}` is **NOT BANNED**.")

@check_freefire_id.error
async def check_freefire_id_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ This command is on cooldown. Please try again in {round(error.retry_after, 1)} seconds.")
    else:
        await ctx.send("❌ An unexpected error occurred.")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"{member} has been banned. Reason: {reason}")
    except Exception as e:
        await ctx.send(f"Failed to ban {member}. Error: {e}")

bot.run(TOKEN)
