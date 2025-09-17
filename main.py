import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
import threading
import aiohttp
from utils import check_ban, is_user_banned  # Import your existing utils functions

# Load environment variables from .env file
load_dotenv()

# Get the application ID and token from environment variables
APPLICATION_ID = os.getenv("APPLICATION_ID")
TOKEN = os.getenv("TOKEN")

# Exit with error if TOKEN is missing
if not TOKEN:
    print("Error: Missing TOKEN environment variable. Please add TOKEN in your .env file.")
    exit(1)

# Flask app for basic health check
app = Flask(__name__)
nomBot = "None"

@app.route('/')
def home():
    global nomBot
    return f"Bot {nomBot} is working"

# Run Flask in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

# Setup Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Language settings per user
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

# Your existing !ID and !checkban and !listbans commands here (unchanged)

@bot.command(name="ID")
async def check_ban_command(ctx):
    # Your existing code here
    ...

@bot.command(name="checkban")
async def checkban(ctx, user_id: int):
    # Your existing code here
    ...

@bot.command()
async def listbans(ctx):
    # Your existing code here
    ...

# New command to check Free Fire ID directly from the original Free Fire ID
@bot.command(name="check_freefire_id")
async def check_freefire_id(ctx, ff_id: str):
    url = f"http://raw.thug4ff.com/check_ban/check_ban/{ff_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                await ctx.send("Could not reach the Free Fire ban API. Please try again later.")
                return
            data = await response.json()
            if data.get("is_banned", 0) == 1:
                await ctx.send(f"Free Fire ID `{ff_id}` is **BANNED**.")
            else:
                await ctx.send(f"Free Fire ID `{ff_id}` is **NOT BANNED**.")

# Your ban command and other commands below

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"{member} has been banned. Reason: {reason}")
    except Exception as e:
        await ctx.send(f"Failed to ban {member}. Error: {e}")

# Start bot
bot.run(TOKEN)
