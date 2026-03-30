import asyncio, cpuinfo, discord, os, re, psutil, platform, time, sys, fnmatch, subprocess, json, struct, shutil, \
    tempfile
from PIL import Image
from discord import app_commands
from discord.ext import commands
from Cogs import Utils, Settings, ReadableTime, GetImage, ProgressBar, Message, DL

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


async def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    await bot.add_cog(Bot(bot, settings, sys.argv[0], 'python'))


# This is the Bot module - it contains things like nickname, status, etc

class Bot(commands.Cog):

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings, path=None, pypath=None):
        self.bot = bot
        self.settings = settings
        self.startTime = time.time()
        self.path = path
        self.pypath = pypath
        self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
        self.message_regex = re.compile(
            r"(?i)(https:\/\/(www\.)?(\w+\.)*discord(app)?\.com\/channels\/(@me|\d+)\/\d+\/)?(?P<message_id>\d+)")
        self.is_current = False
        global Utils
        Utils = self.bot.get_cog("Utils")

    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")

    @commands.Cog.listener()
    async def on_unloaded_extension(self, ext):
        # Called to shut things down
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        self.is_current = False

    @commands.Cog.listener()
    async def on_loaded_extension(self, ext):
        # See if we were loaded
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        await self.bot.wait_until_ready()
        self.is_current = True
        self.bot.loop.create_task(self.status_loop())


    async def status_loop(self):
        # Helper method to loop through and ensure the status remains
        while not self.bot.is_closed():
            try:
                if not self.is_current:
                    # Bail if we're not the current instance
                    return
                await self._update_status()
            except Exception as e:
                print(str(e))
            await asyncio.sleep(3600)  # runs only every 60 minutes (3600 seconds)

    # Ping Slash Command
    @app_commands.command(name="ping", description="Feeling lonely?")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def ping(self, interaction: discord.Interaction):
        """Feeling lonely?"""
        ms = round(self.bot.latency * 1000)  # latency is in seconds, convert to ms
        msg = '*{}*, ***PONG!*** (~{}ms)'.format(interaction.user.mention, ms)
        await interaction.response.send_message(msg, allowed_mentions=discord.AllowedMentions.all())

    # Uptime Slash Command
    @app_commands.command(name="uptime", description="Lists the bot's uptime.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def uptime(self, interaction: discord.Interaction):
        """Lists the bot's uptime."""
        try:
            try:
                startup_time = int(self.bot.startup_time)
            except AttributeError:
                startup_time = int(self.startTime)
        except:
            time_string = "too long to count"
        time_string = ReadableTime.getReadableTimeBetween(startup_time, int(time.time()))
        await interaction.response.send_message("I've been up for *{}*.".format(time_string))

    def _gather_host_info(self, interaction: discord.Interaction):
        cpuName = cpuinfo.get_cpu_info().get("brand_raw", "Unknown")
        cpuThred = os.cpu_count()
        cpuUsage = psutil.cpu_percent(interval=1)
        memStats = psutil.virtual_memory()
        memUsedGB = round(memStats.used / 1024 ** 3, 1)
        memTotalGB = round(memStats.total / 1024 ** 3, 1)
        memPerc = round(memUsedGB / memTotalGB * 100, 1)
        currentOS = platform.platform()
        system = platform.system()
        release = platform.release()
        version = platform.version()
        processor = platform.processor()
        botMember = self.bot.user.id
        botName = self.bot.user.name
        currentTime = int(time.time())
        timeString = ReadableTime.getReadableTimeBetween(psutil.boot_time(), currentTime)
        pythonMajor = sys.version_info.major
        pythonMinor = sys.version_info.minor
        pythonMicro = sys.version_info.micro
        pythonRelease = sys.version_info.releaselevel
        pyBit = struct.calcsize("P") * 8
        process = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'], shell=False, stdout=subprocess.PIPE)
        # git_head_hash = process.communicate()[0].strip() - will revisit this

        threadString = 'thread'
        if not cpuThred == 1:
            threadString += 's'

        msg = '***{}\'s*** **Home:**\n'.format(botName)
        msg += '```\n'
        msg += 'OS        : {}\n'.format(currentOS)
        msg += 'Hostname  : {}\n'.format(platform.node())
        msg += 'Processor : {}\n'.format(cpuName)
        msg += 'Language  : Python {}.{}.{} {} ({} bit)\n'.format(pythonMajor, pythonMinor, pythonMicro, pythonRelease,
                                                                  pyBit)
        #	msg += 'Commit    : {}\n\n'.format(git_head_hash.decode("utf-8")) - again, will re-visit this
        msg += ProgressBar.center('{}% of {} {}'.format(cpuUsage, cpuThred, threadString), 'CPU') + '\n'
        msg += ProgressBar.makeBar(int(round(cpuUsage))) + "\n\n"
        msg += ProgressBar.center('{} ({}%) of {}GB used'.format(memUsedGB, memPerc, memTotalGB), 'RAM') + '\n'
        msg += ProgressBar.makeBar(int(round(memPerc))) + "\n\n"
        msg += '{} uptime```'.format(timeString)

        return msg

    # Host Info Slash Command
    @app_commands.command(name="hostinfo", description="List info about the bot's host environment.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def hostinfo(self, interaction: discord.Interaction):
        """List info about the bot's host environment."""

        # await interaction.response.defer(thinking=True)
        await interaction.response.defer(thinking=True)
        msg = await self.bot.loop.run_in_executor(None, self._gather_host_info, interaction)
        await interaction.followup.send(content=msg)

    # Reboot Slash Command
    @app_commands.command(name="reboot", description="Reboots the bot (owner only).")
    @app_commands.describe(install_or_update="(Optional): Specify 'install' or 'update'")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def reboot(self, interaction: discord.Interaction, install_or_update: str | None = None):
        """Reboots the bot (owner only).  Can optionally take install or update as arguments to clear and install dependencies, or update existing as needed."""
        await interaction.response.defer(thinking=True)
        if not await Utils.is_owner_reply(interaction): return

        # Get our return code
        returncode = 2
        suffix = ""
        if install_or_update:
            if "install" in install_or_update.lower():
                returncode = 4
                suffix = " and installing dependencies"
            elif "update" in install_or_update.lower():
                returncode = 5
                suffix = " and updating dependencies"
        # Flush settings asynchronously here
        await self.settings._flush()
        await interaction.followup.send("Flushed settings to disk.")
        await interaction.followup.send("Rebooting{}...".format(suffix))
        # Logout, stop the event loop, close the loop, quit
        try:
            task_list = asyncio.Task.all_tasks()
        except AttributeError:
            task_list = asyncio.all_tasks()

        for task in task_list:
            try:
                task.cancel()
            except:
                continue
        try:
            await self.bot.close()
            self.bot.loop.stop()
            self.bot.loop.close()
        except:
            pass
        # Kill this process
        os._exit(returncode)

    async def _update_status(self):
        # Helper method to update the status based on the server dict
        # Get ready - play game!
        game = self.settings.getGlobalStat("Game", None)
        url = self.settings.getGlobalStat("Stream", None)
        t = self.settings.getGlobalStat("Type", 0)
        status = self.settings.getGlobalStat("Status", None)
        # Set status
        if status == "2":
            s = discord.Status.idle
        elif status == "3":
            s = discord.Status.dnd
        elif status == "4":
            s = discord.Status.invisible
        else:
            # Online when in doubt
            s = discord.Status.online
        dgame = discord.Activity(name=game, url=url, type=t) if game else None
        await self.bot.change_presence(status=s, activity=dgame)


    # Presence Slash Command
    @app_commands.command(name="presence", description="Changes the bot's presence (owner-only).")
    @app_commands.describe(playing_type="Specify a playing type (Playing, Streaming, Listening, Watching)")
    @app_commands.describe(content="(Optional): Define what you are playing (e.g. Rush)")
    @app_commands.describe(url="(Optional): Enter a valid Twitch URL if you selected `Streaming`.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def presence(self, interaction: discord.Interaction, playing_type: str, content: str | None = None, url: str | None = None):
        """Changes the bot's presence (owner-only).

        Playing type options are:

        0. Playing (or None without game)
        1. Streaming (requires valid twitch url)
        2. Listening
        3. Watching

        Status type options are:

        1. Online
        2. Idle
        3. DnD
        4. Invisible

        If any of the passed entries have spaces, they must be in quotes."""
        await interaction.response.defer()
        if not await Utils.is_owner_reply(interaction): return

        # Check playing type
        play = None
        play_string = ""
        if playing_type.lower() in ["0", "play", "playing"]:
            play = 0
            play_string = "Playing"
        elif playing_type.lower() in ["1", "stream", "streaming"]:
            play = 1
            play_string = "Streaming"
            if url == None or not any("twitch.tv" in x.lower() for x in Utils.get_urls(url)):
                # Guess what - you failed!! :D
                return await interaction.followup.send("You need a valid twitch.tv url to set a streaming status!")
        elif playing_type.lower() in ["2", "listen", "listening"]:
            play = 2
            play_string = "Listening"
        elif playing_type.lower() in ["3", "watch", "watching"]:
            play = 3
            play_string = "Watching"
        # Verify we got something
        if play == None:
            # NOooooooooaooOOooOOooope.
            return await interaction.followup.send("Playing type is invalid!")

        # Clear the URL if we're not streaming
        if not play == 1:
            url = None

        # Used to check for status type - hint - thanks to Discord and user installed apps its going to be always online even if the bot is off! YaAAaaaAy!
        stat = "1"
        stat_string = "Online"
        # Sadly removed Status options due to it not applying with any user installs present of an app. Seems to only work with guild only installs. Discord issue....
        # OHMYGODHOWHARDISITTOFOLLOWDIRECTIONS?!?!? - had to keep this comment in. Love it Corp.


        # Here, we assume that everything is A OK.  Peachy keen.
        # Set the shiz and move along
        self.settings.setGlobalStat("Game", content)
        self.settings.setGlobalStat("Stream", url)
        self.settings.setGlobalStat("Status", stat)
        self.settings.setGlobalStat("Type", play)

        # Actually update our shit
        await self._update_status()

        # Let's formulate a sexy little response concoction
        inline = True
        await Message.Embed(
            title="Presence Update",
            color=interaction.user,
            fields=[
                {"name": "Content:", "value": str(content), "inline": inline},
                {"name": "Status:", "value": stat_string, "inline": inline},
                {"name": "Type:", "value": play_string, "inline": inline},
                {"name": "URL:", "value": str(url), "inline": inline}
            ]
        ).send(interaction)


