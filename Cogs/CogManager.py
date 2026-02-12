import discord, os, dis, subprocess
from discord import app_commands
from discord.ext import commands
from Cogs import Message, PickList

async def setup(bot):
	# Add the bot
	# Removed settings since it isn't being used with CorpLite at the current moment.
	await bot.add_cog(CogManager(bot))


class CogManager(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.preloads = ("Ignore This Until A Future Update",) # Temp removed DisplayName, Settings, and Mute since it is not currently being used for CorpLite. Crappy place holder yes, but retaining this logic until I revisit in a future update.
		self.bot = bot


	@commands.Cog.listener()
	async def on_ready(self):
		# Load cogs when bot is ready
		return

	def _get_imports(self, file_name):
		file_path = os.path.join("Cogs",file_name)
		if not os.path.exists(file_path):
			return []
		with open(file_path,"rb") as f:
			file_string = f.read().decode()
		instructions = dis.get_instructions(file_string)
		cog_imports = []
		for inst in instructions:
			if not inst.opname == "IMPORT_FROM":
				continue
			if not os.path.exists(os.path.join("Cogs","{}.py".format(inst.argval))):
				continue
			cog_imports.append(inst.argval)
		return cog_imports

	def _get_imported_by(self, file_name):
		ext_list = []
		for ext in os.listdir("Cogs"):
			# Avoid reloading Settings and Mute
			if not ext.lower().endswith(".py") or ext == file_name:
				continue
			if file_name[:-3] in self._get_imports(ext):
				ext_list.append(ext)
		return ext_list

	async def _load_extension(self, extension = None): # Updated to be async. See notes in Main.py calling this. Added await for each mention of self calling unload_extension/load_extension
		# Loads extensions - if no extension passed, loads all
		# starts with Settings - removed Mute since CorpLite does not need this at the current time.
		if extension is None:
			# Load them all!
			for x in self.preloads:
				if x in self.bot.extensions:
					self.bot.dispatch("unloaded_extension", self.bot.extensions.get(x))
					try: await self.bot.unload_extension(x)
					except: print("{} failed to unload!".format(x))
				try:
					await self.bot.load_extension(x)
					self.bot.dispatch("loaded_extension", self.bot.extensions.get(x))
				except: print("{} failed to load!".format(x))
			cog_count = len(self.preloads) # Assumes the prior 2 loaded correctly
			cog_loaded = len(self.preloads) # Again, assumes success above
			# Load the rest of the cogs
			for ext in os.listdir("Cogs"):
				# Avoid reloading Settings and Mute
				if ext.lower().endswith(".py") and not (ext.lower() in ["settings.py"]):
					# Valid cog - load it
					cog_count += 1
					# Try unloading
					try:
						# Only unload if loaded
						if "Cogs."+ext[:-3] in self.bot.extensions:
							self.bot.dispatch("unloaded_extension", self.bot.extensions.get("Cogs."+ext[:-3]))
							await self.bot.unload_extension("Cogs."+ext[:-3])
					except Exception as e:
						print("{} failed to unload!".format(ext[:-3]))
						print("    {}".format(e))
						pass
					# Try to load
					try:
						await self.bot.load_extension("Cogs." + ext[:-3])
						self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs."+ext[:-3]))
						cog_loaded += 1
					except Exception as e:
						print("{} failed to load!".format(ext[:-3]))
						print("    {}".format(e))
						pass
			return ( cog_loaded, cog_count )
		else:
			for ext in os.listdir("Cogs"):
				if ext[:-3].lower() == extension.lower():
					# First - let's get a list of extensions
					# that imported this one
					to_reload = self._get_imported_by(ext)
					# Add our extension first
					to_reload.insert(0, ext)
					total = len(to_reload)
					success = 0
					# Iterate and reload
					for e in to_reload:
						# Try unloading
						try:
							# Only unload if loaded
							if "Cogs."+e[:-3] in self.bot.extensions:
								self.bot.dispatch("unloaded_extension", self.bot.extensions.get("Cogs."+e[:-3]))
								await self.bot.unload_extension("Cogs."+e[:-3])
						except Exception as er:
							print("{} failed to unload!".format(e[:-3]))
							print("    {}".format(er))
							pass
						# Try to load
						try:
							await self.bot.load_extension("Cogs."+e[:-3])
							self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs."+e[:-3]))
							success += 1
						except Exception as er:
							print("{} failed to load!".format(e[:-3]))
							print("    {}".format(er))
					return ( success, total )
			# Not found
			return ( 0, 0 )

	def _unload_extension(self, extension = None):
		if extension is None:
			# NEED an extension to unload
			return ( 0, 1 )
		for cog in self.bot.cogs:
			if cog.lower() == extension.lower():
				try:
					self.bot.unload_extension("Cogs."+cog)
				except:
					return ( 0, 1 )
		return ( 0, 0 )
		
	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	# Called by /extensions and /import - this function is no longer nested in the extensions command and is instead now check_extension called by it and import.
	async def check_extension(self, interaction: discord.Interaction, extension: str | None = None):
		"""Outputs the cogs and command count for the passed extension - or all extensions and their corresponding cogs if none passed."""

		# Build our extensions dictionary
		ext_dict = {}
		for e in self.bot.extensions:
			ext_name = str(e)[5:]
			cog_list = ext_dict.get(ext_name, [])
			b_ext = self.bot.extensions.get(e)
			hidden = False
			for cog in self.bot.cogs:
				# Get the cog
				b_cog = self.bot.get_cog(cog)
				if not self._is_submodule(b_ext.__name__, b_cog.__module__):
					continue
				commands = b_cog.get_commands()
				if commands and all((x.hidden for x in commands)):
					hidden = True
					continue  # All commands are hidden
				# Submodule - add it to the list
				cog_list.append(str(cog))
			if hidden: continue  # Don't save hidden cogs
			# Retain any cogs located for the extension here
			if cog_list:
				ext_dict[ext_name] = cog_list
			else:
				cogless = ext_dict.get("Cogless", [])
				cogless.append(ext_name)
				ext_dict["Cogless"] = cogless
		# Check if we got anything
		if not ext_dict:
			return await Message.Embed(
				title="No Extensions Found",
				color=interaction.user
			).send(interaction)
		# Check if we're searching - and retrieve the extension if so
		fields = []
		if extension:
			# Map the key to the first match - case-insensitive
			ext_name = next((x for x in ext_dict if x.lower() == extension.lower()), None)
			if not ext_name:
				return await Message.Embed(
					title="Extension Not Found",
					description="Could not find an extension by that name.",
					color=interaction.user
				).send(interaction)
			if ext_name == "Cogless":
				title = "Extensions Without Cogs ({:,} Total)".format(len(ext_dict[ext_name]))
				fields.append({
					"name": "Cogless - Each Has 0 Commands",
					"value": "\n".join(["`└─ {}`".format(x) for x in ext_dict[ext_name]]),
					"inline": True
				})
			else:
				title = "{} Extension ({:,} Total Cog{})".format(ext_name, len(ext_dict[ext_name]),
																 "" if len(ext_dict[ext_name]) == 1 else "s")
				# Got the target extension - gather its info
				for cog in ext_dict[ext_name]:
					try:
						comms = len([x for x in self.bot.get_cog(cog).get_commands() if not x.hidden])
					except:
						comms = 0  # Zero it out if it's not a cog, or has none
					fields.append({
						"name": cog,
						"value": "`└─ {:,} command{}`".format(comms, "" if comms == 1 else "s"),
						"inline": True
					})
		else:
			# We're listing them all
			title = "All Extensions ({:,} Total)".format(len(ext_dict))
			ext_list = [x for x in sorted(list(ext_dict), key=lambda x: x.lower()) if not x == "Cogless"]
			if "Cogless" in ext_dict: ext_list.append("Cogless")  # Make sure this comes last
			for ext_name in ext_list:
				fields.append({
					"name": ext_name,
					"value": "\n".join(["`└─ {}`".format(x) for x in ext_dict[ext_name]]),
					"inline": True
				})
		return await PickList.PagePicker(
			title=title,
			list=fields,
			ctx=interaction,
			max=24
		).pick()

	# Imports Slash Command
	@app_commands.command(name="imports", description="Outputs the extensions imported by the passed extension.")
	@app_commands.describe(extension="fill this in later")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def imports(self, interaction: discord.Interaction, extension: str | None = None):
		"""Outputs the extensions imported by the passed extension."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		if extension is None:
			# run check_extension
			return await self.check_extension(interaction, extension)
		for ext in os.listdir("Cogs"):
			# Avoid reloading Settings and Mute
			if not ext.lower().endswith(".py"):
				continue
			if ext[:-3].lower() == extension.lower():
				# Found it
				import_list = self._get_imports(ext)
				if not len(import_list):
					await interaction.followup.send("That extension has no local extensions imported.")
				else:
					await interaction.followup.send("Imports:\n\n{}".format(", ".join(import_list)))
				return
		await interaction.followup.send("I couldn't find that extension...")

	# Extensions Slash Command
	@app_commands.command(name="extensions", description="Outputs the cogs and command count")
	@app_commands.describe(extension="fill this in later")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def extensions(self, interaction: discord.Interaction, extension: str | None = None):
		"""Outputs the cogs and command count for the passed extension - or all extensions and their corresponding cogs if none passed."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		# Run check_extension - (function that was previously part of this command but now not. Notes on why this is I made in OpenCore for ALC. Same reasoning behind this.)
		return await self.check_extension(interaction, extension)

	

