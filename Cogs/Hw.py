import discord
from   discord import app_commands
from   discord.ext import commands
from   Cogs import Utils, PickList, Nullify

async def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	await bot.add_cog(Hw(bot, settings))

# This is the Uptime module. It keeps track of how long the bot's been up
# ^ Kept from CorpBot's Hw.py - it was wrong there too. Love it Corp.

# CorpLite notes:  The old prompt()/confirm() pm conversation from CorpBot's Hw.py
# relied on bot.wait_for("message") - which needs the message content intent in
# guilds.  With 0 privileged intents we gather the build name and parts through
# a modal (form) instead - which works the same in guilds, dms, and group dms.
# That also means hwactive sessions, cancelhw, sethwchannel/hwchannel, and the
# whole prompt/confirm machinery are no longer needed.
# Hardware is stored in GlobalMembers keyed only by user id - so a Settings.json
# imported from a CorpBot instance carries builds over untouched.

class Hw(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils
		Utils = self.bot.get_cog("Utils")

	def _name(self, user):
		# A helper function to return the user's display name - DisplayName.py
		# didn't make the trip to CorpLite, so we just keep the part we need
		return Nullify.escape_all(getattr(user,"display_name",user.name))

	def _is_private(self, interaction):
		# Manage commands reply ephemerally when run inside a guild - views stay public
		return interaction.guild_id is not None

	def _get_builds(self, user):
		# Returns the sorted build list for the passed user
		buildList = self.settings.getGlobalUserStat(user, "Hardware")
		if buildList is None:
			buildList = []
		return sorted(buildList, key=lambda x:x['Name'].lower())

	def _get_build(self, buildList, build = None):
		# Get build by name first - then by number
		if build is not None:
			for b in buildList:
				if b['Name'].lower() == build.lower():
					# Found it
					return b
			try:
				build = int(build)-1
				if build >= 0 and build < len(buildList):
					return buildList[build]
			except:
				pass
			return None
		# No build passed - get the main if it exists
		for b in buildList:
			if b['Main']:
				return b
		return None

	async def _save_build(self, interaction, mainBuild, name, parts):
		# Called when an HwModal is submitted - saves a new build, or edits to an
		# existing one, then reports back
		buildList = self._get_builds(interaction.user)
		# Make sure the name isn't already taken by a *different* build - we skip
		# the one we're editing so resubmitting the same name (i.e. only changing
		# parts) doesn't trip the check
		for build in buildList:
			if build is mainBuild:
				continue
			if build['Name'].lower() == name.lower():
				mesg = 'It looks like you already have a build by that name, *{}*.  Try again.'.format(self._name(interaction.user))
				return await interaction.response.send_message(mesg, ephemeral=self._is_private(interaction))
		bname = Nullify.escape_all(name)
		if mainBuild is None:
			# Check if we already have a main build and clear it
			for build in buildList:
				build['Main'] = False
			buildList.append({ 'Name': name, 'Hardware': parts, 'Main': True })
			msg = "*{0}*, {1} was created successfully!  It has been set as your **main build**.  To view your main build, you can use `/hw` - or to change which is your main, use `/edithw` with the `set_main` option.".format(
				self._name(interaction.user),
				bname
			)
		else:
			mainBuild['Name'] = name
			mainBuild['Hardware'] = parts
			msg = '*{}*, {} was edited successfully!'.format(self._name(interaction.user), bname)
		self.settings.setGlobalUserStat(interaction.user, "Hardware", buildList)
		await interaction.response.send_message(msg, ephemeral=self._is_private(interaction))

	# New Hardware Slash Command
	@app_commands.command(name="newhw", description="Add a new hardware build.  The build added will also be set as your Main Build.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def newhw(self, interaction: discord.Interaction):
		"""Initiate a new-hardware form.  The hardware added will also be set as the Main Build."""
		await interaction.response.send_modal(HwModal(self))

	# Edit Hardware Slash Command
	@app_commands.command(name="edithw", description="Edits a build from your build list - can also rename or set your Main Build.")
	@app_commands.describe(build="The build name or number to edit - defaults to your main build.")
	@app_commands.describe(set_main="Set the passed build as your Main Build instead of opening the editor.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def edithw(self, interaction: discord.Interaction, build: str | None = None, set_main: bool | None = None):
		"""Edits a build from your build list.  Renaming is done by changing the name in the editor - and set_main takes over mainhw's old job."""
		buildList = self._get_builds(interaction.user)
		if not len(buildList):
			# No parts!
			msg = 'You have no builds on file!  You can add some with the `/newhw` command.'
			return await interaction.response.send_message(msg, ephemeral=self._is_private(interaction))
		mainBuild = self._get_build(buildList, build)
		if not mainBuild:
			msg = "I couldn't find that build or number."
			return await interaction.response.send_message(msg, ephemeral=self._is_private(interaction))
		if set_main:
			# Just changing which build is the main - no editor needed
			for b in buildList:
				if b is mainBuild:
					b['Main'] = True
				else:
					b['Main'] = False
			self.settings.setGlobalUserStat(interaction.user, "Hardware", buildList)
			msg = "{} set as main!".format(Nullify.escape_all(mainBuild['Name']))
			return await interaction.response.send_message(msg, ephemeral=self._is_private(interaction))
		# Here, we have a build - pre-fill the editor with it
		await interaction.response.send_modal(HwModal(self, mainBuild))

	# Delete Hardware Slash Command
	@app_commands.command(name="delhw", description="Removes a build from your build list.")
	@app_commands.describe(build="The build name or number to remove.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def delhw(self, interaction: discord.Interaction, build: str):
		"""Removes a build from your build list."""
		buildList = self._get_builds(interaction.user)
		if not len(buildList):
			# No parts!
			msg = 'You have no builds on file!  You can add some with the `/newhw` command.'
			return await interaction.response.send_message(msg, ephemeral=self._is_private(interaction))
		b = self._get_build(buildList, build)
		if not b:
			msg = "I couldn't find that build or number."
			return await interaction.response.send_message(msg, ephemeral=self._is_private(interaction))
		buildList.remove(b)
		if b['Main'] and len(buildList):
			buildList[0]['Main'] = True
		self.settings.setGlobalUserStat(interaction.user, "Hardware", buildList)
		msg = "{} removed!".format(Nullify.escape_all(b['Name']))
		await interaction.response.send_message(msg, ephemeral=self._is_private(interaction))

	# Hardware Slash Command
	@app_commands.command(name="hw", description="Lists the hardware for either the user's main build - or the passed build.")
	@app_commands.describe(user="The user whose hardware to show - defaults to yourself.")
	@app_commands.describe(build="The build name or number to show - defaults to the user's main build.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def hw(self, interaction: discord.Interaction, user: discord.User | None = None, build: str | None = None):
		"""Lists the hardware for either the user's default build - or the passed build."""
		# Discord resolves the user option natively - so the reverse name/build
		# parsing loops from CorpBot's Hw.py aren't needed anymore
		member = user or interaction.user
		buildList = self._get_builds(member)
		if not len(buildList):
			# No parts!
			msg = '*{}* has no builds on file!  They can add some with the `/newhw` command.'.format(self._name(member))
			return await interaction.response.send_message(msg)
		buildParts = self._get_build(buildList, build)
		if not buildParts:
			# Well... uh... no defaults
			msg = "I couldn't find that user/build combo..."
			return await interaction.response.send_message(msg)
		# At this point - we *should* have a user and a build
		name = self._name(member)
		msg_head = "__**{}'{} {}:**__\n\n".format(name,"" if name[-1:].lower()=="s" else "s", buildParts['Name'])
		msg = msg_head + buildParts['Hardware']
		if len(msg) > 2000: # is there somwhere the discord char count is defined, to avoid hardcoding?
			msg = buildParts['Hardware'] # if the header pushes us over the limit, omit it and send just the string
		await interaction.response.send_message(Nullify.escape_all(msg,markdown=False,links=False))

	# List Hardware Slash Command
	@app_commands.command(name="listhw", description="Lists the builds for the specified user - or yourself if no user passed.")
	@app_commands.describe(user="The user whose builds to list - defaults to yourself.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def listhw(self, interaction: discord.Interaction, user: discord.User | None = None):
		"""Lists the builds for the specified user - or yourself if no user passed."""
		member = user or interaction.user
		buildList = self._get_builds(member)
		if not len(buildList):
			msg = '*{}* has no builds on file!  They can add some with the `/newhw` command.'.format(self._name(member))
			return await interaction.response.send_message(msg)
		await interaction.response.defer(thinking=True)
		items = [{"name":"{}. {}".format(i,x["Name"]+(" (Main Build)" if x["Main"] else "")),"value":Utils.truncate_string(x["Hardware"])} for i,x in enumerate(buildList,start=1)]
		return await PickList.PagePicker(title="{}'s Builds ({:,} total)".format(self._name(member),len(buildList)),list=items,ctx=interaction).pick()

	# List Hardware (Titles Only) Slash Command
	@app_commands.command(name="lhw", description="Lists only the titles of the builds for the specified user - or yourself if no user passed.")
	@app_commands.describe(user="The user whose build titles to list - defaults to yourself.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def lhw(self, interaction: discord.Interaction, user: discord.User | None = None):
		"""Lists only the titles of the builds for the specified user - or yourself if no user passed."""
		member = user or interaction.user
		buildList = self._get_builds(member)
		if not len(buildList):
			msg = '*{}* has no builds on file!  They can add some with the `/newhw` command.'.format(self._name(member))
			return await interaction.response.send_message(msg)
		await interaction.response.defer(thinking=True)
		desc = "\n".join([Utils.truncate_string("{}. {}".format(i,x["Name"]+(" (Main Build)" if x["Main"] else ""))) for i,x in enumerate(buildList,start=1)])
		return await PickList.PagePicker(
			title="{}'s Builds ({:,} total)".format(self._name(member),len(buildList)),
			description=desc,
			ctx=interaction
		).pick()


# The form used by /newhw and /edithw - replaces the old pm conversation
class HwModal(discord.ui.Modal):
	def __init__(self, outer, mainBuild = None):
		# Modal titles cap out at 45 chars - truncate as needed
		super().__init__(title='Edit "{}"'.format(mainBuild['Name'])[:45] if mainBuild else "New Build")
		self.outer = outer
		self.mainBuild = mainBuild
		self.build_name = discord.ui.TextInput(
			label="Build Name",
			default=mainBuild['Name'] if mainBuild else None,
			max_length=100 # Keep it sane - it has to fit in an embed field name with room to spare
		)
		self.build_parts = discord.ui.TextInput(
			label="Parts",
			style=discord.TextStyle.paragraph,
			default=mainBuild['Hardware'] if mainBuild else None,
			max_length=2000 # Matches Discord's message limit - same cap the old pm approach had by nature
		)
		self.add_item(self.build_name)
		self.add_item(self.build_parts)

	async def on_submit(self, interaction: discord.Interaction):
		await self.outer._save_build(interaction, self.mainBuild, self.build_name.value, self.build_parts.value)
