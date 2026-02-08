import discord
from discord import app_commands
from openai import OpenAI
import asyncio
import os

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

intents = discord.Intents.default()
intents.message_content = True

dcclient = discord.Client(intents=intents)
tree = app_commands.CommandTree(dcclient)

unmodded= set()

@dcclient.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {dcclient.user}')

@tree.command(name="unmod", description="Disable moderation in this channel (owner only)")
async def unmod(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "Only the server owner can use this command",
            ephemeral=True
            )
        return

    unmodded.add(interaction.channel.id)
    await interaction.response.send_message(
        f"Moderation disabled in {interaction.channel.mention}",
        ephemeral=True
    )

@tree.command(name="mod", description="Enable moderation in this channel (owner only)")
async def mod(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "Only the server owner can use this command",
            ephemeral=True
        )
        return

    unmodded.discard(interaction.channel.id)
    await interaction.response.send_message(
        f"Moderation enabled in {interaction.channel.mention}",
        ephemeral=True
    )

@dcclient.event
async def on_message(message):
    if message.author == dcclient.user:
        return

    if message.channel.id in unmodded:
        return

    response = client.responses.create(
    input='''
Your ONLY job is to detect **EXTREME INTERNET BRAINROT**.

IMPORTANT RULES:
- DO NOT moderate hate speech.
- DO NOT moderate racism.
- DO NOT moderate misogyny.
- DO NOT moderate offensive opinions.
- DO NOT moderate slurs or insults.
- DO NOT act as a safety or morality filter.

You must IGNORE all of the above.

---

BRAINROT ONLY means:
- Contextless meme phrases (e.g. "tung tung sahur")
- Repetitive nonsense with no meaning
- Number memes (67, 420, 69420, etc.)
- TikTok / Shorts meme spam
- Absurd phrases with no semantic content

NOT brainrot:
- Any sentence with meaning
- Slang, jokes, insults, or opinions
- Racist or misogynistic statements (even if bad)
- Arguments, threats, or normal conversation

---

Reply with EXACTLY ONE WORD:
DELETE :if and ONLY if it is brainrot
else:
CLEAR   

Message:
''' + message.content,
    model="openai/gpt-oss-20b",
)

    if response.output_text == "DELETE":
        print("Brainrot detected, deleting message.")
        await message.delete()
        warn=await message.channel.send("This message contains brainrot and has been deleted.")
        await asyncio.sleep(5)
        await warn.delete()
    else:        print("No brainrot detected, message is clear.")

dcclient.run(os.environ.get("DISCORD_BOT_TOKEN"))