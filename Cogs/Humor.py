import io
import discord, random, time, os, PIL, textwrap, datetime, asyncio
from discord import app_commands
from discord.ext import commands
from urllib.parse import quote
from html import unescape
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from Cogs import Message, FuzzySearch, GetImage, Utils, DL, PickList, Nullify

async def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	await bot.add_cog(Humor(bot, settings))

# This module is for random funny things I guess...

class Humor(commands.Cog):

	def __init__(self, bot, settings, listName = "Adjectives.txt"):
		self.bot = bot
		global Utils
		Utils = self.bot.get_cog("Utils")
		self.settings = settings
		self.is_current = False
		self.wait_time = 86400 # Default of 24 hours (86400 seconds)
		self.meme_temps = []
		# Setup our adjective list
		self.adj = []
		marks = map(chr, range(768, 879))
		self.marks = list(marks)
		if os.path.exists(listName):
			with open(listName) as f:
				for line in f:
					self.adj.append(line)
		try: self.image = Image.open('images/dosomething.png')
		except: self.image = Image.new("RGBA",(500,500),(0,0,0,0))
		try: self.slap_image = Image.open("images/slap.png")
		except: self.slap_image = Image.new("RGBA",(800,600),(0,0,0,0))
		self.slap_words = ("walloped","slapped","demolished","obliterated","bonked","smacked")
		# Removed Stardew. Might re-visit if requested.

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
		self.is_current = True
		# Start the update loop
		self.bot.loop.create_task(self.update_memetemps())

	async def update_memetemps(self):
		print("Starting imgflip.com meme template update loop - repeats every {:,} second{}...".format(self.wait_time,"" if self.wait_time==1 else "s"))
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			if not self.is_current:
				# Bail if we're not the current instance
				return
			await self._update_memetemps()
			await asyncio.sleep(self.wait_time)

	async def _update_memetemps(self):
		# Helper to actually do the updating
		print("Updating meme templates from imageflip.com: {}".format(datetime.datetime.now().time().isoformat()))
		try:
			result_json = await DL.async_json("https://api.imgflip.com/get_memes")
			meme_temps = result_json["data"]["memes"]
			if meme_temps: self.meme_temps = meme_temps
		except Exception as e:
			print("Meme template update failed: {}".format(e))
		return self.meme_temps

	# Zalgo Slash Command
	@app_commands.command(name="zalgo", description="Send a funny looking message.")
	@app_commands.describe(message="Type a message.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def zalgo(self, interaction: discord.Interaction, message: str):
		"""Ỉ s̰hͨo̹u̳lͪd͆ r͈͍e͓̬a͓͜lͨ̈l̘̇y̡͟ h͚͆a̵͢v͐͑eͦ̓ i͋̍̕n̵̰ͤs͖̟̟t͔ͤ̉ǎ͓͐ḻ̪ͨl̦͒̂ḙ͕͉d͏̖̏ ṡ̢ͬö̹͗m̬͔̌e̵̤͕ a̸̫͓͗n̹ͥ̓͋t̴͍͊̍i̝̿̾̕v̪̈̈͜i̷̞̋̄r̦̅́͡u͓̎̀̿s̖̜̉͌..."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		words = message.split()
		try:
			iterations = int(words[len(words)-1])
			words = words[:-1]
		except Exception:
			iterations = 1

		iterations = 100 if iterations > 100 else 1 if iterations < 1 else iterations
			
		zalgo = " ".join(words)
		for i in range(iterations):
			if len(zalgo) > 2000:
				break
			zalgo = self._zalgo(zalgo)
		
		zalgo = zalgo[:2000]

		# zalgo = Utils.suppressed(ctx,zalgo)
		await Message.Message(message=zalgo).send(interaction)
		
	def _zalgo(self, text):
		words = text.split()
		zalgo = ' '.join(''.join(c + ''.join(random.choice(self.marks)
				for _ in range(i // 2 + 1)) * c.isalnum()
				for c in word)
				for i, word in enumerate(words))
		return zalgo

	# Removed Holy. Might re-vist this if requested?

	# Fart - lol
	@app_commands.command(name="fart", description="Let some air out! Maybe on someone.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def fart(self, ctx):
		"""PrincessZoey :P"""
		fartList = ["Poot", "Prrrrt", "Thhbbthbbbthhh", "Plllleerrrrffff", "Toot", "Blaaaaahnk", "Squerk"]
		await ctx.response.send_message(content=random.choice(fartList))

	# Speak Theo Slash Command
	@app_commands.command(name="french", description="Excuse my French.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def french(self, ctx):
		"""Speaking French... probably..."""
		fr_list = [ "hon", "fromage", "baguette" ]
		punct   = [ ".", "!", "?", "...", "!!!", "?!" ]
		fr_sentence = [random.choice(fr_list) for i in range(random.randint(3,20))]
		# Capitalize the first letter of the first word
		fr_sentence[0] = fr_sentence[0].capitalize()
		totally_french = " ".join(fr_sentence) + random.choice(punct)
		await ctx.response.send_message(content=totally_french)

	# Speak Bobr Slash Command
	@app_commands.command(name="german", description="I think this is German.")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def german(self, ctx):
		"""Speaking German... probably..."""
		de_list = [ "BIER", "sauerkraut", "auto", "weißwurst", "KRANKENWAGEN" ]
		punct   = [ ".", "!", "?", "...", "!!!", "?!" ]
		de_sentence = [random.choice(de_list) for i in range(random.randint(3,20))]
		if random.randint(0,1):
			# Toss "rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz" in there somewhere
			de_sentence[random.randint(0,len(de_sentence)-1)] = "rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz"
		# Capitalize the first letter of the first word
		de_sentence[0] = de_sentence[0].capitalize()
		totally_german = " ".join(de_sentence) + random.choice(punct)
		await ctx.response.send_message(content=totally_german)

	# Removed canDisplay

	# Meme Templates Slash Command
	@app_commands.command(name="memetemps", description="Grab a meme template.")
	@app_commands.describe(search_term="Search for a meme template (e.g. trade offer).")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def memetemps(self, interaction: discord.Interaction, *, search_term: str):
		"""Get Meme Templates"""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		message = None
		if search_term is None:
			# Try to update meme_temps if possible
			if not self.meme_temps:
				await self._update_memetemps()
			if not self.meme_temps:
				return await Message.Embed(
					title="No Meme Templates Found",
					description="It looks like I couldn't get the meme templates from imgur.com :(",
					color=interaction.user
				).edit(interaction,message)
			# Format all the meme_temps
			fields = []
			for template in self.meme_temps:
				fields.append({
					"name" : template["name"],
					"value" : "`{}` [Link]({})".format(
						template["id"],
						"https://imgflip.com/memegenerator/{}".format(template["id"])
					)
				})
			# Send the results to the user
			await PickList.PagePicker(
				title="Meme Templates",
				color=interaction.user,
				list=fields,
				ctx=interaction,
				message=message,
				footer="Powered by imgflip.com"
			).pick()
		else:
			# Try to find the meme template passed
			template = await self._get_meme_from_search(search_term,ensure_blank=True)
			embed = {
				"title":"Meme Results For \"{}\"".format(search_term),
				"color":interaction.user,
				"description":"Nothing found :(",
				"footer":"Powered by imgflip.com"
			}
			if template:
				# Update the info
				embed["description"] = None
				embed["url"] = "https://imgflip.com/memegenerator/{}".format(template["id"])
				fields = []
				for x,y in (("name","Name"),("id","ID"),("format","Format"),("dimensions","Dimensions"),("filesize","File Size")):
					if template.get(x):
						fields.append({
							"name":y,
							"value":template[x]
						})
				if fields:
					embed["fields"] = fields
				embed["image"] = template["blank_url"]
			await Message.Embed(**embed).edit(interaction,message)

	async def _get_meme_from_search(self,search_term,ensure_blank=False):
		if not self.meme_temps:
			await self._update_memetemps()
		# Check if search_term is in our meme_temps list
		search_term = str(search_term)
		chosenTemp = next((x for x in self.meme_temps if search_term.lower() in (x["id"],x["name"].lower())),None)
		if not chosenTemp:
			# We didn't find it - check if it's an int first - maybe it's a template id
			meme_url = None
			try:
				meme_url = "https://imgflip.com/memetemplate/{}".format(int(search_term))
			except:
				try:
					# It's not an int - try to search for it
					search_html = await DL.async_text("https://imgflip.com/memesearch?q={}".format(quote(search_term)))
					# Get the first non-animated match - ensure next() throws an exception if none are found to escape the try/except
					meme_url = "https://imgflip.com/memetemplate/{}".format(
						next(x.strip().split("\n")[0].split('href="/meme/')[1].split('"')[0] for x in search_html.split('<h3 class="mt-title">')[1:] if not "mt-animated-label" in x)
					)
				except:
					pass
			if meme_url:
				try:
					# Load the template HTML and scrape the info
					chosenTemp = await self._get_meme_info_from_url(meme_url)
				except:
					pass
		if not chosenTemp:
			# Fuzzy match by name
			chosenTemp = FuzzySearch.search(search_term,self.meme_temps,"name",1)[0]["Item"]
		if chosenTemp and ensure_blank and not "blank_url" in chosenTemp:
			# If we need to get the blank meme URL but didn't already - resolve it
			chosenTemp = await self._get_meme_info_from_url("https://imgflip.com/memetemplate/{}".format(chosenTemp["id"]))
		return chosenTemp

	async def _get_meme(self,chosenTemp,box_text):
		url = "https://api.imgflip.com/caption_image"
		payload = {'template_id': chosenTemp["id"], 'username':'CorpBot', 'password': 'pooter123'}
		# Add the text to the payload
		for i,x in enumerate(box_text[:chosenTemp.get("box_count",len(box_text))]):
			payload["boxes[{}][text]".format(i)] = x.upper()
		result_json = await DL.async_post_json(url, payload)
		return result_json["data"]["url"]

	async def _get_meme_info_from_url(self,url):
		html = await DL.async_text(url)
		meme_id   = html.split("<p>Template ID: ")[1].split("<")[0]
		meme_name = html.split('<h1 id="mtm-title">')[1].split("<")[0]
		meme_name = unescape(meme_name)
		for x in (" Template"," Meme"):
			if meme_name.endswith(x):
				meme_name = meme_name[:-len(x)]
		url_end = html.split("mtm-img")[1].split('src="')[1].split('"')[0]
		blank_url = "https:{}{}".format(
			"" if url_end.startswith("//") else "//imgflip.com/",
			url_end
		)
		meme_frmt = html.split("<p>Format: ")[1].split("<")[0]
		meme_dims = html.split("<p>Dimensions: ")[1].split("<")[0]
		meme_size = html.split("<p>Filesize: ")[1].split("<")[0]
		return {
			"id":meme_id,
			"name":meme_name,
			"format":meme_frmt,
			"dimensions":meme_dims,
			"filesize":meme_size,
			"blank_url":blank_url
		}

	# Meme Slash Command
	@app_commands.command(name="meme", description="Time for some memes.")
	@app_commands.describe(template_id="Enter a template_id: (Hint: use /memetemp to find this).")
	@app_commands.describe(text_1="Enter what you want you want the first text to be in your meme:")
	@app_commands.describe(text_2="(Optional) Enter what you want you want the first text to be in your meme:")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def meme(self, interaction: discord.Interaction, template_id: str, text_1: str, text_2: str | None = None):
		"""Generate Memes!  You can get a list of meme templates with the memetemps command.  If any fields have spaces, they must be enclosed in quotes."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		# if not self.canDisplay(ctx.message.guild): return
		box_text = [text_1]
		if text_2 is not None and text_2.strip():
			box_text.append(text_2)
		if template_id is None and text_2.strip():
			msg = "Usage: `/meme [template_id] [text_1] [text_2]`\n\n Meme Templates can be found using `/memetemp`"
			return await interaction.followup.send(msg)

		message = None # await Message.Embed(title="Calibrating humor...",color=ctx.author).send(ctx) once again - see notes similar I made in iARK
		chosenTemp = await self._get_meme_from_search(template_id)

		# Actually get the meme
		try:
			assert chosenTemp is not None
			result = await self._get_meme(chosenTemp,box_text)
		except:
			return await Message.Embed(
				title="Something went wrong :(",
				description="Your meme was too powerful - I couldn't get anything from imgflip"
			).edit(interaction,message)
		# Send the resulting meme
		await Message.Embed(
			url=result,
			title=" - ".join([x for x in box_text[:chosenTemp.get("box_count",len(box_text))] if x != " "]),
			image=result,
			footer='Powered by imgflip.com - using template id {}{}'.format(chosenTemp["id"],": "+chosenTemp["name"] if chosenTemp["name"]!=chosenTemp["id"] else "")
		).edit(interaction,message)

	# Poke Slash Command
	@app_commands.command(name="poke", description="C'mon, do something...")
	@app_commands.describe(user="(Optional): Mention a user (e.g. @chris_dodgers)")
	@app_commands.describe(image="(Optional): Upload an image (e.g. something.png)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def poke(self, interaction: discord.Interaction, user: discord.User | None = None, image: discord.Attachment | None = None):
		"""Pokes the passed url/user/uploaded image."""
		Utils = self.bot.get_cog("Utils")  # Not sure at all why I am having to load this here when in CorpBot I dont have to do this. Also revisit....
		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		path = None
		if user is None and image is None:
			return await interaction.followup.send("Usage: `/poke` `[user]`, or `[image]`")
		if user is None:
			path = await image.read()
		# Let's check if a user was defined and if so set the URL and path as such.
		test_user = user
		if test_user:
			# Got a user!
			url = Utils.get_avatar(test_user)
			path = await GetImage.download(url)
		image = self.image.copy()

		if not path:
			return await interaction.followup.send(content="I guess I couldn't poke that...  Make sure you're passing a valid url, user, or attachment.")
		# We should have the image - let's open it and convert to a single frame
		try:
			if test_user:
				img = Image.open(path)
			else:
				img = Image.open(io.BytesIO(path))
			img = img.convert('RGBA')
			# Let's ensure it's the right size, and place it in the right spot
			t_max   = int(image.width*.38)
			t_ratio = min(t_max/img.width,t_max/img.height)
			t_w = int(img.width*t_ratio)
			t_h = int(img.height*t_ratio)
			img = img.resize((t_w,t_h),resample=PIL.Image.LANCZOS)
			# Paste our other image on top
			image.paste(img,(int(image.width*.6),int(image.height*.98)-t_h),mask=img)
			image.save('images/dosomethingnow.png')
			await interaction.followup.send(file=discord.File(fp='images/dosomethingnow.png'))
			os.remove('images/dosomethingnow.png')
		except Exception as e:
			print(e)
			pass
		if os.path.exists(path):
			GetImage.remove(path)

	# Fry Slash Command
	@app_commands.command(name="fry", description="Fry an image to a crisp.")
	@app_commands.describe(image="Upload an image (e.g. bigmeme.png)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def fry(self, interaction: discord.Interaction, image: discord.Attachment):
		"""Fry up some memes."""
		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		# Removed URL handling - see other areas why this is.
		message = None

		image_upload = await image.read() #Renamed from Path. Reading the direct uploaded attachment instead of trying to use GetImage.
		if not image_upload:
			return await message.edit(content="I guess I couldn't fry that...  Make sure you're uploading a valid attachment.")
		# We should have the image - let's open it and convert to a single frame
		try:
			# Credit for the frying goes to Flame442
			img = Image.open(io.BytesIO(image_upload)).convert("RGBA") #Using io.BytesIO now as we are directly handling an uploaded attachment. Fixes the `embedded null byte` error.
			e = ImageEnhance.Sharpness(img)
			img = e.enhance(100)
			e = ImageEnhance.Contrast(img)
			img = e.enhance(100)
			e = ImageEnhance.Brightness(img)
			img = e.enhance(.27)
			r, b, g, a = img.split()
			e = ImageEnhance.Brightness(r)
			r = e.enhance(4)
			e = ImageEnhance.Brightness(g)
			g = e.enhance(1.75)
			e = ImageEnhance.Brightness(b)
			b = e.enhance(.6)
			img = Image.merge('RGBA', (r, g, b, a))
			e = ImageEnhance.Brightness(img)
			img = e.enhance(1.5)
			img.save('images/fried.png')
			await interaction.followup.send(file=discord.File(fp='images/fried.png'))
			await message.delete()
			os.remove('images/fried.png')
		except Exception as e:
			print(e)
			pass

	# Removed Stardew. Might re-visit if requested.

	# Slap Slash Command
	@app_commands.command(name="slap", description="What did the 5 fingers say to the face?")
	@app_commands.describe(user="Mention a user (e.g. @chris_dodgers)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def slap(self, interaction: discord.Interaction, user: discord.User):

		"""It's easier than talking... probably?"""
		Utils = self.bot.get_cog("Utils")  # Not sure at all why I am having to load this here when in CorpBot I dont have to do this. Also revisit....
		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		# Let's check if the "url" is actually a user
		test_user = user
		# Removed check for user as it is not optional running the slash command.
		# Got a user!
		user = Utils.get_avatar(interaction.user)
		targ = Utils.get_avatar(test_user)
		image = self.slap_image.copy()
		# The slapper's image will be 300x300, the slaped user's image will be 350x350
		# The top left corner of the slapper is at (487, 17)
		# The top left of the slapped user is at (167, 124)
		if not image.width == 800 or not image.height == 600:
			image = image.resize((800,600),resample=PIL.Image.LANCZOS)
		message = None
		ouch_msg = "Ouch!  That wind-up hurt my arm...  Make sure you're passing a valid user."
		user_path = await GetImage.download(user)
		if not user_path: return await Message.EmbedText(title=ouch_msg,description="I couldn't get the slapper's avatar :(").edit(interaction,message)
		targ_path = await GetImage.download(targ)
		if not targ_path: return await Message.EmbedText(title=ouch_msg,description="I couldn't get the slapped user's avatar :(").edit(interaction,message)
		# We should have the images - let's open them and convert to a single frame
		try:
			# Gather the slapper image
			user_img = Image.open(user_path)
			user_img = user_img.convert('RGBA')
			# Let's ensure it's the right size, and place it in the right spot
			user_img = user_img.resize((300,300))
			# Paste our other image on top
			image.paste(user_img,(487,17),mask=user_img)
			# Get the slapped user image
			targ_img = Image.open(targ_path)
			targ_img = targ_img.convert('RGBA')
			# Let's ensure it's the right size, and place it in the right spot
			targ_img = targ_img.resize((350,350))
			# Paste our other image on top
			image.paste(targ_img,(167,124),mask=targ_img)
			image.save('images/slapnow.png')
			await Message.Embed(
				title="Looks like someone got {}!".format(random.choice(self.slap_words)),
				description="{} was {} by {}!".format(test_user.mention,random.choice(self.slap_words),interaction.user.mention),
				file="images/slapnow.png"
			).edit(interaction,message)
			os.remove('images/slapnow.png')
		except Exception as e:
			print(e)
			pass
		for path in (user_path,targ_path):
			if os.path.exists(path): GetImage.remove(path)
