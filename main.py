import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
import threading
from utils import check_ban, is_user_banned  # Import the new function for guild ban check

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

# Original !ID command using external API - kept for reference, or remove if not needed
@bot.command(name="ID")
async def check_ban_command(ctx):
    content = ctx.message.content
    user_id = content[3:].strip()
    lang = user_languages.get(ctx.author.id, "en")
    print(f"Command issued by {ctx.author} (lang={lang})")
    if not user_id.isdigit():
        message = {
            "en": f"{ctx.author.mention} ❌ **Invalid UID!**\n➡️ Please use: `!ID 123456789`",
            "fr": f"{ctx.author.mention} ❌ **UID invalide !**\n➡️ Veuillez fournir un UID valide : `!ID 123456789`"
        }
        await ctx.send(message[lang])
        return
    async with ctx.typing():
        try:
            ban_status = await check_ban(user_id)
        except Exception as e:
            await ctx.send(f"{ctx.author.mention} ⚠️ An error occurred while checking the ban status.")
            return
        if ban_status is None:
            message = {
                "en": f"{ctx.author.mention} ❌ Could not get information. Try again later.",
                "fr": f"{ctx.author.mention} ❌ Impossible d'obtenir les informations. Réessayez plus tard."
            }
            await ctx.send(message[lang])
            return
        is_banned = int(ban_status.get("is_banned", 0))
        period = ban_status.get("period", "N/A")
        nickname = ban_status.get("nickname", "N/A")
        region = ban_status.get("region", "N/A")
        id_str = f"`{user_id}`"
        period_str = f"more than {period} months" if isinstance(period, int) and lang == "en" else (
                     f"plus de {period} mois" if isinstance(period, int) else
                     ("unavailable" if lang == "en" else "indisponible"))
        embed = discord.Embed(
            color=0xFF0000 if is_banned else 0x00FF00,
            timestamp=ctx.message.created_at
        )
        if is_banned:
            embed.title = "**▌ Banned Account 🛑 **" if lang == "en" else "**▌ Compte banni 🛑 **"
            embed.description = (
                f"**• {'Reason' if lang == 'en' else 'Raison'} :** "
                f"{'This account was confirmed for using cheats.' if lang == 'en' else 'Ce compte a été confirmé comme utilisant des hacks.'}\n"
                f"**• {'Suspension duration' if lang == 'en' else 'Durée de la suspension'} :** {period_str}\n"
                f"**• {'Nickname' if lang == 'en' else 'Pseudo'} :** `{nickname}`\n"
                f"**• {'Player ID' if lang == 'en' else 'ID du joueur'} :** `{id_str}`\n"
                f"**• {'Region' if lang == 'en' else 'Région'} :** `{region}`"
            )
            file = discord.File("assets/banned.gif", filename="banned.gif")
            embed.set_image(url="attachment://banned.gif")
        else:
            embed.title = "**▌ Clean Account ✅ **" if lang == "en" else "**▌ Compte non banni ✅ **"
            embed.description = (
                f"**• {'Status' if lang == 'en' else 'Statut'} :** "
                f"{'No sufficient evidence of cheat usage.' if lang == 'en' else 'Aucune preuve suffisante pour confirmer l’utilisation de hacks.'}\n"
                f"**• {'Nickname' if lang == 'en' else 'Pseudo'} :** `{nickname}`\n"
                f"**• {'Player ID' if lang == 'en' else 'ID du joueur'} :** `{id_str}`\n"
                f"**• {'Region' if lang == 'en' else 'Région'} :** `{region}`"
            )
            file = discord.File("assets/notbanned.gif", filename="notbanned.gif")
            embed.set_image(url="attachment://notbanned.gif")
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.set_footer(text="DEVELOPED BY THUG•")
        await ctx.send(f"{ctx.author.mention}", embed=embed, file=file)

# New !checkban command implementation using Discord guild ban check
@bot.command(name="checkban")
async def checkban(ctx, user_id: int):
    lang = user_languages.get(ctx.author.id, "en")
    print(f"Checkban command issued by {ctx.author} with user_id {user_id} (lang={lang})")
    async with ctx.typing():
        banned = await is_user_banned(ctx.guild, user_id)
        if banned:
            await ctx.send(f"{ctx.author.mention} User with ID `{user_id}` is banned in {ctx.guild.name}.")
        else:
            await ctx.send(f"{ctx.author.mention} User with ID `{user_id}` is not banned in {ctx.guild.name}.")

# Fixed !listbans command to handle async generator and errors
@bot.command()
async def listbans(ctx):
    try:
        banned_users = [ban async for ban in ctx.guild.bans()]  # Fixed async iteration
    except discord.Forbidden:
        await ctx.send("I do not have permission to view the ban list.")
        return
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        return
    if not banned_users:
        await ctx.send("There are no banned users in this server.")
        return
    banned_list = "\n".join(f"{ban.user} - ID: {ban.user.id}" for ban in banned_users)
    if len(banned_list) > 1900:
        chunks = [banned_list[i:i+1900] for i in range(0, len(banned_list), 1900)]
        for chunk in chunks:
            await ctx.send(f"Banned users:\n{chunk}")
    else:
        await ctx.send(f"Banned users:\n{banned_list}")

# New ban command added here
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"{member} has been banned. Reason: {reason}")
    except Exception as e:
        await ctx.send(f"Failed to ban {member}. Error: {e}")

# Start the bot
bot.run(TOKEN)
