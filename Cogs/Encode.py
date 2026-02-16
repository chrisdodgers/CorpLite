import asyncio, discord, base64, binascii, re, os, random
from discord import app_commands
from   discord.ext import commands
from   Cogs import DL, Message, Nullify
from   PIL import Image

async def setup(bot):
	# Add the bot and deps
	# Removed settings
	await bot.add_cog(Encode(bot))

class Encode(commands.Cog):

	# Init with the bot reference
	def __init__(self, bot):
		self.bot = bot
		self.types = (
			# Decimal types
			"decimal",
			"dec",
			"d",
			"integer",
			"int",
			"i",
			# Base64 types
			"base64",
			"b64",
			"b",
			# Binary types
			"binary",
			"bin",
			# Ascii/text types
			"ascii",
			"a",
			"text",
			"t",
			"string",
			"str",
			"s",
			# Hex types
			"hexadecimal",
			"hex",
			"h",
			# - Big endian specifics
			"bhex",
			"hexb",
			"bh",
			"hb",
			# - Little endian specifics
			"lhex",
			"hexl",
			"lh",
			"hl",
			# - Big endian full hex value
			"bitb",
			"bbit",
			"bb",
			# - Little endian full hex value
			"bitl",
			"lbit",
			"bl",
			"lb"
		)
		self.padded_prefixes = (
			"bin",
			"hexadecimal",
			"hex",
			"h",
			"bh",
			"hb",
			"hexb",
			"lh",
			"hl",
			"hexl",
			"bitl",
			"lb",
			"bitb",
			"bb"
		)
		self.display_types = (
			"(d)ecimal/(i)nteger",
			"(b)ase64",
			"(bin)ary",
			"(a)scii/(t)ext/(s)tring",
			"(h)ex/bhex/lhex",
			"(lb)it/(bb)it"
		)

		# Removed Utils and DisplayName


	# Helper methods
	def _to_bytes(self, in_string):
		return in_string.encode('utf-8')
	
	def _to_string(self, in_bytes, split_hex = 0):
		out_str = in_bytes.decode("utf-8")
		if split_hex>0: # Break into chunks of split_hex size
			out_str = " ".join((out_str[0+i:split_hex+i] for i in range(0, len(out_str), split_hex))).upper()
		return out_str

	# Check hex value
	def _check_hex(self, hex_string):
		# Remove 0x/0X
		hex_string = hex_string.replace("0x", "").replace("0X", "")
		hex_string = re.sub(r'[^0-9A-Fa-f]+', '', hex_string)
		return hex_string

	def _convert_value(self, val, from_type, to_type):
		# Normalize case
		from_type = from_type.lower()
		to_type = to_type.lower()
		# Ensure types are valid
		if (not from_type in self.types \
		and not from_type.startswith(self.padded_prefixes)) \
		or (not to_type in self.types \
		and not to_type.startswith(self.padded_prefixes)):
			raise Exception("Invalid from or to type")
		# Resolve the value to hex bytes
		if from_type.startswith(("d","i")):
			val_hex = "{:x}".format(int(val))
			val_adj = binascii.unhexlify("0"*(len(val_hex)%2)+val_hex)
		elif from_type.startswith("bin"):
			val_hex = "{:x}".format(int("".join([x for x in val if x in "01"]),2))
			val_adj = binascii.unhexlify("0"*(len(val_hex)%2)+val_hex)
		elif from_type.startswith("b") and not from_type.startswith(self.padded_prefixes):
			if len(val)%4: # Pad with =
				val += "="*(4-len(val)%4)
			val_adj = base64.b64decode(val.encode())
		elif from_type.startswith(("a","t","s")):
			val_adj = binascii.hexlify(val.encode())
			val_adj = val.encode()
		elif from_type.startswith(("lh","hl","hexl")): # Little-endian
			val = self._check_hex(val)
			val = "0"*(len(val)%2)+val
			hex_rev = "".join(["".join(x) for x in [val[i:i + 2] for i in range(0,len(val),2)][::-1]])
			val_adj = binascii.unhexlify(hex_rev)
		elif from_type.startswith(("bitl","lb","bl")): # Little-endian bit-level
			val = self._check_hex(val)
			pad = self._get_pad(from_type, default_pad=0)
			# Ensure we have pads in 8-bit increments
			pad = int(8-pad%8+pad if pad%8 else pad)
			# Can't have a 0 pad
			pad = max(pad,8)
			# Convert to binary
			val = "{:b}".format(int(val,16))
			# Pad if needed
			if len(val)%pad:
				val = "0"*(pad-len(val)%pad)+val
			val_hex = "{:x}".format(int(val[::-1],2))
			val_adj = binascii.unhexlify("0"*(len(val_hex)%2)+val_hex)
		else: # Assume bhex/hex
			val = self._check_hex(val)
			val_adj = binascii.unhexlify("0"*(len(val)%2)+val)
		# At this point - everything is converted to hex bytes - let's convert
		out = None
		if to_type.startswith(("d","i")):
			out = str(int(binascii.hexlify(val_adj).decode(),16))
		elif to_type.startswith("bin"):
			out = "{:b}".format(int(binascii.hexlify(val_adj).decode(),16))
			# Get our chunk/pad size - use 8 as a fallback
			pad = self._get_pad(to_type, default_pad=8)
			# Can't have a 0 pad
			if pad <= 0: pad = 8
			# Pad if needed
			if len(out)%pad:
				out = "0"*(pad-len(out)%pad)+out
			# Split into chunks
			out = "{}".format(" ".join((out[0+i:pad+i] for i in range(0,len(out),pad))))
		elif to_type.startswith("b") and not to_type.startswith(self.padded_prefixes):
			out = base64.b64encode(val_adj).decode()
		elif to_type.startswith(("a","t","s")):
			out = val_adj.decode()
		elif to_type.startswith(("lh","hl","hexl")): # Little-endian
			pad = self._get_pad(to_type, default_pad=8)
			# Ensure we have pads in 8-bit increments
			pad = int((8-pad%8+pad if pad%8 else pad)/4)
			out = binascii.hexlify(val_adj).decode().upper() # Get the hex values as a string
			if len(out) < pad:
				# Make sure we pad to the correct amount
				out = "0"*(pad-len(out))+out
			# Ensure it's an even number of elements as well
			pad_val = "0"*(len(out)%2)+out
			out = "".join(["".join(x) for x in [pad_val[i:i + 2] for i in range(0,len(pad_val),2)][::-1]]).upper()
			# Also split into chunks of 8 for readability
			out = "0x"+" ".join((out[0+i:8+i] for i in range(0,len(out),8)))
		elif to_type.startswith(("bitl","lb","bl")):
			pad = self._get_pad(to_type, default_pad=8)
			# Ensure we have pads in 8-bit increments
			pad = int(8-pad%8+pad if pad%8 else pad)
			# Can't have a 0 pad
			pad = max(pad,8)
			out = "{:b}".format(int(binascii.hexlify(val_adj).decode(),16)) # Get the hex value in binary
			if len(out)%pad:
				# Make sure we pad to the correct amount
				out = "0"*(pad-len(out)%pad)+out
			# Reverse the bits and convert to hex
			out = "{:x}".format(int(out[::-1],2)).upper()
			# Ensure it's an even number of elements as well
			out = "0"*(len(out)%2)+out
			# Also split into chunks of 8 for readability
			out = "0x"+" ".join((out[0+i:8+i] for i in range(0,len(out),8)))
		else:
			pad = self._get_pad(to_type, default_pad=0)
			# Ensure we have pads in 8-bit increments
			pad = int((8-pad%8+pad if pad%8 else pad)/4)
			out = binascii.hexlify(val_adj).decode().upper()
			if from_type.startswith(("d","i","bin")) and pad == 0: # No need to pad to an even length - but prepend 0x
				out = "0x"+out
			else:
				out = binascii.hexlify(val_adj).decode().upper() # Get the hex values as a string
				if len(out) < pad:
					# Make sure we pad to the correct amount
					out = "0"*(pad-len(out))+out
				# Ensure it's an even number of elements as well
				pad_val = "0"*(len(out)%2)+out
				# Also split into chunks of 8 for readability
				out = "0x"+" ".join((out[0+i:8+i] for i in range(0,len(out),8)))
		return out

	def _get_pad(self, type_string, default_pad = 0):
		pad = default_pad
		m = re.search(r"\d",type_string)
		if m:
			try: pad = abs(int(type_string[m.start():]))
			except: pass
		return pad

	# To base64 methods
	def _ascii_to_base64(self, ascii_string):
		ascii_bytes = self._to_bytes(ascii_string)
		base_64     = base64.b64encode(ascii_bytes)
		return self._to_string(base_64)

	def _hex_to_base64(self, hex_string):
		hex_string    = self._check_hex(hex_string)
		hex_s_bytes   = self._to_bytes(hex_string)
		hex_bytes     = binascii.unhexlify(hex_s_bytes)
		base64_bytes  = base64.b64encode(hex_bytes)
		return self._to_string(base64_bytes)

	# To ascii methods
	def _hex_to_ascii(self, hex_string):
		hex_string  = self._check_hex(hex_string)
		hex_bytes   = self._to_bytes(hex_string)
		ascii_bytes = binascii.unhexlify(hex_bytes)
		return self._to_string(ascii_bytes)

	def _base64_to_ascii(self, base64_string):
		if len(base64_string) % 4: base64_string+="="*(4-(len(base64_string)%4))
		base64_bytes  = self._to_bytes(base64_string)
		ascii_bytes   = base64.b64decode(base64_bytes)
		return self._to_string(ascii_bytes)

	# To hex methods
	def _ascii_to_hex(self, ascii_string):
		ascii_bytes = self._to_bytes(ascii_string)
		hex_bytes   = binascii.hexlify(ascii_bytes)
		return self._to_string(hex_bytes,split_hex=8)

	def _base64_to_hex(self, base64_string):
		if len(base64_string) % 4: base64_string+="="*(4-(len(base64_string)%4))
		b64_string   = self._to_bytes(base64_string)
		base64_bytes = base64.b64decode(b64_string)
		hex_bytes    = binascii.hexlify(base64_bytes)
		return self._to_string(hex_bytes,split_hex=8)

	def _rgb_to_hex(self, r, g, b):
		return "#{:02x}{:02x}{:02x}".format(r,g,b).upper()

	def _hex_to_rgb(self, _hex):
		_hex = _hex.lower().replace("#", "").replace("0x","")
		l_hex = len(_hex)
		return tuple(int(_hex[i:i + l_hex // 3], 16) for i in range(0, l_hex, l_hex // 3))

	def _hex_to_cmyk(self, _hex):
		return self._rgb_to_cmyk(*self._hex_to_rgb(_hex))

	def _cmyk_to_hex(self, c, m, y, k):
		return self._rgb_to_hex(*self._cmyk_to_rgb(c,m,y,k))

	def _cmyk_to_rgb(self, c, m, y, k):
		c, m, y, k = [float(x)/100.0 for x in tuple([c, m, y, k])]
		return tuple([round(255.0 - ((min(1.0, x * (1.0 - k) + k)) * 255.0)) for x in tuple([c, m, y])])

	def _rgb_to_cmyk(self, r, g, b):
		c, m, y = [1 - x/255 for x in tuple([r, g, b])]
		min_cmy = min(c, m, y)
		return tuple([0,0,0,100]) if all(x == 0 for x in [r, g, b]) else tuple([round(x*100) for x in [(x - min_cmy) / (1 - min_cmy) for x in tuple([c, m, y])] + [min_cmy]])

	def _hex_int_to_tuple(self, _hex):
		return (_hex >> 16 & 0xFF, _hex >> 8 & 0xFF, _hex & 0xFF)




	# Grab and process types for use for autocomplete in /encode
	# Maybe later sort alphabetically and add another types list since some are just aliases basically like lhex, hexl, lh for example.
	async def encode_type_autocomplete(self, interaction: discord.Interaction, current: str):
		types = self.types if self else []
		results = [t for t in types if current.lower() in t.lower()]
		return [app_commands.Choice(name=t, value=t) for t in results[:25]]

	# Encode Slash Command:
	@app_commands.command(name="encode", description="Data converter that supports hex, decimal, binary, base64, and ascii.")
	@app_commands.describe(from_type="What you are converting from (e.g. `hex`):")
	@app_commands.describe(to_type="What you are converting to (e.g. `lhex`):")
	@app_commands.describe(value="The value you are wanting to convert (e.g. 0x3EA50000)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	@app_commands.autocomplete(from_type=encode_type_autocomplete, to_type=encode_type_autocomplete)
	async def encode(self, interaction: discord.Interaction, from_type: str, to_type: str, value: str):
		"""Data converter that supports hex, decimal, binary, base64, and ascii."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		usage = 'Usage: `/encode [from_type] [to_type] [value]`\nAvailable types include:\n- {}'

		if from_type is None or to_type is None:
			return await interaction.followup.send(usage)

		# Find out if we're replying to another message
		# Currently disabled since I haven't figured out how to update Utils functions yet...
		reply = None
		# if ctx.message.reference:
		# Resolve the replied to reference to a message object
		#    try:
		#        message = await Utils.get_replied_to(ctx.message, ctx=interaction)
		#        reply = await Utils.get_message_content(message)
		#    except:
		#        pass
		if reply:  # Use the replied to message content instead
			value = reply

		if not value:
			return await interaction.followup.send(usage)

		for v, n in ((from_type, "from"), (to_type, "to")):
			if not v.lower() in self.types and not v.lower().startswith(self.padded_prefixes):
				return await interaction.followup.send(
					"Invalid *{}* type!\nAvailable types include:\n- {}".format(n,
																				"\n- ".join(self.display_types)))

		if from_type.lower() == to_type.lower():
			return await interaction.followup.send("*Poof!* Your encoding was done before it started!")

		try:
			return await interaction.followup.send(
				Nullify.escape_all(self._convert_value(value, from_type, to_type)))
		except Exception as e:
			return await interaction.followup.send(Nullify.escape_all("I couldn't make that conversion:\n{}".format(e)))

	# Hexswap Slash Command:
	@app_commands.command(name="hexswap", description="Enter a hex value to byte swap.")
	@app_commands.describe(input_hex="Enter a hex value (e.g. 0x3EA50000):")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def hexswap(self, interaction: discord.Interaction, input_hex: str):
		"""Byte swaps the passed hex value."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		if input_hex is None:
			return await interaction.followup.send("Usage: `/hexswap [input_hex]`")
		input_hex = self._check_hex(input_hex)
		if not len(input_hex):
			return await interaction.followup.send("Malformed hex - try again.")
		# Normalize hex into pairs
		input_hex = list("0" * (len(input_hex) % 2) + input_hex)
		hex_pairs = [input_hex[i:i + 2] for i in range(0, len(input_hex), 2)]
		hex_rev = hex_pairs[::-1]
		hex_str = "".join(["".join(x) for x in hex_rev])
		await interaction.followup.send(hex_str.upper())

	# Define and process types for use for autocomplete in /mem
	async def mem_type_autocomplete(self, interaction: discord.Interaction, current: str):
		types = ["MiB", "lhex"]
		results = [t for t in types if current.lower() in t.lower()]
		return [app_commands.Choice(name=t, value=t) for t in results[:25]]


	# Mem Slash Command:
	@app_commands.command(name="mem", description="Convert between MiB and little-endian hex.")
	@app_commands.describe(from_type="Convert from (MiB or lhex):")
	@app_commands.describe(to_type="Convert to (MiB or lhex):")
	@app_commands.describe(value="The value you are wanting to convert (e.g. 26MiB or 0000A001)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	@app_commands.autocomplete(from_type=mem_type_autocomplete, to_type=mem_type_autocomplete)
	async def mem(self, interaction: discord.Interaction, from_type: str, to_type: str, value: str):
		"""Converts between MiB and little-endian hexadecimal (lhex)."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		try:
			from_type = from_type.lower()
			to_type = to_type.lower()
			val = value.strip()

			# Convert MiB to lhex
			if from_type == "mib" and to_type == "lhex":
				# Store as a float, remove mib if present in the search
				num = float(val.lower().replace("mib", "").strip())
				# Convert to bytes
				bytes_val = int(num * 1024 * 1024)
				# Use _convert_value to handle decimal to lhex conversion
				out = self._convert_value(str(bytes_val), "decimal", "lhex")
				return await interaction.followup.send(Nullify.escape_all(out))
                # Seacrest out!

			# Convert lhex to MiB
			elif from_type == "lhex" and to_type == "mib":
				# Convert from lhex to decimal
				dec_val = self._convert_value(val, "lhex", "decimal")
				# Convert to MiB
				mib_val = round(int(dec_val) / (1024 * 1024), 4)
				return await interaction.followup.send(f"{mib_val}MiB")

			else:
				return await interaction.followup.send("Invalid conversion. Use proper `MiB` or `lhex` values only.")

		except Exception as e:
			print(f"[mem] Exception occurred: {e}")
			return await interaction.followup.send(Nullify.escape_all("I couldn't make that conversion:\n{}".format(e)))
