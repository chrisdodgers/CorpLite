import discord, os
from   datetime import datetime
from discord import app_commands
from   discord.ext import commands
from   Cogs import ReadableTime, Message, FuzzySearch, PickList, Nullify

async def setup(bot):
	# Add the cog
	bot.remove_command("help")
	await bot.add_cog(Help(bot))

# This is the Help module. It replaces the built-in help command

class Help(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot


	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	def _get_help(self, command, max_len = 0):
		# A helper method to return the command help - grabbing app_command descriptions
		help_text = getattr(command, 'description', None) or "Help not available..."
		if max_len == 0:
			# Get the whole thing
			return help_text
		else:
			c_help = help_text.split("\n")[0]
			return (c_help[:max_len-3]+"...") if len(c_help) > max_len else c_help

	async def _get_info(self, ctx, com = None):
		# Helper method to return a list of embed content
		# or None if no results
		prefix = "/"
		# Setup the footer
		footer = "\nType `{}help command` for more info on a command. \n".format(prefix)
		footer += "You can also type `{}help category` for more info on a category.".format(prefix)
		# Get settings - and check them if they exist
		settings = self.bot.get_cog("Settings")
		# disabled_list = settings.getServerStat(ctx.guild, "DisabledCommands", []) if settings and ctx.guild else [] - Currently not in use. Might revisit later.
		if com:
			# We passed a command or cog - let's gather info
			embed_list = {"title":com,"fields":[]}
			the_cog = self.bot.get_cog(com)
			if the_cog:
				# Get the extension
				for e in self.bot.extensions:
					b_ext = self.bot.extensions.get(e)
					if not self._is_submodule(b_ext.__name__, the_cog.__module__): continue
					# It's a submodule
					embed_list = {"title" : "{} Cog - {}.py Extension". format(com, e[5:]), "fields" : [] }
					break
				# Removed aliases, hidden/disabled, and getting bot.tree commands instead of get_commands
				for command in sorted([c for c in self.bot.tree.get_commands() if c.binding is the_cog],
									  key=lambda x: x.name):
					command_help = self._get_help(command, 80)
					name = "{}{} {}".format(prefix, command.name,
											" ".join(f"<{p.name}>" for p in command.parameters)).strip()
					embed_list["fields"].append({"name": name, "value": "`└─ " + command_help + "`", "inline": False})
				# If all commands are hidden - pretend it doesn't exist
				if not len(embed_list["fields"]): return None
				return embed_list
			the_com = next((c for c in self.bot.tree.get_commands() if c.name == com), None)
			if the_com:
				for e in self.bot.extensions:
					b_ext = self.bot.extensions.get(e)
					if the_com.binding and self._is_submodule(b_ext.__name__, the_com.binding.__module__):
						# It's a submodule
						embed_list = {"title": "{} Cog - {}.py Extension".format(type(the_com.binding).__name__, e[5:]),
									  "fields": []}
						break
				name = "**{}{} {}**".format(
					prefix,
					the_com.name,
					" ".join(f"<{p.name}>" for p in the_com.parameters)
				).strip()
				embed_list["com_name"] = name
				embed_list["com_desc"] = self._get_help(the_com)
				embed_list["description"] = "{}\n```\n{}\n```".format(
					embed_list["com_name"],
					embed_list["com_desc"]
				)
				return embed_list
			return None
		# No command or cog - let's send the coglist
		embed_list = { "title" : "Current Categories", "fields" : [] }
		command_list = {}
		for cog in sorted(self.bot.cogs):
			the_cog = self.bot.get_cog(cog)
			# Filter each slash command to its cog
			comms = [c for c in self.bot.tree.get_commands() if c.binding is the_cog]
			# Make sure there are non-hidden commands here - currently commenting this out as CorpLite currently does not have disable/hide functionality for cogs
			# visible = [x for x in comms if not x.hidden]
			# disabled = len([x for x in visible if x.name in disabled_list])
			if not comms: continue
			# Add the name of each cog in the list
			embed_list["fields"].append({
				"name": cog,
				"value": "`└─ {:,} command{}`".format(len(comms), "" if len(comms) == 1 else "s"),
				"inline": True
			})
		return embed_list

	def _dict_add_cog(self, current_dict, cog, prefix, command_named=None, show_hidden=False):
		the_cog = self.bot.get_cog(cog)
		if not the_cog:
			return current_dict # Didn't find it
		# Resolve the extension
		extension = "Unknown"
		for e in self.bot.extensions:
			b_ext = self.bot.extensions.get(e)
			if self._is_submodule(b_ext.__name__, the_cog.__module__):
				# It's a submodule
				extension = "{}.py".format(e[5:])
				break
		commands = sorted([c for c in self.bot.tree.get_commands() if c.binding is the_cog], key=lambda x: x.name)
		# if not show_hidden: Removed as again, no hidden command functionality in CorpLite currently
		if not commands:
			return current_dict
		# Build our info
		current_dict[cog] = {
			"command_count":len(commands),
			"extension":extension,
			"commands":{},
			"formatted":"	{} Cog ({:,} command{}){}:".format(
				cog,
				len(commands),
				"" if len(commands)==1 else "s",
				" - {} Extension".format(extension) if extension else ""
			),
		}
		# Add the markdown variant
		current_dict[cog]["markdown"] = "## {}\n####{}".format(cog,current_dict[cog]["formatted"])
		# Walk the commands
		for comm in sorted(commands,key=lambda x:x.name):
			if command_named and not command_named == comm.name:
				continue # Skip, as it doesn't match what we're looking for
			# Add the info
			sig = " ".join(f"<{p.name}>" for p in comm.parameters)
			current_dict[cog]["commands"][comm.name] = {
				"signature": sig,
				"prefix": prefix,
				"aliases": [],
				"help": self._get_help(comm, 80),
				"formatted": "    {}{}\n     {}└─ {}".format(
					(prefix + comm.name + " " + sig).strip(),
					"",  # No aliases for app_commands
					" " * len(prefix),
					self._get_help(comm, 80)
				)
			}
		return current_dict

	def _dump_help(self, ctx, file_name=None, cog_or_command=None, markdown=False, show_hidden=False):
		if file_name is None:
			file_name = "{}HelpList-{}.txt".format(
				"" if cog_or_command is None else "{}-".format(cog_or_command),
				datetime.today().strftime("%Y-%m-%d %H.%M")
			)
		prefix = "/"
		if cog_or_command:
			cog_dict = self._dict_add_cog({},cog_or_command,prefix,show_hidden=show_hidden)
			if not cog_dict:
				# Wasn't found - let's try to locate the command if possible
				for cog in self.bot.cogs:
					comm = next((c for c in self.bot.tree.get_commands() if cog_or_command == c.name),None)
					if comm:
						cog_dict = self._dict_add_cog({},cog,prefix,command_named=comm.name,show_hidden=show_hidden)
						break
		else:
			# Add them all
			cog_dict = {}
			for cog in sorted(self.bot.cogs):
				cog_dict = self._dict_add_cog(cog_dict,cog,prefix,show_hidden=show_hidden)
		# Walk our list and build the output text if any
		if not cog_dict:
			return None
		output = []
		for cog in cog_dict:
			cog_text = cog_dict[cog]["markdown" if markdown else "formatted"]
			for comm in cog_dict[cog]["commands"]:
				cog_text += "\n"+cog_dict[cog]["commands"][comm]["formatted"]
			output.append(cog_text)
		# Join all the elements with two newlines
		final_output = "\n\n".join(output)
		# Check if we need the markdown index
		if markdown:
			final_output = "{}\n\n{}".format(
				", ".join(["[{}](#{})".format(x,x.lower()) for x in cog_dict]),
				final_output
			)
		return final_output

	# Dump Help Slash Command:
	@app_commands.command(name="dumphelp", description="Dumps and uploads a timestamped, formatted list of commands and descriptions.")
	@app_commands.describe(cog_or_command="Enter a cog or command. (e.g `OpenCore` or `plist`)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def dumphelp(self, interaction: discord.Interaction, cog_or_command: str | None = None):
		"""Dumps and uploads a timestamped, formatted list of commands and descriptions.  Can optionally take a specific Cog or command name to dump help for."""

		await interaction.response.defer()
		file_name = "{}HelpList-{}.txt".format(
			"" if cog_or_command is None else "{}-".format(cog_or_command),
			datetime.today().strftime("%Y-%m-%d %H.%M")
		)
		prefix = "/"
		output = self._dump_help(interaction, file_name, cog_or_command)
		if not output:
			return await interaction.followup.send("I couldn't find that Cog or command.  Cog and command names are case-sensitive.")

		# Got something!
		message = await interaction.followup.send('Saving help list to *{}*...'.format(file_name))
		# Encode to binary
		# Trim the trailing newlines
		output = output.rstrip().encode("utf-8")
		with open(file_name, "wb") as myfile:
			myfile.write(output)
		# Upload the resulting file and clean up
		await message.edit(content='Uploading *{}*...'.format(file_name))
		await interaction.followup.send(file=discord.File(file_name))
		await message.edit(content='Uploaded *{}!*'.format(file_name))
		os.remove(file_name)

	# Dump Help (Markdown) Slash Command: - might consolidate this later with just a single slash command and optionally setting md to true as a slash cmd option
	@app_commands.command(name="dumpmarkdown", description="Dumps and uploads a timestamped, markdown-formatted list of commands and descriptions.")
	@app_commands.describe(cog_or_command="Enter a cog or command. (e.g `OpenCore` or `plist`)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def dumpmarkdown(self, interaction: discord.Interaction, cog_or_command: str | None = None):
		"""Dumps and uploads a timestamped, markdown-formatted list of commands and descriptions.  Can optionally take a specific Cog or command name to dump help for."""

		await interaction.response.defer(thinking=True)
		file_name = "{}HelpMarkdown-{}.md".format(
			"" if cog_or_command is None else "{}-".format(cog_or_command),
			datetime.today().strftime("%Y-%m-%d %H.%M")
		)
		prefix = "/"
		output = self._dump_help(interaction, file_name, cog_or_command, markdown=True)
		if not output:
			return await interaction.followup.send("I couldn't find that Cog or command.  Cog and command names are case-sensitive.")

		# Got something!
		message = await interaction.followup.send('Saving help list to *{}*...'.format(file_name))
		# Encode to binary
		# Trim the trailing newlines
		output = output.rstrip().encode("utf-8")
		with open(file_name, "wb") as myfile:
			myfile.write(output)
		# Upload the resulting file and clean up
		await message.edit(content='Uploading *{}*...'.format(file_name))
		await interaction.followup.send(file=discord.File(file_name))
		await message.edit(content='Uploaded *{}!*'.format(file_name))
		os.remove(file_name)

	# Help Slash Command:
	@app_commands.command(name="help", description="Get Help")
	@app_commands.describe(command="Enter a command or cog. (e.g plist)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def help(self, interaction: discord.Interaction, command: str | None = None):
		"""Lists the bot's commands and cogs.
		You can pass a command or cog to this to get more info (case-sensitive)."""

		await interaction.response.defer(thinking=True)
		prefix = "/"
		result = await self._get_info(interaction, command)

		if result == None:
			# Get a list of all commands and modules and server up the 3 closest
			cog_name_list = []
			com_name_list = []
			# ali_name_list = []
			
			for cog in self.bot.cogs:
				if cog in cog_name_list: continue
				the_cog = self.bot.get_cog(cog)
				cog_commands = [c for c in self.bot.tree.get_commands() if c.binding is the_cog]
				if not cog_commands: continue
				cog_name_list.append(cog)
				for comm in cog_commands:
					if comm.name not in com_name_list:
						com_name_list.append(comm.name)
			
			# Get cog list:
			cog_match = FuzzySearch.search(command, cog_name_list)
			com_match = FuzzySearch.search(command, com_name_list)
			# ali_match = FuzzySearch.search(command, ali_name_list)

			# Build the embed
			m = Message.Embed()
			if type(interaction.user) is discord.Member:
				m.color = interaction.user
			m.title = "Cog or command Not Found"
			m.description = "No exact Cog or command matches for \"{}\".".format(command)
			if len(cog_match):
				cog_mess = "\n".join(["`└─ {}`".format(x["Item"]) for x in cog_match])
				m.add_field(name="Close Cog Matches:", value=cog_mess)
			if len(com_match):
				com_mess = "\n".join(["`└─ {}`".format(x["Item"]) for x in com_match])
				m.add_field(name="Close Command Matches:", value=com_mess)
			'''if len(ali_match):
				ali_mess = "\n".join(["`└─ {}`".format(x["Item"]) for x in ali_match])
				m.add_field(name="Close Command Alias Matches:", value=ali_mess)'''
			m.footer = "Cog and command names are case-sensitive."
			return await m.send(interaction)
		result["color"] = interaction.user
		bot_user = interaction.guild.get_member(self.bot.user.id) if interaction.guild else self.bot.user
		desc = "Get more info with \"{}help Cog\" or \"{}help command\".\nCog and command names are case-sensitive.\n\n{}: {}".format(
			prefix,
			prefix,
			bot_user.display_name,
			self.bot.description
		)
		return await PickList.PagePicker(
			title=result["title"],
			list=result["fields"],
			ctx=interaction,
			description=result.get("com_desc",desc),
			max=12 if result["fields"] else 100, # 12 fields or 100 lines of desc text
			d_header=result.get("com_name","")+"```\n",
			d_footer="```",
			footer=result.get("footer","" if len(result["fields"]) else desc.replace("```\n","").split("\n")[0])
		).pick()
