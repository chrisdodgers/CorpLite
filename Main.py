import asyncio, discord, time, os, json
from discord import app_commands, errors
from discord.ext import commands

build_version = "v0.3.1"
# Added Humor, Jpeg, Clippy, GetImage, and Utils Cogs + updates in temp /help. Jeez I need to move this section into an actual changelog. Will happen probably.
# Previous v0.3.0 Notes
# Fixed (in PickList) an issue with attaching the Pager view when only 1 page is present. Now only attaches when more than one page is present.
# Fixed (in PickList) with PickButtons view where the view would not clear once a selection was made.
# Added/updated Comic Cog
# Added /slide to OpenCore cog
# Cleaned up a bit for initial fork and commit.
# Renamed from CorpLite.py to Main.py and updated references.

# Previous v0.2.1 Notes:
# Moved the actual app_commands back into their cogs where they belong.
# Using CogManager and Shards now:
# Cogs/Cog Manager for setup and load extensions and unload is now working (if setup defs are not async/awaited with using discord.py instead of pycord - cog will fail to load.)
# Temporarily removed reliance of settings, utils, and mute. Will revisit this.

"""To do: Add a few more cogs and revisiting preloads in CogManager..."""
# Would be cool to figure out how to integrate Settings and fix it up for being solely a user app.
# Do not plan on adding *too many* cogs as well... that isn't the point of this fork hence the name. Possibly will create an Extras folder and you can chose additional updated cogs to move into Cogs.
# Use CorpBot if you require things well out of the scope of this fork.
# Full credit to @CorpNewt (https://github.com/corpnewt) for creating CorpBot which most of the code here *is* CorpBot. Thanks for making CorpBot and the other amazing tools we use and love.
# Forked from: https://github.com/corpnewt/CorpBot.py

# Let's migrate any specific txt settings files into a single json file
# called settings_dict.json
if os.path.exists("settings_dict.json"):
    try:
        settings_dict = json.load(open("settings_dict.json"))
    except Exception as e:
        print("Could not load settings_dict.json!")
        print(" - {}".format(e))
        # Kill the process to avoid constant reloads
        os._exit(3)
else:
    settings_dict = {"token": ""}
    print("Migrating .txt files to settings_dict.json...")
    for x in ["prefix.txt", "corpSiteAuth.txt", "token.txt", "igdbKey.txt", "weather.txt", "discogs.txt",
              "currency.txt"]:
        if not os.path.exists(x): continue  # Didn't find it
        try:
            with open(x, "rb") as f:
                setting = f.read().strip().decode("utf-8")
        except Exception as e:
            print("Failed to migrate setting from {}! Ignoring.".format(x))
            print(" - {}".format(e))
            continue
        settings_dict[x[:-4].lower()] = setting
    json.dump(settings_dict, open("settings_dict.json", "w"), indent=4)

# Set intents and let's SHARD!
try:
    # Setup intents
    intents = discord.Intents.default()
    # Will most likely remove these commented out privileged intents as it currently isn't in use. Leaving it for now if I do end up needing it in the future...
    # intents.message_content = True
    # intents.messages = True
    # intents.guilds = True
    bot = commands.AutoShardedBot(
        command_prefix="", # Purposely not defining a prefix nor pulling a prefix from settings_dict. Not needed since CorpLite is intended to be used only as a user app with slash commands.
        intents=intents,
        shard_count=settings_dict.get("shard_count", 4)
    )
except:
    print("Failed to intent and SHARD it up...")

bot.settings_dict = settings_dict
bot.ready_dispatched = False
bot.ready_time = None
bot.local_client = None
bot.startup_time = time.time()


# Main bot events
@bot.event
async def on_ready():
    # Special workaround for the bot saying it's ready before all shards are ready.
    # The bot seems to dispatch the ready event every 2 shards or so.
    if not bot.ready_dispatched:
        print(" - {} of {} ready...".format(len(bot.shards), bot.shard_count))
        if len(bot.shards) >= bot.shard_count:
            print("\nAll shards ready!\n")
            bot.ready_dispatched = True
            bot.ready_time = time.time()
            bot.dispatch("all_shards_ready")


@bot.event
async def on_all_shards_ready():
    if not bot.get_cog("CogManager"):
        # We need to load shiz!
        print('Logged in as:\n{0} (ID: {0.id})\n'.format(bot.user))
        print("Invite Link:\nhttps://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8\n".format(
            bot.user.id))
        # Let's try to use the CogManager class to load things
        print("Loading CogManager...")
        await bot.load_extension(
            "Cogs.CogManager")  # added awaiting since using discord.py instead of pycord - it wants this to be async or will throw an error.
        cg_man = bot.get_cog("CogManager")
        # Load up the rest of the extensions
        cog_loaded, cog_count = await cg_man._load_extension()  # once again like my note above
        # Output the load counts

        if cog_count == 1:
            print("Loaded {} of {} cog.".format(cog_loaded, cog_count))
        else:
            print("Loaded {} of {} cogs.".format(cog_loaded, cog_count))
        print("CorpLite is ready for action!")
    await bot.tree.sync()
    print("Synchronizing Slash Commands...")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Rush"))
    print("We're listen to Rush!")

# Utility function to split long messages into chunks - Probably will remove this once I integrate the Help cog instead of the help command below.
def split_message(message, limit=2000):
    words = message.split(' ')  # Split the message into words
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 > limit:  # Check if adding the word exceeds the limit
            chunks.append(current_chunk.strip())  # Add the current chunk to chunks
            current_chunk = ""  # Reset the current chunk
        current_chunk += word + ' '  # Add the word to the current chunk

    if current_chunk.strip():  # Check if the last chunk is not empty
        chunks.append(current_chunk.strip())  # Add the last chunk to chunks

    return chunks

# Help Slash Command (temp not using the help cog - will eventually re-work and add the help cog and remove this):
@bot.tree.command(name="help", description="Learn how to use CorpLite")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
async def help(ctx):
    response = (
        f"# How to use CorpLite:\n"
        f"\n"
        f"- Use __**/iark**__ to search an Intel CPU model (e.g. `i7-10700K`) to get CPU/iGPU info.\n"
        f"- Use __**/weg**__ to search WhateverGreen's IntelHD FAQ for device-id and connector info. Use the optional `search_term` to search using a big/little endian device-id, AAPL,ig-platform-id, or AAPL,snb-platform-id.\n"
        f"- Use __**/alc**__ to search a codec name or device-id to get layouts for AppleALC.\n"
        f"- Use __**/listcodec**__ to list all codecs available *(or optionally search for one)*.\n"
        f"- Use __**/occ**__ to search OC Configuration.tex. You can search a path (e.g. Kernel Quirks DisableIoMapper) or can search for a specific item (e.g. SecureBootModel).\n"
        f"- Use __**/plist**__ to upload a config.plist to validate its plist structure.\n"
        f"- Use __**/slide**__ to upload a memmap.txt dump to calculate a slide value.\n"
        f"- Use __**/pci**__ to look up a PCI device using pci-ids.ucw.cz. Use `vvvv:dddd` where `vvvv` is the vendor id, and `dddd` is the device id (e.g. `8086:3E30`).\n"
        f"- Use __**/usb**__ to look up a USB device using usb-ids.gowdy.us. Use `vvvv:dddd` where `vvvv` is the vendor id, and `dddd` is the device id (e.g. `8086:A36D`).\n"
        f"- Use __**/encode**__ to convert data (hex, decimal, binary, base64, and ascii).\n"
        f"- Use __**/hexswap**__ to byte swap a hex value.\n"
        f"- Use __**/mem**__ to convert MiB to lhex (or vise-versa).\n"
        f"- Use __**/weather**__ to get some weather.\n"
        f"- Use __**/forecast**__ to get some weather, for 5 days or whatever.\n"
        f"- Use __**/garfield**__ *(or /gmg, /peanuts, /dilbert)* for getting some comics! Optionally, can specify a date (e.g. 02-11-2026).\n"
        f"- Use __**/randgarfield**__ *(or /randgmg, /randpeanuts, /randilbert)* for getting some comics (using a random date)!\n"
        f"- Use __**/clippy**__ to make Clippy say something.\n"
        f"- Use __**/fart**__ to make CorpLite fart.\n"
        f"- Use __**/french**__ to make CorpLite say something in French.\n"
        f"- Use __**/german**__ to make CorpLite say something in German - probably.\n"
        f"- Use __**/fry**__ to burn an uploaded image to a crisp.\n"
        f"- Use __**/jpeg**__ to jpegify an uploaded image.\n"
        f"- Use __**/poke**__ to hopefully make *something* do...something...\n"
        f"- Use __**/memetemp**__ to search and grab a meme template.\n"
        f"- Use __**/meme**__ to use a meme template id and to make some memes.\n"
        f"- Use __**/slap**__ to slap someone by specifying who you want to slap (e.g. @chris_dodgers).\n"
        f"- Use __**/zalgo**__ to enter a message that turns into something...interesting.\n"
        f"- Use __**/extensions**__ to view what cogs are running.\n"
        f"\n"
        f"## About CorpLite:\n"
        f"\n"
        f"This is test concept of a light version of CorpBot - hence the name CorpLite. \n"
        f"CorpLite is designed to run solely as a user app using slash commands. A few key cogs have been added, and possibly a few more will be added at a later time. \n"
        f"Since CorpLite is built to be solely used as a user app - it can be used in DMs and servers that allow the use of external apps. \n"
        f"---------------------------------------\n"
        f"`Full credit to @corpnewt for creating CorpBot https://github.com/corpnewt/CorpBot.py and for creating many of the tools we use and love.` \n"
        f"`Current running build of CorpLite: {build_version} - @chris_dodgers`\n"

    )
    # Split response into multiple messages since it exceeds the 2000 char limit
    chunks = split_message(response)
    await ctx.response.send_message(content=chunks[0], ephemeral=True)
    # Send follow-up messages if there are more chunks
    for chunk in chunks[1:]:
        if chunk.strip():  # Check if the chunk is not empty
            await ctx.followup.send(content=chunk[:2000], ephemeral=True)

# Run the bot
try:
    print("Starting up {} shard{}...".format(bot.shard_count, "" if bot.shard_count == 1 else "s"))
    bot.run(settings_dict.get("token", ""))
except errors.LoginFailure as e:
    print("\nSomething went wrong logging in: {}\n".format(e))
    if "token" in str(e).lower():
        print("You can create/reset your token in the Developer Portal:\n")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Select your bot under 'My Applications' or click 'New Application' to")
        print("   create a new bot")
        print("3. Click 'Bot' in the menu on the left side of the page")
        print("4. Click 'Reset Token'")
        print("   - DO NOT SHARE THIS TOKEN WITH ANYONE")
        print("   - YOU CAN ONLY VIEW IT ONCE")
        print("5. Copy the token to the clipboard")
        print("")
        os._exit(6)
    os._exit(3)
except RuntimeError as e:
    print("Dirty shutdown - runtime error minimized:\n - {}".format(e))
