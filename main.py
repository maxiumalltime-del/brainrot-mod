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
    input='''Check if the following message contains EXTREME internet brainrot.

Brainrot INCLUDES:
- Contextless meme phrases (e.g., “tung tung sahur”)
- Repetitive nonsense words
- Number memes (67, 420, 69420, etc.)
- TikTok / shorts meme spam with no semantic meaning

Brainrot DOES NOT include:
- Normal slang
- Puns
- Playful spelling
- Real words with meaning

Reply ONLY with:
DELETE → if brainrot
CLEAR → otherwise

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