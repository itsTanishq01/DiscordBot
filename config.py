import discord

defaultPrefix = "."

embedColor = 0xFF4444

requiredIntents = discord.Intents.default()
requiredIntents.messages = True
requiredIntents.message_content = True
requiredIntents.guilds = True
requiredIntents.members = True

defaultConfig = {
    "spamMaxMessages": "5",
    "spamTimeWindow": "10",
    "spamEnabled": "1",
    "maxAttachments": "5",
    "blockedFileTypes": "[]",
    "attachmentEnabled": "1",
    "maxMentions": "10",
    "blockEveryone": "0",
    "blockHere": "0",
    "mentionEnabled": "1",
    "maxLines": "30",
    "maxWords": "500",
    "maxCharacters": "2000",
    "messageLimitEnabled": "1",
    "linkFilterEnabled": "0",
    "linkRegexPatterns": "[]",
    "wordFilterEnabled": "0",
    "wordFilterPartialMatch": "0",
    "wordFilterRegex": "0",
    "modLogChannel": "",
    "prefix": ".",
}
