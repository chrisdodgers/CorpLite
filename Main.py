import asyncio, discord, time, os, json
from discord import app_commands, errors
from discord.ext import commands

build_version = "v0.4.0"
# Finally yeeted the growing changelog out of here. Not sure why I put one in here to begin with, at least that you could see if you are reading this.

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
