import discord
from discord import app_commands
from openai import OpenAI
import asyncio
import os

client = OpenAI( api_key=os.environ["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1", )
intents = discord.Intents.default()
intents.message_content = True

delete_queue = asyncio.Queue()


dcclient = discord.Client(intents=intents)
tree = app_commands.CommandTree(dcclient)

semaphore = asyncio.Semaphore(10)

unmodded= set()
processed_messages = set()

@dcclient.event
async def on_ready():

    await tree.sync()
    print(f'We have logged in as {dcclient.user}')
    dcclient.loop.create_task(delete_worker())

@tree.command(name="unmod", description="Disable moderation in this channel (owner only)")

async def unmod(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message( "Only the server owner can use this command", ephemeral=True )
        return
    
    unmodded.add(interaction.channel.id)
    await interaction.response.send_message( f"Moderation disabled in {interaction.channel.mention}", ephemeral=True )

@tree.command(name="mod", description="Enable moderation in this channel (owner only)")
async def mod(interaction: discord.Interaction):

    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message( "Only the server owner can use this command", ephemeral=True )
        return 
    
    unmodded.discard(interaction.channel.id)
    await interaction.response.send_message( f"Moderation enabled in {interaction.channel.mention}", ephemeral=True )

async def delete_worker():
    await dcclient.wait_until_ready()
    while not dcclient.is_closed():
        message = await delete_queue.get()

        try:
            me = message.guild.me
            if me and me.guild_permissions.manage_messages:
                await message.delete()

                warn = await message.channel.send(
                    "This message contains brainrot and has been deleted.",
                    allowed_mentions=discord.AllowedMentions.none()
                )

                await asyncio.sleep(5)
                await warn.delete()

                await asyncio.sleep(0.4)

        except Exception as e:
            print("Delete error:", e)

        delete_queue.task_done()


@dcclient.event
async def on_message(message):

    if message.author.bot:
        return

    if not message.guild:
        return

    content = message.content.strip().lower()

    if (
    content.isdigit() or
    content in {"67"} 
    ):
       await delete_queue.put(message)
       return

    if message.id in processed_messages:
        return
    
    processed_messages.add(message.id)

    
    if not message.content.strip():
        return
    
    if message.channel.id in unmodded:
        return
    
    prompt = f"""your ONLY job is to detect **EXTREME INTERNET BRAINROT**. IMPORTANT RULES:
          - DO NOT moderate hate speech.
          - DO NOT moderate racism.
          - DO NOT moderate misogyny.
          - DO NOT moderate offensive opinions.
          - DO NOT moderate slurs or insults.
          - DO NOT act as a safety or morality filter.
          You must IGNORE all of the above.

          --- BRAINROT ONLY means:
          - Contextless meme phrases (e.g. "tung tung sahur")
          - Repetitive nonsense with no meaning
          - Number memes (67, 420, 69420, etc.)
          - TikTok / shorts meme spam with no semantic meaning Brainrot DOES NOT include:
          - Weapon names or model numbers (M1911, M4A1, AK-47, etc.)
          - Game update announcements - Technical identifiers
          - Version numbers -the word "brainrot" itself when used in a context that is clearly self-aware and not just a meme phrase
          - Normal slang
          - Puns
          - Playful spelling
          - Real words with meaning Reply ONLY with: 
          "DELETE" if brainrot 
          "CLEAR"  otherwise Message:
          {message.content}""" 
    
    try:
        async with semaphore:
            response = await asyncio.to_thread(
                client.responses.create,
                input=prompt,
                model="openai/gpt-oss-120b",
            )
            print("API response:", response.output_text)
    except Exception as e:
        print("API error:", e)
        return
 
    
    result = (
    response.output_text.strip()
    if hasattr(response, "output_text") and response.output_text
    else ""
)

    if "DELETE" in result.upper():
        await delete_queue.put(message)

token = os.environ.get("DISCORD_BOT_TOKEN")

if not token:
    raise RuntimeError("DISCORD_BOT_TOKEN not set")

dcclient.run(token)