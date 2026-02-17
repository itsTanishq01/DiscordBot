# Discord Automod Bot

A powerful, customizable moderation bot for Discord servers. Features 6 advanced filters, role exemptions, mod-logging, and a full configuration system via slash commands.

**Built with GSD** (Get Stuff Done) workflow.

## Features

### 🛡️ Core Filters
1. **Spam Filter**: Limits X messages per Y seconds per user.
2. **Attachment Filter**: Limits attachment count and blocks specific file types.
3. **Mention Filter**: Limits mention count and blocks @everyone/@here.
4. **Message Limit Filter**: Limits lines, words, and characters per message.
5. **Link Filter**: Blocks non-whitelisted URLs and Discord invites (supports regex).
6. **Word Filter**: Blocks banned words (exact, partial, or regex match).

### ⚙️ System Features
- **Configurable**: Every threshold and toggle is adjustable per-server.
- **Exemptions**: Exempt specific roles from specific filters.
- **Mod Log**: Rich embeds sent to a configured channel for every violation.
- **Hybrid Commands**: Full support for both Slash Commands (`/`) and Prefix Commands (`.`).

## Installation

### Prerequisites
- Python 3.8+
- A Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/discord-automod-bot.git
   cd discord-automod-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file:
   ```env
   BOT_TOKEN=your_token_here
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

## Configuration

### Slash Commands (Recommended)
- `/config view` — Check current settings
- `/modlog set <channel>` — Set log channel
- `/spam set <max> <window>` — Configure spam filter
- `/attachment block <filetype>` — Block file types (e.g. `exe`)
- `/linkfilter whitelist_add <domain>` — Allow specific domains
- `/wordfilter add <word>` — Ban a word
- `/exempt add <rule> <role>` — Exempt a role from a filter

### Prefix Commands
Default prefix is `.`. Change with `.prefix set <new_prefix>`.
- `.config view`
- `.modlog set #channel`
- `.spam enable` / `.spam disable`
- `.linkfilter regex_add <pattern>`

## Deployment

### Render
This bot is configured for [Render](https://render.com).
1. Create a new **Worker Service**.
2. Connect your repository.
3. Add a **Disk** named `bot-data` mounted at `/data` (Crucial for saving config!).
4. Add environment variable `BOT_TOKEN`.

### Docker / Other VPS
Ensure the database file (`bot.db`) is mounted to a persistent volume, or use the `DATA_DIR` pattern if modifying the code.
