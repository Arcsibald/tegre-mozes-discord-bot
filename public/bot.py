import random
import discord
from discord.ext import commands
import os
import json
import logging

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bejelentkezve mint: {bot.user}")
    load_reaction_role_messages()

# -------------------------------------
# Debug support
# -------------------------------------

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# TODO: Logging functions

# -------------------------------------
# Server join
# -------------------------------------

@bot.event
async def on_guild_join(guild):
    """
    Activates when added to server.
    """
    # Searches for the first text channel
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            bot_message = await channel.send(
                f"Sziasztok!\n"
                f"Bizony, én vagyok az, Tegré Mozes... <:tegre_logo:1328752657157984379>\n"
                f"Egyelőre leginkább a csatornákra való fel és leiratkozásban fogok segíteni, de később akár más ügyben is kereshettek majd. 😉"
            )
            
            emoji = discord.PartialEmoji(name="tegre_logo", id=1328752657157984379)
            await bot_message.add_reaction(emoji)

            break

# -------------------------------------
# Welcome messages
# -------------------------------------

WELCOME_MESSAGES = [
    "Dejóóóóóóóóó, megjött {mention} is! 😍",
    "Szia {mention}! Szuper, hogy Te is csatlakoztál! 😊",
    "Szevasz {mention}! Üdv a családi Discord-szerón! 😎",
    "Hoppá-hoppá, ki van itt? Csak nem {mention}?! 🤯",
    "Dejóóóóóóóóó, megjött {mention} is! 🎉",
    "Helló {mention}! Nagyon örülünk, hogy itt vagy! 🥳",
    "Ba dum tss 🥁: megérkezett {mention}!",
    "Naaaaa! Nemár, hogy csak én üdvözöljem {mention}-t... 🙄",
    "Itt van megjött {mention}, aki a fagylaltját ...!\n(Valaki tud valami jó rímet?🥵)"
]

@bot.event
async def on_member_join(member):
    """
    Event for when someone joins the server.
    """
    guild = member.guild
    channel = None

    for text_channel in guild.text_channels:
        if text_channel.permissions_for(guild.me).send_messages:
            channel = text_channel
            break

    if channel:
        welcome_message = random.choice(WELCOME_MESSAGES).format(mention=member.mention)
        await channel.send(welcome_message)

# -------------------------------------
# Reaction role messages
# -------------------------------------

"""
Dictionary to store messages for role reactions
Format: {message_id: {emoji: role_name}}
"""
reaction_role_messages = {}

def save_reaction_role_messages():
    with open("reaction_role_messages.json", "w", encoding="utf-8") as file:
        json.dump(reaction_role_messages, file, indent=4, ensure_ascii=False)

def load_reaction_role_messages():
    global reaction_role_messages
    try:
        with open("reaction_role_messages.json", "r", encoding="utf-8") as file:
            reaction_role_messages = json.load(file)
            reaction_role_messages = {int(message_id): roles for message_id, roles in reaction_role_messages.items()}
    except FileNotFoundError:
        reaction_role_messages = {}

@bot.command()
async def rr(ctx, message_body: str, *emoji_role_pairs):
    """
    Command to create a role-reaction message.
    Usage: !rr "Your message body" :emoji1: Role1 :emoji2: Role2 ...
    """
    guild = ctx.guild
    reaction_roles = {}

    # Parse emoji-role pairs
    for i in range(0, len(emoji_role_pairs), 2):
        emoji = emoji_role_pairs[i]
        role_name = emoji_role_pairs[i + 1]

        # Ensure the role exists
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await ctx.send(f"Role `{role_name}` does not exist.")
            return

        reaction_roles[emoji] = role_name

    # Send the bot's message
    bot_message = await ctx.send(message_body)
    for emoji in reaction_roles.keys():
        await bot_message.add_reaction(emoji)

    # Save the message ID and associated reaction-role pairs
    reaction_role_messages[bot_message.id] = reaction_roles
    save_reaction_role_messages()

    # Delete the command message
    await ctx.message.delete()

    await ctx.send("Reaction role message created successfully!", delete_after=5)

@bot.command()
async def crr(ctx):
    """
    Command to check saved role-reaction messages.
    """
    await ctx.send(f"Betöltött adat: {reaction_role_messages}")


@bot.command()
async def subscription_channel(ctx         : commands.context.Context,
                               emoji       : str = None,
                               message_body: str = None,
                               role_name   : str = None,
                               subs_channel: str = None):

    channel   = ctx.channel

    # Set default values
    if emoji is None:
        emoji = ":eyes:"
    if message_body is None:
        message_body = f"Reagálj {emoji} emojival erre az üzenetre, hogy feliratkozz a {channel.name} csatornára"
    if role_name is None:
        role_name = f"feliratkozas-{channel.name}"
    if subs_channel is None:
        subs_channel = "feliratkozasok"
    try:
        raise ValueError("Tolmácsot szeretnék kérni")
    except Exception as e:
        error_msg = f"""Valami baj történt. Úgy értettem, a következő paramétereket adtad meg:
- feliratkozós emoji: `{emoji}`
- feliratkozó üzenet:
    > {message_body.replace("\n","\n    > ")}
- létrehozandó rang neve: `{role_name}`
- csatorna, ahol feliratkoznak majd erre: `{subs_channel}`
A következő hibát kaptam: ```{str(e)}```"""
        await ctx.send(error_msg)




"""
Managing member reactions on RR messages.
"""
@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id in reaction_role_messages:
        
        guild = discord.utils.get(bot.guilds, id=payload.guild_id)
        channel = discord.utils.get(guild.text_channels, id=payload.channel_id)

        member = guild.get_member(payload.user_id)
        if member is None:
            member = await guild.fetch_member(payload.user_id)

        emoji = str(payload.emoji)
        if emoji in reaction_role_messages[payload.message_id]:
            role_name = reaction_role_messages[payload.message_id][emoji]
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role)
                print(f"Added role `{role_name}` to {member.name} for reacting with `{emoji}`")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id in reaction_role_messages:
        guild = discord.utils.get(bot.guilds, id=payload.guild_id)
        member = guild.get_member(payload.user_id)

        if member is None:
            member = await guild.fetch_member(payload.user_id)

        emoji = str(payload.emoji)
        if emoji in reaction_role_messages[payload.message_id]:
            role_name = reaction_role_messages[payload.message_id][emoji]
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.remove_roles(role)
                print(f"Removed role `{role_name}` from {member.name} for removing reaction `{emoji}`")

# -------------------------------------
# Running bot
# -------------------------------------

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
