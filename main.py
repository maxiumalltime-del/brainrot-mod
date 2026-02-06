import discord

from openai import OpenAI
import asyncio
import os

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

intents = discord.Intents.default()

intents.message_content = True

dcclient = discord.Client(intents=intents)

@dcclient.event
async def on_ready():
    print(f'We have logged in as {dcclient.user}')
@dcclient.event
async def on_message(message):
    if message.author == dcclient.user:
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