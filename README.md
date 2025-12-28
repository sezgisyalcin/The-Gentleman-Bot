# Gaming Hub Discord Bot (Railway-ready)

A Python (discord.py) Discord bot scaffold designed for Railway deployment.

## Features (current scaffold)
- Slash commands (English):
  - /ping
  - /free (placeholder)
  - /deals (placeholder)
  - /bundles (placeholder)
  - /resources (magazines | books | archives)
  - /gear
  - /awards
  - /drops_watch, /drops_unwatch, /drops_watchlist
  - /setchannel (admin)
- SQLite storage for:
  - Drops watchlist
  - Per-topic channel routing

## Local run
1. Create a Discord application + bot token in Discord Developer Portal.
2. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
3. Set env var:
   - Windows (PowerShell): `setx DISCORD_TOKEN "YOUR_TOKEN"`
   - macOS/Linux: `export DISCORD_TOKEN="YOUR_TOKEN"`
4. Run:
   ```bash
   python main.py
   ```

## Railway deploy
1. Push this repo to GitHub.
2. Railway: New Project -> Deploy from GitHub.
3. Set Variables:
   - `DISCORD_TOKEN` = your Discord bot token
   - (optional) `DB_PATH` = `bot.sqlite`
4. Deploy. Check logs for "Synced X command(s)".

## Discord OAuth2 invite
In Discord Developer Portal:
- OAuth2 -> URL Generator
  - Scopes: `bot`, `applications.commands`
  - Permissions: Send Messages, Embed Links, Read Message History
Use the generated URL to invite the bot to your server.
