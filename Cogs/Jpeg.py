import discord, time, os
import io
from PIL import Image, ImageFilter, ImageEnhance
from discord import app_commands
from discord.ext import commands
from Cogs import GetImage, Message
from io import BytesIO

async def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	await bot.add_cog(Jpeg(bot, settings))

class Jpeg(commands.Cog):

	# Init with the bot reference
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils
		Utils = self.bot.get_cog("Utils")


	# Removed canDisplay

	# JPEG Slash Command
	@app_commands.command(name="jpeg", description="Do I look like I know what a JPEG is?")
	@app_commands.describe(image="Upload an image (e.g. bigmeme.png)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def jpeg(self, interaction, image: discord.Attachment):
		"""MOAR JPEG!  Accepts an attached image."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		message = None
		image_upload = await image.read()

		fn = os.path.splitext(image.filename)[0]
		path = os.path.join(fn + ".jpeg")
		# JPEEEEEEEEGGGGG
		try:
			i = Image.open(io.BytesIO(image_upload))
			# Get the first frame, and replace transparency with black
			i = i.convert("RGBA")
			bg = Image.new(i.mode[:-1],i.size,"black")
			bg.paste(i,i.split()[-1])
			i = bg
			# Enhance the edges
			i = i.filter(ImageFilter.EDGE_ENHANCE)
			# Blur the image to offset the edges - use a box blur with a radius
			# of the image's largest edge/200 and rounded to the nearest int (min of 1)
			blur_amount = max(i.size)/200
			blur_amount = int(blur_amount) + (1 if blur_amount-int(blur_amount)>=0.5 else 0)
			blur_amount = max(blur_amount,1) # Minimum of 1 px blur amount
			i = i.filter(ImageFilter.BoxBlur(blur_amount))
			# Enhance the saturation to ensure colors don't get drowned out by the
			# jpeg compression
			converter = ImageEnhance.Color(i)
			i = converter.enhance(1.2)
			# Offset the blur by sharpening the image again
			converter = ImageEnhance.Sharpness(i)
			i = converter.enhance(2.5)
			# Resize the image to 80% - and save it with extreme compression
			w,h = i.size
			i = i.resize((int(w*0.8),int(h*0.8)),Image.NEAREST)
			# Save it to a temp image path
			half_bytes = BytesIO()
			i.save(half_bytes,"JPEG",quality=1)
			# Seek to the start in memory
			half_bytes.seek(0)
			# Load it again - then resize it up
			i = Image.open(half_bytes)
			i = i.resize((int(w),int(h)),Image.NEAREST)
			# Save it to a path ending in .jpeg
			if not image.filename.lower().endswith((".jpeg", ".jpg")):
				# Strip .jpg if needed
				if image.filename.lower().endswith(".jpg"):
					path = image_upload[:-4]
				path = os.path.join(fn+".jpeg")
			i.save(path,"JPEG",quality=1)
			# Upload and send
			await Message.Embed(file=path, title="Moar Jpeg!").edit(interaction, message)
		except:
			await Message.Embed(title="An error occurred!", description="I couldn't jpegify that image...  Make sure you're pointing me to a valid image file.").edit(interaction, message)
		GetImage.remove(path)
