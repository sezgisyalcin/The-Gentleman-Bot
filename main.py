import os
import sqlite3
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

# Optional: local dev for .env (Railway doesn't need this)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing. Set it as an environment variable (Railway Variables)."
    )

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

DB_PATH = os.getenv("DB_PATH", "bot.sqlite")


def db_init() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS drops_watch (
                guild_id INTEGER NOT NULL,
                game TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, game)
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                guild_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                channel_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, topic)
            );
            """
        )
        conn.commit()


def db_set_channel(guild_id: int, topic: str, channel_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO channels (guild_id, topic, channel_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, topic) DO UPDATE SET channel_id=excluded.channel_id;
            """,
            (guild_id, topic, channel_id),
        )
        conn.commit()


def db_get_channel(guild_id: int, topic: str) -> Optional[int]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT channel_id FROM channels WHERE guild_id=? AND topic=?;",
            (guild_id, topic),
        )
        row = cur.fetchone()
        return int(row[0]) if row else None


def db_watch_drop(guild_id: int, game: str) -> bool:
    game = game.strip()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO drops_watch (guild_id, game) VALUES (?, ?);",
                (guild_id, game),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def db_unwatch_drop(guild_id: int, game: str) -> bool:
    game = game.strip()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM drops_watch WHERE guild_id=? AND game=?;",
            (guild_id, game),
        )
        conn.commit()
        return cur.rowcount > 0


def db_list_drops(guild_id: int) -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT game FROM drops_watch WHERE guild_id=? ORDER BY game ASC;",
            (guild_id,),
        )
        return [r[0] for r in cur.fetchall()]


@bot.event
async def on_ready():
    db_init()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s). Logged in as {bot.user}")
    except Exception as e:
        print(f"Command sync failed: {e}")


def require_guild(interaction: discord.Interaction) -> bool:
    return interaction.guild is not None


@bot.tree.command(name="ping", description="Check if the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong.")


# -------------------------
# Deals / Free / Bundles (placeholders for now)
# -------------------------

@bot.tree.command(name="free", description="Show currently free games (placeholder).")
@app_commands.describe(store="Optional store filter (e.g., epic, gog)")
async def free(interaction: discord.Interaction, store: Optional[str] = None):
    store_txt = f" (store: {store})" if store else ""
    await interaction.response.send_message(
        f"Free games{store_txt}: Coming next. This command will fetch Epic/GOG etc."
    )


@bot.tree.command(name="deals", description="Show hot deals (placeholder).")
@app_commands.describe(store="Optional store filter (e.g., steam, gog, humble)")
async def deals(interaction: discord.Interaction, store: Optional[str] = None):
    store_txt = f" (store: {store})" if store else ""
    await interaction.response.send_message(
        f"Deals{store_txt}: Coming next. This will use deal aggregators (e.g., ITAD/CheapShark)."
    )


@bot.tree.command(name="bundles", description="Show active bundles (placeholder).")
@app_commands.describe(source="Optional source (e.g., humble, fanatical)")
async def bundles(interaction: discord.Interaction, source: Optional[str] = None):
    src_txt = f" (source: {source})" if source else ""
    await interaction.response.send_message(
        f"Bundles{src_txt}: Coming next. This will include Humble bundles, Fanatical etc."
    )


# -------------------------
# Resources: magazines/books/archives (curated, safe)
# -------------------------

@bot.tree.command(
    name="resources",
    description="Free-access gaming resources (magazines/books/archives)."
)
@app_commands.describe(category="magazines | books | archives")
async def resources(interaction: discord.Interaction, category: str):
    category = category.lower().strip()

    if category not in {"magazines", "books", "archives"}:
        await interaction.response.send_message(
            "Invalid category. Use: magazines | books | archives",
            ephemeral=True,
        )
        return

    items = []
    if category == "magazines":
        items = [
            ("Video Game History Foundation (Library/Archive)", "https://gamehistory.org/"),
            ("Internet Archive — video game magazines (search)", "https://archive.org/search?query=video+game+magazine"),
            ("Retromags (index/community)", "https://retromags.com/"),
        ]
    elif category == "books":
        items = [
            ("The Video Game Library (catalog)", "https://www.thevideogamelibrary.org/"),
            ("Internet Archive — game history books (search)", "https://archive.org/search?query=video+game+history+book"),
        ]
    elif category == "archives":
        items = [
            ("Internet Archive — Software & Games", "https://archive.org/details/software"),
            ("Video Game History Foundation", "https://gamehistory.org/"),
            ("The Strong National Museum of Play (museum + digital)", "https://www.museumofplay.org/"),
        ]

    embed = discord.Embed(
        title=f"Free-access resources: {category}",
        description="Curated links (reference-only).",
    )
    for name, url in items:
        embed.add_field(name=name, value=url, inline=False)

    await interaction.response.send_message(embed=embed)


# -------------------------
# Gear: official stores hub (reference-only)
# -------------------------

@bot.tree.command(name="gear", description="Official gaming gear stores (reference-only).")
async def gear(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Official gear stores",
        description="Official brand stores (reference-only).",
    )
    embed.add_field(name="Logitech G", value="https://www.logitechg.com/", inline=False)
    embed.add_field(name="Razer", value="https://www.razer.com/", inline=False)
    embed.add_field(name="SteelSeries", value="https://steelseries.com/", inline=False)
    embed.add_field(name="Corsair", value="https://www.corsair.com/", inline=False)
    await interaction.response.send_message(embed=embed)


# -------------------------
# Awards: starter list
# -------------------------

@bot.tree.command(name="awards", description="Major international game awards (starter list).")
async def awards(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Major game awards",
        description="Starter list. We'll add current + historical lookups next.",
    )
    embed.add_field(name="The Game Awards", value="https://thegameawards.com/", inline=False)
    embed.add_field(name="BAFTA Games Awards", value="https://www.bafta.org/awards/games", inline=False)
    embed.add_field(name="D.I.C.E. Awards (AIAS)", value="https://www.interactive.org/awards/", inline=False)
    embed.add_field(name="Game Developers Choice Awards (GDC)", value="https://gdconf.com/awards", inline=False)
    embed.add_field(name="Golden Joystick Awards", value="https://www.gamesradar.com/goldenjoystickawards/", inline=False)
    embed.add_field(name="Independent Games Festival (IGF)", value="https://igf.com/", inline=False)
    await interaction.response.send_message(embed=embed)


# -------------------------
# Drops: watchlist (game-name based)
# -------------------------

@bot.tree.command(
    name="drops_watch",
    description="Watch a game for Twitch Drops announcements (game-name based)."
)
@app_commands.describe(game="Game name, e.g., VALORANT")
async def drops_watch(interaction: discord.Interaction, game: str):
    if not require_guild(interaction):
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    added = db_watch_drop(interaction.guild_id, game)
    if added:
        await interaction.response.send_message(f"Watching Drops for: **{game.strip()}**")
    else:
        await interaction.response.send_message(f"Already watching: **{game.strip()}**", ephemeral=True)


@bot.tree.command(name="drops_unwatch", description="Stop watching a game for Twitch Drops announcements.")
@app_commands.describe(game="Game name")
async def drops_unwatch(interaction: discord.Interaction, game: str):
    if not require_guild(interaction):
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    removed = db_unwatch_drop(interaction.guild_id, game)
    if removed:
        await interaction.response.send_message(f"Removed from watchlist: **{game.strip()}**")
    else:
        await interaction.response.send_message(f"Not found in watchlist: **{game.strip()}**", ephemeral=True)


@bot.tree.command(name="drops_watchlist", description="List watched games for Twitch Drops.")
async def drops_watchlist(interaction: discord.Interaction):
    if not require_guild(interaction):
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    games = db_list_drops(interaction.guild_id)
    if not games:
        await interaction.response.send_message("No watched games yet. Use /drops_watch game:<name>")
        return

    embed = discord.Embed(title="Drops watchlist", description="\n".join(f"• {g}" for g in games))
    await interaction.response.send_message(embed=embed)


# -------------------------
# Setchannel (admin)
# -------------------------

@bot.tree.command(name="setchannel", description="Set a channel for a topic (admin).")
@app_commands.describe(topic="free | deals | bundles | drops | awards | resources", channel="Target channel")
async def setchannel(interaction: discord.Interaction, topic: str, channel: discord.TextChannel):
    if not require_guild(interaction):
        await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
        return

    topic = topic.lower().strip()
    allowed = {"free", "deals", "bundles", "drops", "awards", "resources"}
    if topic not in allowed:
        await interaction.response.send_message(
            f"Invalid topic. Choose one of: {', '.join(sorted(allowed))}",
            ephemeral=True,
        )
        return

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You need 'Manage Server' permission to use this.",
            ephemeral=True,
        )
        return

    db_set_channel(interaction.guild_id, topic, channel.id)
    await interaction.response.send_message(f"Set **{topic}** channel to {channel.mention}")


bot.run(DISCORD_TOKEN)
