# 📘 Discord Automod Bot — User Guide

This guide explains how to configure and manage the Automod Bot for your server.

## 🚀 Quick Start

1. **Invite the Bot**: Use the invite link generated from the Developer Portal.
2. **Set the Log Channel**: This is where deleted messages are logged.
   - Command: `/modlog set #channel`
   - Example: `/modlog set #mod-logs`
3. **Check Defaults**: View the current configuration to see what's enabled.
   - Command: `/config view`

---

## 🛡️ Configuring Filters

All filters can be configured via **Slash Commands** (`/`) or **Prefix Commands** (`.`).

### 1. Spam Filter
Prevents users from sending too many messages too quickly.
- **Enable**: `/spam enable`
- **Configure**: `/spam set <max_messages> <time_window>`
- **Default**: 5 messages in 10 seconds.
- *Example*: `/spam set 3 5` (Strict: 3 messages in 5 seconds)

### 2. Mention Filter
Prevents mass pings and spam mentions.
- **Enable**: `/mention enable`
- **Limit Count**: `/mention limit <count>` (Max mentions per message)
- **Block Mass Pings**:
  - `/mention blockeveryone true` (Blocks `@everyone` and `@here`)
  - `/mention blockhere true` (Blocks just `@here`)

### 3. Link Filter
Blocks all links *except* the ones you whitelist.
- **Enable**: `/linkfilter enable`
- **Whitelist a Domain**: `/linkfilter whitelist_add <domain>`
- *Example*: `/linkfilter whitelist_add youtube.com` (Allows YouTube links)
- **Block Discord Invites**: The bot automatically blocks Discord invites unless the server is whitelisted (e.g., `discord.gg`).

### 4. Word Filter
Blocks specific words or phrases.
- **Enable**: `/wordfilter enable`
- **Add Word**: `/wordfilter add <word>`
- *Example*: `/wordfilter add badword`
- **Matching Modes**:
  - **Exact** (Default): Blocks "badword" but allows "scunthorpe".
  - **Partial**: `/wordfilter partial true` (Blocks "scunthorpe" because it contains "badword").
  - **Regex**: `/wordfilter regex true` (Advanced pattern matching).

### 5. Attachment Filter
Limits files and blocks dangerous extensions.
- **Enable**: `/attachment enable`
- **Limit Count**: `/attachment limit <count>`
- **Block File Type**: `/attachment block <extension>`
- *Example*: `/attachment block exe` (Blocks .exe files)

### 6. Message Limits
Prevents walls of text.
- **Enable**: `/msglimit enable`
- **Configure**:
  - `/msglimit lines <count>` (Max newlines)
  - `/msglimit words <count>`
  - `/msglimit characters <count>`

---

## 👮 Role Exemptions
You probably don't want your **Admins** or **Moderators** to be affected by these filters. You can exempt them!

- **Command**: `/exempt add <rule> <role>`
- **Rules available**: `spam`, `attachment`, `mention`, `messageLimit`, `link`, `word`.

**Examples**:
- Let Mods post links:
  `/exempt add link @Moderator`
- Let Admins spam:
  `/exempt add spam @Admin`
- See who is exempt:
  `/exempt list link`

---

## ❓ FAQ

**Q: I changed the prefix but forgot it!**
A: The Slash Command `/prefix set` will always work, even if you forget the text prefix.

**Q: The bot isn't deleting messages?**
A:
1. Check if the bot has **Administrator** or **Manage Messages** permission.
2. Check if the filter is enabled (`/config view`).
3. Check if your role is exempt.
4. Ensure the bot's role is **higher** than the user's role in the Server Settings.

**Q: Can I use text commands instead of Slash commands?**
A: Yes! Replace `/` with `.` (or your custom prefix).
- Example: `.spam enable` instead of `/spam enable`.
