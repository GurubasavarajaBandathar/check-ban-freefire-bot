import aiohttp
import os
from dotenv import load_dotenv
import asyncio  # Import asyncio for timeout
import discord  # Add discord.py import for guild ban check

load_dotenv()

# Original async API ban check (can still be used if needed)
async def check_ban(uid: str) -> dict | None:
    api_url = f"http://raw.thug4ff.com/check_ban/check_ban/{uid}"
    
    timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds total timeout
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as response:
                response.raise_for_status()
                response_data = await response.json()
                if response_data.get("status") == 200:
                    data = response_data.get("data")
                    if data:  # Ensure 'data' key exists and is not None
                        return {
                            "is_banned": data.get("is_banned", 0),
                            "nickname": data.get("nickname", ""),
                            "period": data.get("period", 0),
                            "region": data.get('region', "")
                        }
                # If status is not 200 or data is missing, return None
                return None
    except aiohttp.ClientError as e:
        print(f"API request failed for UID {uid}: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"API request timed out for UID {uid}.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for UID {uid}: {e}")
        return None

# New function to check if a user is banned in a specific Discord guild
async def is_user_banned(guild: discord.Guild, user_id: int) -> bool:
    """Check if a user ID is banned in the given guild."""
    try:
        bans = await guild.bans()
        for ban_entry in bans:
            if ban_entry.user.id == user_id:
                return True
        return False
    except Exception as e:
        print(f"Error checking ban for user {user_id} in guild {guild.id}: {e}")
        return False
