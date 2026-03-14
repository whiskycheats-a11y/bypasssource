import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import asyncio
import hashlib

# Replace with your bot token
TOKEN = "MTQ3MjkyODQ4MDAyNjAzODQ0Nw.GHZDcn.vbiN8WoilEa6-YOUaPRNGcCZ42i-OznQKuuzOE"
SERVERS = ["bd", "br", "europe", "id", "ind", "me", "na", "pk", "ru", "sac", "sg", "th", "us", "vn"]

SERVER_NAMES = {
    "bd": "BD - Bangladesh",
    "br": "BR - Brazil",
    "europe": "EUROPE - Europe",
    "id": "ID - Indonesia",
    "ind": "IND - India",
    "me": "ME - Middle East",
    "na": "NA - North America",
    "pk": "PK - Pakistan",
    "ru": "RU - Russia",
    "sac": "SAC - South America",
    "sg": "SG - Singapore",
    "th": "TH - Thailand",
    "us": "US - United States",
    "vn": "VN - Vietnam"
}

# Configuration file for allowed servers and authorized users
CONFIG_FILE = "bot_config.json"

# Developer name and security
DEVELOPER_NAME = "LORD._.SARTHAK"
DEVELOPER_NAME_HASH = hashlib.sha256(DEVELOPER_NAME.encode()).hexdigest()

# Hierarchy levels
class PermissionLevel:
    MAIN_OWNER = 0  # Can do everything, including adding other owners
    SUB_OWNER = 1   # Can only manage whitelists (add/remove UIDs)
    AUTHORIZED_USER = 2  # Can only manage whitelists
    NONE = 3  # No permissions

def check_developer_name():
    """Check if developer name has been tampered with."""
    current_hash = hashlib.sha256(DEVELOPER_NAME.encode()).hexdigest()
    if current_hash != DEVELOPER_NAME_HASH:
        print(f"[SECURITY ALERT] Developer name has been modified! Bot shutting down.")
        print(f"Expected hash: {DEVELOPER_NAME_HASH}")
        print(f"Current hash: {current_hash}")
        os._exit(1)  # Force quit the bot

def get_whitelist_filename(server: str) -> str:
    """Returns the filename for a specific server's whitelist."""
    return f"whitelist_{server.lower()}.json"

def load_config() -> dict:
    """Load bot configuration."""
    if not os.path.exists(CONFIG_FILE):
        # Default configuration with main owner ID
        default_config = {
            "main_owner_id": "",  # Will be set when bot starts
            "sub_owners": [],  # List of sub-owner user IDs
            "authorized_users": [],  # User IDs who can manage whitelists
            "allowed_servers": [],  # Discord server IDs where bot will work
            "admin_role_name": "Whitelist Admin"  # Optional: role name that can also manage
        }
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_config(config: dict):
    """Save bot configuration."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"[Config] Saved configuration")
    except Exception as e:
        print(f"[Error] Failed to save config: {e}")

def load_whitelist(server: str) -> dict:
    """Loads the whitelist for a specific server."""
    filename = get_whitelist_filename(server)
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_whitelist(server: str, data: dict):
    """Saves the whitelist for a specific server."""
    filename = get_whitelist_filename(server)
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[Whitelist] Saved {filename}")
    except Exception as e:
        print(f"[Error] Failed to save {filename}: {e}")

def save_to_main_whitelist(uid: str, expiry_timestamp: float):
    """Also save UID to main whitelist.json for compatibility with mitmproxy"""
    try:
        main_file = Path("whitelist.json")
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                main_data = json.load(f)
        else:
            main_data = {
                "auto_whitelist_duration_hours": 5555,
                "description": "Auto whitelist duration in hours - users added without explicit duration will be whitelisted for this duration",
                "metadata": {
                    "created": time.strftime("%Y-%m-%d"),
                    "last_updated": time.strftime("%Y-%m-%d"),
                    "unit": "hours"
                },
                "whitelisted_uids": {}
            }
        
        if "whitelisted_uids" not in main_data:
            main_data["whitelisted_uids"] = {}
        
        main_data["whitelisted_uids"][uid] = expiry_timestamp
        main_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d")
        
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=4, ensure_ascii=False)
        
        print(f"[Main Whitelist] Also added UID {uid} to whitelist.json")
        return True
    except Exception as e:
        print(f"[Main Whitelist] Error adding to main whitelist: {e}")
        return False

def remove_from_main_whitelist(uid: str):
    """Remove UID from main whitelist.json"""
    try:
        main_file = Path("whitelist.json")
        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                main_data = json.load(f)
            
            if "whitelisted_uids" in main_data and uid in main_data["whitelisted_uids"]:
                del main_data["whitelisted_uids"][uid]
                
                with open(main_file, 'w', encoding='utf-8') as f:
                    json.dump(main_data, f, indent=4, ensure_ascii=False)
                
                print(f"[Main Whitelist] Removed UID {uid} from whitelist.json")
                return True
    except Exception as e:
        print(f"[Main Whitelist] Error removing from main whitelist: {e}")
    return False

def get_auto_whitelist_duration() -> float:
    """Loads the auto whitelist duration in hours from whitelist.json."""
    try:
        if os.path.exists("whitelist.json"):
            with open("whitelist.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                return float(data.get("auto_whitelist_duration_hours", 5555))
    except (json.JSONDecodeError, FileNotFoundError, ValueError):
        pass
    return 5555  # Default to 5555 hours

class WhitelistBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.config = load_config()
        self.removal_queue = {}  # {message_id: {"channel_id": x, "uid": y, "server": z, "expiry": t}}

    async def setup_hook(self):
        self.check_expiration.start()
        print(f"[System] Whitelist Bot developed by Zytrone XD")
        print("[System] Background expiration check started.")

    @tasks.loop(minutes=1)
    async def check_expiration(self):
        """Iterates through all server files and removes expired UIDs."""
        now = time.time()
        
        # Check all server files
        for server in SERVERS:
            whitelist = load_whitelist(server)
            if not whitelist:
                continue
                
            expired_uids = []
            for uid, expiry_data in list(whitelist.items()):
                try:
                    # Handle both timestamp and dict formats
                    if isinstance(expiry_data, dict):
                        expiry_timestamp = expiry_data.get("expiry", float('inf'))
                    else:
                        expiry_timestamp = float(expiry_data)
                    
                    if expiry_timestamp <= now:
                        expired_uids.append(uid)
                except (ValueError, TypeError):
                    continue
            
            if expired_uids:
                for uid in expired_uids:
                    print(f"[System] UID {uid} expired on server {server}. Removing.")
                    del whitelist[uid]
                save_whitelist(server, whitelist)
                print(f"[System] Removed {len(expired_uids)} expired UIDs from {server}")
        
        # Also check and clean main whitelist.json
        try:
            main_file = Path("whitelist.json")
            if main_file.exists():
                with open(main_file, 'r', encoding='utf-8') as f:
                    main_data = json.load(f)
                
                if "whitelisted_uids" in main_data:
                    expired_main_uids = []
                    for uid, expiry in list(main_data["whitelisted_uids"].items()):
                        try:
                            if float(expiry) <= now:
                                expired_main_uids.append(uid)
                        except (ValueError, TypeError):
                            continue
                    
                    if expired_main_uids:
                        for uid in expired_main_uids:
                            del main_data["whitelisted_uids"][uid]
                        
                        with open(main_file, 'w', encoding='utf-8') as f:
                            json.dump(main_data, f, indent=4, ensure_ascii=False)
                        
                        print(f"[System] Removed {len(expired_main_uids)} expired UIDs from main whitelist.json")
        except Exception as e:
            print(f"[System] Error cleaning main whitelist: {e}")

    @check_expiration.before_loop
    async def before_check_expiration(self):
        await self.wait_until_ready()

    def is_allowed_server(self, guild_id: int) -> bool:
        """Check if the bot is allowed to work in this server."""
        allowed_servers = self.config.get("allowed_servers", [])
        # If allowed_servers is empty, allow all servers
        if not allowed_servers:
            return True
        return str(guild_id) in allowed_servers or guild_id in allowed_servers

    def get_permission_level(self, user_id: int) -> int:
        """Get the permission level of a user."""
        # Check if main owner
        main_owner = self.config.get("main_owner_id", "")
        if str(user_id) == main_owner or user_id == main_owner:
            return PermissionLevel.MAIN_OWNER
        
        # Check if sub-owner
        sub_owners = self.config.get("sub_owners", [])
        if str(user_id) in sub_owners or user_id in sub_owners:
            return PermissionLevel.SUB_OWNER
        
        # Check if authorized user
        authorized_users = self.config.get("authorized_users", [])
        if str(user_id) in authorized_users or user_id in authorized_users:
            return PermissionLevel.AUTHORIZED_USER
        
        return PermissionLevel.NONE

    def can_add_sub_owner(self, user_id: int) -> bool:
        """Check if user can add sub-owners (only main owner)."""
        return self.get_permission_level(user_id) == PermissionLevel.MAIN_OWNER

    def can_add_authorized_user(self, user_id: int) -> bool:
        """Check if user can add authorized users (only main owner)."""
        return self.get_permission_level(user_id) == PermissionLevel.MAIN_OWNER

    def can_manage_whitelist(self, user_id: int) -> bool:
        """Check if user can manage whitelists (main owner, sub-owners, authorized users)."""
        level = self.get_permission_level(user_id)
        return level in [PermissionLevel.MAIN_OWNER, PermissionLevel.SUB_OWNER, PermissionLevel.AUTHORIZED_USER]

    def can_manage_server_list(self, user_id: int) -> bool:
        """Check if user can manage server list (only main owner)."""
        return self.get_permission_level(user_id) == PermissionLevel.MAIN_OWNER

    def can_manage_owners(self, user_id: int) -> bool:
        """Check if user can manage owners (only main owner)."""
        return self.get_permission_level(user_id) == PermissionLevel.MAIN_OWNER

bot = WhitelistBot()

def add_developer_footer(embed: discord.Embed) -> discord.Embed:
    """Add premium developer footer to embed."""
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    return embed

def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create premium error embed."""
    embed = discord.Embed(color=0xFF004D) # Neon Red/Pink
    embed.set_author(name="⚠️ ＳＹＳＴＥＭ ＥＲＲＯＲ")
    desc = description.replace('\n', '\n> ')
    embed.description = f"### {title}\n> {desc}"
    return add_developer_footer(embed)

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create premium success embed."""
    embed = discord.Embed(color=0x00FFD1) # Neon Cyan
    embed.set_author(name="✨ ＳＵＣＣＥＳＳ")
    desc = description.replace('\n', '\n> ')
    embed.description = f"### {title}\n> {desc}"
    return add_developer_footer(embed)

def create_info_embed(title: str, description: str) -> discord.Embed:
    """Create premium info embed."""
    embed = discord.Embed(color=0x7000FF) # Neon Purple
    embed.set_author(name="💠 ＩＮＦＯＲＭＡＴＩＯＮ")
    desc = description.replace('\n', '\n> ')
    embed.description = f"### {title}\n> {desc}"
    return add_developer_footer(embed)

@bot.event
async def on_ready():
    print(f"[System] Logged in as {bot.user} (ID: {bot.user.id})")
    
    # Security check
    check_developer_name()
    
    # Set main owner in config if not already set
    bot.config = load_config()
    if not bot.config.get("main_owner_id"):
        bot.config["main_owner_id"] = str(bot.owner_id)
        save_config(bot.config)
        print(f"[System] Set main owner ID to {bot.owner_id}")
    
    try:
        synced = await bot.tree.sync()
        print(f"[System] Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"[Error] Failed to sync commands: {e}")
    
    # Start the message update task
    update_expired_messages.start()

async def send_not_allowed_message(interaction: discord.Interaction):
    """Send message when bot is not allowed in server."""
    embed = discord.Embed(
        title="🚫 Bot Not Allowed",
        description="This bot is not configured to work in this server.",
        color=0xe74c3c
    )
    embed.add_field(
        name="Setup Required",
        value="Ask the Main Owner to add this server's ID using `/owner addserver`",
        inline=False
    )
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def send_permission_denied_message(interaction: discord.Interaction, required_level: str = "AUTHORIZED_USER"):
    """Send permission denied message."""
    levels = {
        "MAIN_OWNER": "Main Owner",
        "SUB_OWNER": "Sub-Owner",
        "AUTHORIZED_USER": "Authorized User"
    }
    
    embed = discord.Embed(
        title="🚫 Permission Denied",
        description=f"This command requires **{levels.get(required_level, required_level)}** permissions.",
        color=0xe74c3c
    )
    
    current_level = bot.get_permission_level(interaction.user.id)
    level_names = {
        PermissionLevel.MAIN_OWNER: "Main Owner",
        PermissionLevel.SUB_OWNER: "Sub-Owner",
        PermissionLevel.AUTHORIZED_USER: "Authorized User",
        PermissionLevel.NONE: "No Permissions"
    }
    
    embed.add_field(
        name="Your Permission Level",
        value=level_names.get(current_level, "Unknown"),
        inline=False
    )
    
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================
# MAIN OWNER ONLY COMMANDS
# ============================

@bot.tree.command(name="owner_addsubowner", description="Add a user as sub-owner (Main Owner Only)")
@app_commands.describe(user_id="The Discord user ID to add as sub-owner")
async def owner_addsubowner(interaction: discord.Interaction, user_id: str):
    """Add a user as sub-owner (Main Owner only)."""
    if not bot.can_manage_owners(interaction.user.id):
        await send_permission_denied_message(interaction, "MAIN_OWNER")
        return
    
    if not user_id.isdigit():
        embed = create_error_embed("❌ Invalid ID", "User ID must be numeric.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    bot.config = load_config()
    sub_owners = bot.config.get("sub_owners", [])
    
    # Check if already a sub-owner
    if user_id in sub_owners:
        embed = create_success_embed("✅ Already Sub-Owner", f"User ID `{user_id}` is already a sub-owner.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check if trying to add main owner
    if user_id == str(bot.config.get("main_owner_id")):
        embed = create_error_embed("❌ Cannot Add Main Owner", "Cannot add main owner as sub-owner.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    sub_owners.append(user_id)
    bot.config["sub_owners"] = sub_owners
    save_config(bot.config)
    
    embed = discord.Embed(
        title="👑 Sub-Owner Added",
        description=f"User ID `{user_id}` added as sub-owner.",
        color=0xf1c40f
    )
    embed.add_field(
        name="Sub-Owner Permissions",
        value="• Can add/remove UIDs from whitelist\n• Can check whitelist status\n• Can list whitelisted UIDs",
        inline=False
    )
    embed.add_field(name="👤 Added by", value=f"<@{interaction.user.id}>", inline=True)
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="owner_removesubowner", description="Remove a user from sub-owners (Main Owner Only)")
@app_commands.describe(user_id="The Discord user ID to remove from sub-owners")
async def owner_removesubowner(interaction: discord.Interaction, user_id: str):
    """Remove a user from sub-owners (Main Owner only)."""
    if not bot.can_manage_owners(interaction.user.id):
        await send_permission_denied_message(interaction, "MAIN_OWNER")
        return
    
    if not user_id.isdigit():
        embed = create_error_embed("❌ Invalid ID", "User ID must be numeric.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    bot.config = load_config()
    sub_owners = bot.config.get("sub_owners", [])
    
    if user_id not in sub_owners:
        embed = create_error_embed("❌ Not a Sub-Owner", f"User ID `{user_id}` is not a sub-owner.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    sub_owners.remove(user_id)
    bot.config["sub_owners"] = sub_owners
    save_config(bot.config)
    
    # Also remove from authorized users if they're there
    authorized_users = bot.config.get("authorized_users", [])
    if user_id in authorized_users:
        authorized_users.remove(user_id)
        bot.config["authorized_users"] = authorized_users
        save_config(bot.config)
    
    embed = discord.Embed(
        title="👑 Sub-Owner Removed",
        description=f"User ID `{user_id}` removed from sub-owners.",
        color=0xe74c3c
    )
    embed.add_field(name="👤 Removed by", value=f"<@{interaction.user.id}>", inline=True)
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="owner_addauthorized", description="Add a user to authorized users list (Main Owner Only)")
@app_commands.describe(user_id="The Discord user ID to authorize")
async def owner_addauthorized(interaction: discord.Interaction, user_id: str):
    """Add a user to authorized users list (Main Owner only)."""
    if not bot.can_add_authorized_user(interaction.user.id):
        await send_permission_denied_message(interaction, "MAIN_OWNER")
        return
    
    if not user_id.isdigit():
        embed = create_error_embed("❌ Invalid ID", "User ID must be numeric.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    bot.config = load_config()
    authorized_users = bot.config.get("authorized_users", [])
    
    if user_id in authorized_users:
        embed = create_success_embed("✅ Already Authorized", f"User ID `{user_id}` is already authorized.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check if trying to add main owner or sub-owner
    main_owner = bot.config.get("main_owner_id", "")
    sub_owners = bot.config.get("sub_owners", [])
    
    if user_id == str(main_owner) or user_id in sub_owners:
        embed = create_error_embed("❌ Already Has Access", "User is already a main owner or sub-owner.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    authorized_users.append(user_id)
    bot.config["authorized_users"] = authorized_users
    save_config(bot.config)
    
    embed = discord.Embed(
        title="✅ User Authorized",
        description=f"User ID `{user_id}` added to authorized users list.",
        color=0x2ecc71
    )
    embed.add_field(
        name="Permissions Granted",
        value="• Can add/remove UIDs from whitelist\n• Can check whitelist status\n• Can list whitelisted UIDs",
        inline=False
    )
    embed.add_field(name="👤 Added by", value=f"<@{interaction.user.id}>", inline=True)
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="owner_removeauthorized", description="Remove a user from authorized users list (Main Owner Only)")
@app_commands.describe(user_id="The Discord user ID to remove")
async def owner_removeauthorized(interaction: discord.Interaction, user_id: str):
    """Remove a user from authorized users list (Main Owner only)."""
    if not bot.can_add_authorized_user(interaction.user.id):
        await send_permission_denied_message(interaction, "MAIN_OWNER")
        return
    
    if not user_id.isdigit():
        embed = create_error_embed("❌ Invalid ID", "User ID must be numeric.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    bot.config = load_config()
    authorized_users = bot.config.get("authorized_users", [])
    
    if user_id not in authorized_users:
        embed = create_error_embed("❌ Not Authorized", f"User ID `{user_id}` is not in authorized users list.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    authorized_users.remove(user_id)
    bot.config["authorized_users"] = authorized_users
    save_config(bot.config)
    
    embed = discord.Embed(
        title="🗑️ User Authorization Removed",
        description=f"User ID `{user_id}` removed from authorized users list.",
        color=0xe74c3c
    )
    embed.add_field(name="👤 Removed by", value=f"<@{interaction.user.id}>", inline=True)
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="owner_addserver", description="Add a server to the allowed servers list (Main Owner Only)")
@app_commands.describe(server_id="The Discord server ID to allow")
async def owner_addserver(interaction: discord.Interaction, server_id: str):
    """Add a server to allowed servers list (Main Owner only)."""
    if not bot.can_manage_server_list(interaction.user.id):
        await send_permission_denied_message(interaction, "MAIN_OWNER")
        return
    
    if not server_id.isdigit():
        embed = create_error_embed("❌ Invalid ID", "Server ID must be numeric.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    bot.config = load_config()
    allowed_servers = bot.config.get("allowed_servers", [])
    
    if server_id not in allowed_servers:
        allowed_servers.append(server_id)
        bot.config["allowed_servers"] = allowed_servers
        save_config(bot.config)
        
        embed = discord.Embed(
            title="✅ Server Added",
            description=f"Server ID `{server_id}` added to allowed servers list.",
            color=0x2ecc71
        )
        embed.add_field(name="👤 Added by", value=f"<@{interaction.user.id}>", inline=True)
        embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
        await interaction.response.send_message(embed=embed)
    else:
        embed = create_success_embed("✅ Already Allowed", f"Server ID `{server_id}` is already in the allowed list.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="owner_removeserver", description="Remove a server from allowed servers list (Main Owner Only)")
@app_commands.describe(server_id="The Discord server ID to remove")
async def owner_removeserver(interaction: discord.Interaction, server_id: str):
    """Remove a server from allowed servers list (Main Owner only)."""
    if not bot.can_manage_server_list(interaction.user.id):
        await send_permission_denied_message(interaction, "MAIN_OWNER")
        return
    
    if not server_id.isdigit():
        embed = create_error_embed("❌ Invalid ID", "Server ID must be numeric.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    bot.config = load_config()
    allowed_servers = bot.config.get("allowed_servers", [])
    
    if server_id not in allowed_servers:
        embed = create_error_embed("❌ Not in List", f"Server ID `{server_id}` is not in the allowed list.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    allowed_servers.remove(server_id)
    bot.config["allowed_servers"] = allowed_servers
    save_config(bot.config)
    
    embed = discord.Embed(
        title="🗑️ Server Removed",
        description=f"Server ID `{server_id}` removed from allowed servers list.",
        color=0xe74c3c
    )
    embed.add_field(name="👤 Removed by", value=f"<@{interaction.user.id}>", inline=True)
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="owner_listpermissions", description="List all permissions and users (Main Owner Only)")
async def owner_listpermissions(interaction: discord.Interaction):
    """List all permissions and users (Main Owner only)."""
    if not bot.can_manage_owners(interaction.user.id):
        await send_permission_denied_message(interaction, "MAIN_OWNER")
        return
    
    bot.config = load_config()
    main_owner = bot.config.get("main_owner_id", "Not set")
    sub_owners = bot.config.get("sub_owners", [])
    authorized_users = bot.config.get("authorized_users", [])
    allowed_servers = bot.config.get("allowed_servers", [])
    
    embed = discord.Embed(
        title="👑 Permission Hierarchy - Main Owner View",
        color=0xf1c40f
    )
    
    # Main Owner
    embed.add_field(
        name="👑 Main Owner",
        value=f"<@{main_owner}> (`{main_owner}`)",
        inline=False
    )
    
    # Sub-Owners
    if sub_owners:
        sub_owner_list = "\n".join([f"• <@{uid}> (`{uid}`)" for uid in sub_owners])
        embed.add_field(
            name=f"👥 Sub-Owners ({len(sub_owners)})",
            value=sub_owner_list,
            inline=False
        )
    else:
        embed.add_field(name="👥 Sub-Owners", value="No sub-owners added yet.", inline=False)
    
    # Authorized Users
    if authorized_users:
        auth_user_list = "\n".join([f"• <@{uid}> (`{uid}`)" for uid in authorized_users[:10]])
        if len(authorized_users) > 10:
            auth_user_list += f"\n... and {len(authorized_users) - 10} more"
        embed.add_field(
            name=f"✅ Authorized Users ({len(authorized_users)})",
            value=auth_user_list,
            inline=False
        )
    else:
        embed.add_field(name="✅ Authorized Users", value="No authorized users yet.", inline=False)
    
    # Allowed Servers
    if allowed_servers:
        server_list = []
        for srv_id in allowed_servers[:5]:  # Show first 5 only
            try:
                guild = bot.get_guild(int(srv_id))
                server_name = guild.name if guild else "Unknown Server"
                server_list.append(f"• `{srv_id}` - {server_name}")
            except:
                server_list.append(f"• `{srv_id}` - Unknown Server")
        
        if len(allowed_servers) > 5:
            server_list.append(f"... and {len(allowed_servers) - 5} more")
        
        embed.add_field(
            name=f"🌍 Allowed Servers ({len(allowed_servers)})",
            value="\n".join(server_list),
            inline=False
        )
    else:
        embed.add_field(
            name="🌍 Allowed Servers",
            value="No restrictions - bot works in all servers",
            inline=False
        )
    
    # Summary
    embed.add_field(
        name="📊 Summary",
        value=f"**Total Users with Access:** {1 + len(sub_owners) + len(authorized_users)}\n**Total Servers:** {len(allowed_servers) if allowed_servers else 'All'}",
        inline=False
    )
    
    embed.set_footer(text=f"DEVELOPED BY Zytrone XD | Only Main Owner can modify these permissions")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================
# PERMISSION CHECK COMMAND (Anyone can use)
# ============================

@bot.tree.command(name="mypermissions", description="Check your permission level")
async def mypermissions(interaction: discord.Interaction):
    """Check your own permission level."""
    level = bot.get_permission_level(interaction.user.id)
    level_names = {
        PermissionLevel.MAIN_OWNER: "👑 Main Owner",
        PermissionLevel.SUB_OWNER: "👥 Sub-Owner",
        PermissionLevel.AUTHORIZED_USER: "✅ Authorized User",
        PermissionLevel.NONE: "🚫 No Permissions"
    }
    
    level_descriptions = {
        PermissionLevel.MAIN_OWNER: (
            "• Add/remove sub-owners\n"
            "• Add/remove authorized users\n"
            "• Manage server list\n"
            "• Add/remove UIDs from whitelist"
        ),
        PermissionLevel.SUB_OWNER: (
            "• Add/remove UIDs from whitelist\n"
            "• Check whitelist status\n"
            "• List whitelisted UIDs"
        ),
        PermissionLevel.AUTHORIZED_USER: (
            "• Add/remove UIDs from whitelist\n"
            "• Check whitelist status\n"
            "• List whitelisted UIDs"
        ),
        PermissionLevel.NONE: "• No permissions (contact Main Owner)"
    }
    
    commands_allowed = {
        PermissionLevel.MAIN_OWNER: "All commands",
        PermissionLevel.SUB_OWNER: "/whitelistadd, /whitelistremove, /whiteliststatus, /whitelistlist",
        PermissionLevel.AUTHORIZED_USER: "/whitelistadd, /whitelistremove, /whiteliststatus, /whitelistlist",
        PermissionLevel.NONE: "None"
    }
    
    embed = discord.Embed(
        title="🔐 Your Permissions",
        color=0x9b59b6
    )
    
    embed.add_field(
        name="Permission Level",
        value=level_names.get(level, "Unknown"),
        inline=False
    )
    
    embed.add_field(
        name="Capabilities",
        value=level_descriptions.get(level, "None"),
        inline=False
    )
    
    embed.add_field(
        name="Commands You Can Use",
        value=commands_allowed.get(level, "None"),
        inline=False
    )
    
    if level == PermissionLevel.NONE:
        embed.add_field(
            name="How to Get Access",
            value="Contact the Main Owner (<@" + bot.config.get("main_owner_id", "Unknown") + ">)",
            inline=False
        )
    
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================
# WHITELIST COMMANDS (Sub-Owner+ and Authorized User+)
# ============================

@bot.tree.command(name="whitelistadd", description="Add a UID to a server whitelist with optional expiration")
@app_commands.describe(
    uid="The player UID to whitelist",
    server="The game server",
    duration="Duration in hours until expiration (leave empty for auto-whitelist duration)"
)
async def whitelistadd(interaction: discord.Interaction, uid: str, server: str, duration: float = None):
    """Command to add a UID to a server-specific whitelist file."""
    # Check if bot is allowed in this server
    if not bot.is_allowed_server(interaction.guild_id):
        await send_not_allowed_message(interaction)
        return
    
    # Check if user can manage whitelist
    if not bot.can_manage_whitelist(interaction.user.id):
        await send_permission_denied_message(interaction, "SUB_OWNER")
        return
    
    server = server.lower()
    if server not in SERVERS:
        embed = create_error_embed("❌ Invalid Server", f"Choose from: {', '.join(SERVERS)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if duration is not None and duration <= 0:
        embed = create_error_embed("❌ Invalid Duration", "Duration must be greater than 0 hours.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not uid.isdigit():
        embed = create_error_embed("❌ Invalid UID", "UID must be numeric.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    whitelist = load_whitelist(server)
    
    # Use auto-whitelist duration if not specified
    actual_duration = duration if duration is not None else get_auto_whitelist_duration()
    
    expiry_timestamp = time.time() + (actual_duration * 3600)
    
    # Add to server-specific file
    whitelist[uid] = expiry_timestamp
    save_whitelist(server, whitelist)
    
    # ALSO ADD TO MAIN WHITELIST.JSON for mitmproxy compatibility
    save_to_main_whitelist(uid, expiry_timestamp)
    
    expiry_datetime = datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc)
    
    duration_source = "specified" if duration is not None else "auto (from whitelist.json)"
    
    # Get permission level of adder
    adder_level = bot.get_permission_level(interaction.user.id)
    level_names = {
        PermissionLevel.MAIN_OWNER: "👑 Main Owner",
        PermissionLevel.SUB_OWNER: "👥 Sub-Owner",
        PermissionLevel.AUTHORIZED_USER: "✅ Authorized User"
    }
    
    embed = discord.Embed(
        color=0x00FFD1,  # Aesthetic Neon Cyan
        timestamp=expiry_datetime
    )
    embed.set_author(name="🛡️ ＷＨＩＴＥＬＩＳＴ  ＡＵＴＨＯＲＩＺＡＴＩＯＮ")
    
    embed.description = (
        f"# ✨ ACCESS GRANTED\n\n"
        f"> **SUBJECT UID:** `{uid}`\n"
        f"> **SERVER NODE:** `{server.upper()}`\n"
        f"────────────────────────"
    )
    
    embed.add_field(
        name="⏳ **DURATION**", 
        value=f"```ansi\n\u001b[2;36m{actual_duration} HOURS\u001b[0m\n```", 
        inline=True
    )
    embed.add_field(
        name="⏰ **EXPIRES ET**", 
        value=f"> <t:{int(expiry_timestamp)}:R>\n> <t:{int(expiry_timestamp)}:f>", 
        inline=True
    )
    
    embed.add_field(
        name="📂 **DATA DUMPS**", 
        value="```\n- Antiban\n- All Server Safe\n- All Emulator Supported\n- Advanced Anticheats Added\n```", 
        inline=False
    )
    
    embed.add_field(
        name="🛡️ **AUTHORIZED BY**", 
        value=f"> <@{interaction.user.id}>\n> `{level_names.get(adder_level, 'Unknown')}`", 
        inline=False
    )
    
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ ＢＹ Zytrone XD ✦ | Auto-Remove Active")
    
    # Create view with remove button
    view = discord.ui.View(timeout=None)
    
    remove_button = discord.ui.Button(
        style=discord.ButtonStyle.danger,
        label=f"Remove UID {uid}",
        custom_id=f"remove_{uid}_{server}_{int(expiry_timestamp)}"
    )
    
    async def remove_button_callback(button_interaction: discord.Interaction):
        # Check permissions for button clicker
        if not bot.can_manage_whitelist(button_interaction.user.id):
            await send_permission_denied_message(button_interaction, "SUB_OWNER")
            return
            
        # Remove from server file
        whitelist = load_whitelist(server)
        if uid in whitelist:
            del whitelist[uid]
            save_whitelist(server, whitelist)
            
        # Remove from main whitelist
        remove_from_main_whitelist(uid)
        
        # Get permission level of remover
        remover_level = bot.get_permission_level(button_interaction.user.id)
        
        # Update the original message
        updated_embed = discord.Embed(color=0xFF004D) # Neon Red
        updated_embed.set_author(name="🗑️ ＷＨＩＴＥＬＩＳＴ  ＲＥＶＯＫＥＤ")
        updated_embed.description = (
            f"# 🚫 ACCESS TERMINATED\n\n"
            f"> **SUBJECT UID:** `{uid}`\n"
            f"> **SERVER NODE:** `{server.upper()}`\n"
            f"────────────────────────"
        )
        updated_embed.add_field(
            name="🛡️ **REVOKED BY**", 
            value=f"> <@{button_interaction.user.id}>\n> `{level_names.get(remover_level, 'Unknown')}`", 
            inline=True
        )
        updated_embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ ＢＹ Zytrone XD ✦")
        
        # Disable the button
        remove_button.style = discord.ButtonStyle.secondary
        remove_button.disabled = True
        remove_button.label = f"Removed by {button_interaction.user.name}"
        
        await button_interaction.message.edit(embed=updated_embed, view=view)
        
        # Send confirmation
        confirm_embed = discord.Embed(color=0xFF004D)
        confirm_embed.set_author(name="✨ ＡＣＴＩＯＮ ＳＵＣＣＥＳＳ")
        confirm_embed.description = f"### ✅ UID Removed\n> UID `{uid}` has been successfully removed from **{server.upper()}**."
        confirm_embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ  ＢＹ  Zytrone XD ✦")
        await button_interaction.response.send_message(embed=confirm_embed, ephemeral=True)
    
    remove_button.callback = remove_button_callback
    view.add_item(remove_button)
    
    # Store message info for scheduled removal
    message = await interaction.response.send_message(embed=embed, view=view)
    
    # Schedule automatic removal message update when expired
    if actual_duration < 100000:  # Only schedule if not permanent
        removal_time = datetime.fromtimestamp(expiry_timestamp)
        bot.removal_queue[message.id] = {
            "channel_id": interaction.channel_id,
            "uid": uid,
            "server": server,
            "expiry": expiry_timestamp
        }

@whitelistadd.autocomplete('server')
async def server_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=SERVER_NAMES.get(srv, srv.upper()), value=srv)
        for srv in SERVERS if current.lower() in srv.lower()
    ][:25]

@bot.tree.command(name="whitelistremove", description="Remove a UID from a server whitelist")
@app_commands.describe(
    uid="The player UID to remove",
    server="The game server"
)
async def whitelistremove(interaction: discord.Interaction, uid: str, server: str):
    """Remove a UID from whitelist."""
    # Check if bot is allowed in this server
    if not bot.is_allowed_server(interaction.guild_id):
        await send_not_allowed_message(interaction)
        return
    
    # Check if user can manage whitelist
    if not bot.can_manage_whitelist(interaction.user.id):
        await send_permission_denied_message(interaction, "SUB_OWNER")
        return
    
    server = server.lower()
    if server not in SERVERS:
        embed = create_error_embed("❌ Invalid Server", f"Choose from: {', '.join(SERVERS)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    whitelist = load_whitelist(server)
    if uid not in whitelist:
        embed = create_error_embed("❌ Not Whitelisted", f"UID `{uid}` is not whitelisted on **{server.upper()}**.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Remove from server file
    del whitelist[uid]
    save_whitelist(server, whitelist)
    
    # ALSO REMOVE FROM MAIN WHITELIST.JSON
    remove_from_main_whitelist(uid)

    embed = discord.Embed(
        color=0xFF004D # Neon Red
    )
    embed.set_author(name="🗑️ ＷＨＩＴＥＬＩＳＴ  ＲＥＶＯＫＥＤ")
    embed.description = (
        f"# 🚫 ACCESS TERMINATED\n\n"
        f"> **SUBJECT UID:** `{uid}`\n"
        f"> **SERVER NODE:** `{server.upper()}`\n"
        f"────────────────────────"
    )
    embed.add_field(
        name="🛡️ **REVOKED BY**", 
        value=f"> <@{interaction.user.id}>", 
        inline=True
    )
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ ＢＹ Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="whiteliststatus", description="Check whitelist status of a UID")
@app_commands.describe(
    uid="The player UID to check",
    server="The game server"
)
async def whiteliststatus(interaction: discord.Interaction, uid: str, server: str):
    """Check whitelist status."""
    # Check if bot is allowed in this server
    if not bot.is_allowed_server(interaction.guild_id):
        await send_not_allowed_message(interaction)
        return
    
    server = server.lower()
    if server not in SERVERS:
        embed = create_error_embed("❌ Invalid Server", f"Choose from: {', '.join(SERVERS)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    whitelist = load_whitelist(server)
    if uid not in whitelist:
        embed = create_error_embed("❌ Not Whitelisted", f"UID `{uid}` is **NOT** whitelisted on **{server.upper()}**.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    expiry_data = whitelist[uid]
    try:
        if isinstance(expiry_data, dict):
            expiry_timestamp = expiry_data.get("expiry", float('inf'))
        else:
            expiry_timestamp = float(expiry_data)
    except (ValueError, TypeError):
        expiry_timestamp = float('inf')
    
    remaining = expiry_timestamp - time.time()
    
    if remaining <= 0:
        embed = create_info_embed("⌛ Expired", f"UID `{uid}` whitelist has **expired**.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if remaining > (999 * 365 * 24 * 3600):
        remaining_text = "**PERMANENT**"
    else:
        hours = remaining / 3600
        remaining_text = f"`{round(hours, 2)} hours`"

    embed = discord.Embed(
        color=0x7000FF # Neon Purple
    )
    embed.set_author(name="🔍 ＳＴＡＴＵＳ  ＱＵＥＲＹ")
    embed.description = (
        f"# 📡 ACTIVE RECORD FOUND\n\n"
        f"> **SUBJECT UID:** `{uid}`\n"
        f"> **SERVER NODE:** `{server.upper()}`\n"
        f"────────────────────────"
    )
    embed.add_field(
        name="⏳ **REMAINING TIME**", 
        value=f"```ansi\n\u001b[2;35m{remaining_text.replace('`','')}\u001b[0m\n```", 
        inline=True
    )
    
    if remaining < (999 * 365 * 24 * 3600):
        embed.add_field(
            name="⏰ **EXPIRATION ETA**", 
            value=f"> <t:{int(expiry_timestamp)}:R>\n> <t:{int(expiry_timestamp)}:f>", 
            inline=True
        )
        
    embed.add_field(
        name="📂 **DATA SOURCES**", 
        value="```\n- Antiban\n- All Server Safe\n- All Emulator Supported\n- Advanced Anticheats Added\n```", 
        inline=False
    )
    
    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ ＢＹ Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed)

@whiteliststatus.autocomplete('server')
async def status_server_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=SERVER_NAMES.get(srv, srv.upper()), value=srv)
        for srv in SERVERS if current.lower() in srv.lower()
    ][:25]

@bot.tree.command(name="whitelistlist", description="List all whitelisted UIDs for a server")
@app_commands.describe(
    server="The game server"
)
async def whitelistlist(interaction: discord.Interaction, server: str):
    """List whitelisted UIDs."""
    # Check if bot is allowed in this server
    if not bot.is_allowed_server(interaction.guild_id):
        await send_not_allowed_message(interaction)
        return
    
    server = server.lower()
    if server not in SERVERS:
        embed = create_error_embed("❌ Invalid Server", f"Choose from: {', '.join(SERVERS)}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    whitelist = load_whitelist(server)
    if not whitelist:
        embed = create_info_embed("📭 Empty Whitelist", f"No UIDs whitelisted on **{server.upper()}**.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Build list of UIDs with their status
    uid_list = []
    now = time.time()
    
    for uid, expiry_data in list(whitelist.items()):
        try:
            if isinstance(expiry_data, dict):
                expiry_timestamp = expiry_data.get("expiry", float('inf'))
            else:
                expiry_timestamp = float(expiry_data)
            
            remaining = expiry_timestamp - now
            
            if remaining > (999 * 365 * 24 * 3600):
                status = "🟢 PERMANENT"
            elif remaining > 0:
                hours = remaining / 3600
                status = f"🟡 {round(hours, 1)}h"
            else:
                status = "🔴 EXPIRED"
            
            uid_list.append(f"`{uid}` {status}")
        except:
            uid_list.append(f"`{uid}` ⚠️ ERROR")

    # Split into chunks if too many
    chunks = [uid_list[i:i+15] for i in range(0, len(uid_list), 15)]
    
    for idx, chunk in enumerate(chunks):
        embed = discord.Embed(
            color=0x4169E1 # Royal Blue
        )
        embed.set_author(name=f"📋 {server.upper()} ＷＨＩＴＥＬＩＳＴ  ＤＡＴＡＢＡＳＥ")
        embed.description = (
            f"# 📊 SECURE LOGS ({len(whitelist)} ENTRIES)\n\n"
            f"> " + "\n> ".join(chunk)
        )
        
        embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ ＢＹ Zytrone XD ✦" + (f" | PAGE {idx+1}/{len(chunks)}" if len(chunks) > 1 else ""))
        
        if idx == 0:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.followup.send(embed=embed)

@whitelistlist.autocomplete('server')
async def list_server_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=SERVER_NAMES.get(srv, srv.upper()), value=srv)
        for srv in SERVERS if current.lower() in srv.lower()
    ][:25]

# ============================
# OTHER WHITELIST COMMANDS (Keep existing ones)
# ============================

@bot.tree.command(name="whitelistmaincheck", description="Check if a UID exists in main whitelist.json")
@app_commands.describe(uid="The player UID to check")
async def whitelistmaincheck(interaction: discord.Interaction, uid: str):
    """Check if UID exists in main whitelist.json."""
    # Check if user can manage whitelist
    if not bot.can_manage_whitelist(interaction.user.id):
        await send_permission_denied_message(interaction, "SUB_OWNER")
        return
    
    try:
        main_file = Path("whitelist.json")
        if not main_file.exists():
            embed = create_error_embed("❌ File Not Found", "`whitelist.json` not found.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        with open(main_file, 'r', encoding='utf-8') as f:
            main_data = json.load(f)
        
        if "whitelisted_uids" in main_data and uid in main_data["whitelisted_uids"]:
            expiry = main_data["whitelisted_uids"][uid]
            current_time = time.time()
            remaining = expiry - current_time
            
            if remaining > 0:
                hours = remaining / 3600
                embed = discord.Embed(
                    color=0x00FFD1 # Neon Cyan
                )
                embed.set_author(name="🔍 ＭＡＩＮ  ＤＡＴＡＢＡＳＥ  ＱＵＥＲＹ")
                embed.description = (
                    f"# ✨ RECORD VERIFIED\n\n"
                    f"> **SUBJECT UID:** `{uid}`\n"
                    f"> **LOCATED IN:** `whitelist.json`\n"
                    f"────────────────────────"
                )
                embed.add_field(
                    name="⏳ **REMAINING TIME**", 
                    value=f"```ansi\n\u001b[2;36m{round(hours, 2)} HOURS\u001b[0m\n```", 
                    inline=True
                )
                embed.add_field(
                    name="⏰ **EXPIRATION ETA**", 
                    value=f"> <t:{int(expiry)}:R>\n> <t:{int(expiry)}:f>", 
                    inline=True
                )
                embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ ＢＹ Zytrone XD ✦")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = create_info_embed("⌛ Expired", f"UID `{uid}` EXPIRED in main whitelist.json")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = create_error_embed("❌ Not Found", f"UID `{uid}` NOT found in main whitelist.json")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    except Exception as e:
        embed = create_error_embed("⚠️ Error", f"Error checking main whitelist: {e}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="whitelistaddall", description="Add a UID to ALL server whitelists")
@app_commands.describe(
    uid="The player UID to whitelist",
    duration="Duration in hours until expiration (leave empty for auto-whitelist duration)"
)
async def whitelistaddall(interaction: discord.Interaction, uid: str, duration: float = None):
    """Add UID to ALL server whitelist files at once."""
    # Check if user can manage whitelist
    if not bot.can_manage_whitelist(interaction.user.id):
        await send_permission_denied_message(interaction, "SUB_OWNER")
        return
    
    if duration is not None and duration <= 0:
        embed = create_error_embed("❌ Invalid Duration", "Duration must be greater than 0 hours.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not uid.isdigit():
        embed = create_error_embed("❌ Invalid UID", "UID must be numeric.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Use auto-whitelist duration if not specified
    actual_duration = duration if duration is not None else get_auto_whitelist_duration()
    expiry_timestamp = time.time() + (actual_duration * 3600)
    
    added_count = 0
    failed_count = 0
    
    # Add to ALL server files
    for server in SERVERS:
        try:
            whitelist = load_whitelist(server)
            whitelist[uid] = expiry_timestamp
            save_whitelist(server, whitelist)
            added_count += 1
        except Exception as e:
            print(f"[Error] Failed to add to {server}: {e}")
            failed_count += 1
    
    # Add to main whitelist.json
    save_to_main_whitelist(uid, expiry_timestamp)
    
    expiry_datetime = datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc)
    
    embed = discord.Embed(
        color=0xFFD700, # Gold
        timestamp=expiry_datetime
    )
    embed.set_author(name="🌐 ＧＬＯＢＡＬ  ＡＵＴＨＯＲＩＺＡＴＩＯＮ")
    embed.description = (
        f"# ✨ OMNI-ACCESS GRANTED\n\n"
        f"> **SUBJECT UID:** `{uid}`\n"
        f"> **TARGET NODES:** `ALL SERVERS`\n"
        f"────────────────────────"
    )
    
    embed.add_field(
        name="⏳ **DURATION**", 
        value=f"```ansi\n\u001b[2;33m{actual_duration} HOURS\u001b[0m\n```", 
        inline=True
    )
    embed.add_field(
        name="⏰ **EXPIRES ET**", 
        value=f"> <t:{int(expiry_timestamp)}:R>\n> <t:{int(expiry_timestamp)}:f>", 
        inline=True
    )
    
    embed.add_field(
        name="📂 **DATA DUMPS**", 
        value="```\n- Antiban\n- All Server Safe\n- All Emulator Supported\n- Advanced Anticheats Added\n```", 
        inline=False
    )
    
    if failed_count > 0:
        embed.add_field(name="⚠️ **ERRORS**", value=f"> `{failed_count}` FILES FAILED TO WRITE", inline=False)

    embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ ＢＹ Zytrone XD ✦")
    
    await interaction.response.send_message(embed=embed)

# ============================
# TASK FOR EXPIRED MESSAGES
# ============================

# Task to check and update expired UID messages
@tasks.loop(seconds=30)
async def update_expired_messages():
    """Check for expired UIDs and update their messages."""
    now = time.time()
    expired_messages = []
    
    for msg_id, data in list(bot.removal_queue.items()):
        if data["expiry"] <= now:
            try:
                channel = bot.get_channel(data["channel_id"])
                if channel:
                    try:
                        message = await channel.fetch_message(msg_id)
                        
                        # Update the message
                        updated_embed = discord.Embed(
                            color=0xFF8C00 # Dark Orange
                        )
                        updated_embed.set_author(name="⌛ ＥＸＰＩＲＥＤ  ＲＥＣＯＲＤ")
                        updated_embed.description = (
                            f"# ⚠️ ACCESS TIMEOUT\n\n"
                            f"> **SUBJECT UID:** `{data['uid']}`\n"
                            f"> **SERVER NODE:** `{data['server'].upper()}`\n"
                            f"────────────────────────\n"
                            f"> Authorization has formally expired."
                        )
                        updated_embed.add_field(
                            name="⏰ **TIMESTAMP**", 
                            value=f"> <t:{int(now)}:f>", 
                            inline=True
                        )
                        updated_embed.set_footer(text=f"✦ ＤＥＶＥＬＯＰＥＤ ＢＹ Zytrone XD ✦ | Auto-Managed Status")
                        
                        # Disable the remove button if it exists
                        view = discord.ui.View(timeout=None)
                        if message.components:
                            for component in message.components[0].children:
                                if isinstance(component, discord.Button):
                                    component.disabled = True
                                    component.style = discord.ButtonStyle.secondary
                                    component.label = "Expired"
                                    view.add_item(component)
                        
                        await message.edit(embed=updated_embed, view=view)
                        
                    except discord.NotFound:
                        pass  # Message was deleted
                    
                expired_messages.append(msg_id)
                
            except Exception as e:
                print(f"[Error] Failed to update expired message: {e}")
    
    # Clean up expired messages from queue
    for msg_id in expired_messages:
        if msg_id in bot.removal_queue:
            del bot.removal_queue[msg_id]

@update_expired_messages.before_loop
async def before_update_expired_messages():
    await bot.wait_until_ready()

if __name__ == "__main__":
    print(f"[System] Whitelist Bot developed by Zytrone XD")
    print("[System] Starting Whitelist Bot...")
    
    # Set bot owner ID (replace with your Discord user ID)
    bot.owner_id = 1301461496651317291  # CHANGE THIS TO YOUR DISCORD USER ID
    
    # Initial security check
    check_developer_name()
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"[Error] Failed to start bot: {e}")
