import asyncio, discord, datetime, re
import geopy.geocoders
from geopy.adapters import AioHTTPAdapter
from geopy.geocoders import Nominatim
from   discord.ext import commands
from discord import app_commands
from   Cogs import Message, PickList, DL

async def setup(bot):

	if not bot.settings_dict.get("weather"):
		if not bot.settings_dict.get("suppress_disabled_warnings"):
			print("\n!! Weather Cog has been disabled !!")
			print("* Weather API key is missing ('weather' in settings_dict.json)")
			print("* You can get a free openweathermap API key by signing up at:")
			print("   https://openweathermap.org/home/sign_up")
			print("* Or if you already have an account, create/copy your API key at:")
			print("   https://home.openweathermap.org/api_keys\n")
		return
	await bot.add_cog(Weather(bot))

# This is the Weather module
class Weather(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.weather_timeout = bot.settings_dict.get("weather_timeout",15)
		if not isinstance(self.weather_timeout,int):
			self.weather_timeout = 15
		# Min of 5 seconds, max of 100
		self.weather_timeout = min(100,max(self.weather_timeout,5))
		# Increase the default timeout to 15 seconds
		geopy.geocoders.options.default_timeout = 15
		self.user_agent = "CorpLite"

	def _get_output(self, w_text):
		# https://openweathermap.org/weather-conditions
		w_lower = w_text.lower()
		if "clear" in w_lower:
			return "☀️ "+w_text
		if "thunder" in w_lower:
			return "⛈️ "+w_text
		if "tornado" in w_lower:
			return "🌪️ "+w_text
		if "broken clouds" in w_lower:
			return "⛅ "+w_text
		if any(x in w_lower for x in ["few clouds", "scattered clouds"]):
			return "🌤️ "+w_text
		if "clouds" in w_lower:
			return "☁️ "+w_text
		if any(x in w_lower for x in ["snow", "freezing rain"]):
			return "🌨️ "+w_text
		if any(x in w_lower for x in ["rain", "drizzle", "sleet"]):
			return "🌧️ "+w_text
		if any(x in w_lower for x in ["mist", "smoke", "haze", "sand", "fog", "dust", "ash", "squalls"]):
			return "️🌫️ "+w_text
		return w_text

	def _check_float(self, f, round_to=4):
		if f == int(f): return int(f)
		if round_to<=0: return f
		temp = f*10**round_to
		if temp-int(temp) >= 0.5: temp += 1
		return self._check_float(int(temp)/10**round_to,round_to=0)

	def _f_to_c(self, f):
		return self._check_float((f-32)/1.8,round_to=2)
	def _c_to_f(self, c):
		return self._check_float((c*1.8)+32,round_to=2)
	def _c_to_k(self, c):
		return self._check_float(c+273.15,round_to=2)
	def _k_to_c(self, k):
		return self._check_float(k-273.15,round_to=2)
	def _f_to_k(self, f):
		return self._c_to_k(self._f_to_c(f))
	def _k_to_f(self, k):
		return self._c_to_f(self._k_to_c(k))
	def _f_to_r(self, f):
		return self._check_float(f+459.67)
	def _r_to_f(self, r):
		return self._check_float(r-459.67)
	def _c_to_r(self, c):
		return self._f_to_r(self._c_to_f(c))
	def _r_to_c(self, r):
		return self._f_to_c(self._r_to_f(r))
	def _k_to_r(self, k):
		return self._f_to_r(self._k_to_f(k))
	def _r_to_k(self, r):
		return self._f_to_k(self._r_to_f(r))

	# Weather Slash Command:
	# @app_commands.command(name="tconvert", description="Converts between Fahrenheit, Celsius, and Kelvin.")
	@app_commands.describe(temp="Enter a temperature value (e.g. 72):")
	@app_commands.describe(f="Enter what you want to convert from (e.g. Fahrenheit):")
	@app_commands.describe(t="Enter what you want to convert to (e.g. Celsius):")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def tconvert(self, interaction: discord.Interaction, temp: str, f: str, t: str):
		"""Converts between Fahrenheit, Celsius, and Kelvin.  From/To types can be:
		(F)ahrenheit
		(C)elsius
		(K)elvin
		(R)ankine"""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)
		
		types = [ "Fahrenheit", "Celsius", "Kelvin", "Rankine" ]
		usage = "Usage: `{}tconvert [temp] [from_type] [to_type]`"
		if not temp:
			return await interaction.followup.send(usage)
		args = temp.split()
		if not len(args) == 3:
			return await interaction.followup.send(usage)
		try:
			f = next((x for x in types if x.lower() == args[1].lower() or x.lower()[:1] == args[1][:1].lower()), None)
			t = next((x for x in types if x.lower() == args[2].lower() or x.lower()[:1] == args[2][:1].lower()), None)
			m = float(args[0])
		except:
			return await interaction.followup.send(usage)
		if not(f) or not(t):
			# No valid types
			return await interaction.followup.send("Current temp types are: {}".format(", ".join(types)))
		if f == t:
			# Same in as out
			return await interaction.followup.send("No change when converting {} ---> {}.".format(f, t))
		output = "I guess I couldn't make that conversion..."
		try:
			out_val = None
			if f == "Fahrenheit":
				if t == "Celsius":
					out_val = self._f_to_c(m)
				elif t == "Rankine":
					out_val = self._f_to_r(m)
				else:
					out_val = self._f_to_k(m)
			elif f == "Celsius":
				if t == "Fahrenheit":
					out_val = self._c_to_f(m)
				elif t == "Rankine":
					out_val = self._c_to_r(m)
				else:
					out_val = self._c_to_k(m)
			elif f == "Rankine":
				if t == "Fahrenheit":
					out_val = self._r_to_f(m)
				elif t == "Celsius":
					out_val = self._r_to_c(m)
				else:
					out_val = self._r_to_k(m)
			else:
				if t == "Celsius":
					out_val = self._k_to_c(m)
				elif t == "Rankine":
					out_val = self._k_to_r(m)
				else:
					out_val = self._k_to_f(m)
			output = "{:,} {}{} is {:,} {}{}".format(
				self._check_float(float(m),round_to=2),
				"" if f == "Kelvin" else "degree " if abs(m)==1 else "degrees ",
				f,
				out_val,
				"" if t == "Kelvin" else "degree " if abs(out_val)==1 else "degrees ",
				t
			)
		except:
			pass
		await interaction.followup.send(output)

	def get_weather_text(self, r = {}, show_current = True):
		# Returns a string representing the weather passed
		main    = r["main"]
		weath   = r["weather"]
		# Make sure we get the temps in both F and C
		tc   = self._k_to_c(main["temp"])
		tf   = self._c_to_f(tc)
		minc = self._k_to_c(main["temp_min"])
		minf = self._c_to_f(minc)
		maxc = self._k_to_c(main["temp_max"])
		maxf = self._c_to_f(maxc)
		hum  = main.get("humidity")
		fl_c = fl_f = None
		if "feels_like" in main:
			fl_c = self._k_to_c(main["feels_like"])
			fl_f = self._c_to_f(fl_c)
		# Gather the formatted conditions
		weath_list = []
		for x,y in enumerate(weath):
			d = y["description"]
			if x == 0:
				d = d.capitalize()
			weath_list.append(self._get_output(d))
		condition = ", ".join(weath_list)
		# Format the description
		if show_current:
			desc = "{} °F ({} °C){}{}\n\n".format(
				tf,
				tc,
				"\n\nFeels like {} °F ({} °C)".format(fl_f,fl_c) if fl_c is not None else "",
				"\n\n{}% Humidity".format(hum) if hum is not None else ""
			)
		else:
			desc = ""
		desc += "{}\n\nHigh of {} °F ({} °C) - Low of {} °F ({} °C)\n\n".format(
			condition,
			maxf, maxc,
			minf, minc
		)
		return desc

	# Weather Slash Command:
	@app_commands.command(name="weather", description="Get some weather")
	@app_commands.describe(city_name="Enter a city name (e.g. Los Angeles)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def weather(self, interaction: discord.Interaction, city_name: str):
		"""Gets some weather."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		# Load and define the Encode Cog
		# weather_cog = bot.get_cog("Weather")

		if city_name is None:
			return await interaction.followup.send("Usage: `/weather [city_name]`")
		# Strip anything that's non alphanumeric or a space
		city_name = re.sub(r'([^\s\w]|_)+', '', city_name)
		message = await interaction.followup.send("Gathering weather data...")

		try:
			user_agent = "CorpLite"
			async with Nominatim(user_agent=user_agent, adapter_factory=AioHTTPAdapter) as geolocator:
				location = await geolocator.geocode(city_name)
		except:
			return await message.edit(content="Something went wrong geolocating...")
		if location is None:
			return await message.edit(content="I couldn't find that city...")
		title = location.address
		# Just want the current weather
		try:
			r = await DL.async_json("http://api.openweathermap.org/data/2.5/weather?appid={}&lat={}&lon={}".format(
				self.bot.settings_dict.get("weather", ""),
				location.latitude,
				location.longitude
			))


		except:
			return await message.edit(content="Something went wrong querying openweathermap.org...")
		desc = self.get_weather_text(r)
		# Let's post it!
		await Message.EmbedText(
			title=title,
			description=desc,
			color=interaction.user,
			footer="Powered by OpenWeatherMap"
		).send(interaction, message)

	# Forecast Slash Command:
	@app_commands.command(name="forecast", description="Gets some weather, for 5 days or whatever.")
	@app_commands.describe(city_name="Enter a city name (e.g. Los Angeles)")
	@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
	@app_commands.user_install()
	async def forecast(self, interaction: discord.Interaction, city_name: str):
		"""Gets some weather, for 5 days or whatever."""

		# Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
		await interaction.response.defer(thinking=True)

		# Load and define the Encode Cog
		# weather_cog = bot.get_cog("Weather")

		if city_name is None:
			return await interaction.followup.send("Usage: `/forecast [city_name]`")
		# Strip anything that's non alphanumeric or a space
		city_name = re.sub(r'([^\s\w]|_)+', '', city_name)
		message = await interaction.followup.send("Gathering forecast data...")
		try:

			async with Nominatim(user_agent=self.user_agent,adapter_factory=AioHTTPAdapter) as geolocator:
				location = await geolocator.geocode(city_name)
		except:
			return await message.edit(content="Something went wrong geolocating...")
		if location is None:
			return await message.edit(content="I couldn't find that city...")
		title = location.address
		# We want the 5-day forecast at this point
		try:
			r = await DL.async_json("http://api.openweathermap.org/data/2.5/forecast?appid={}&lat={}&lon={}".format(
				self.bot.settings_dict.get("weather",""),
				location.latitude,
				location.longitude
			))
		except:
			return await message.edit(content="Something went wrong querying openweathermap.org...")
		days = {}
		for x in r["list"]:
			# Check if the day exists - if not, we set up a pre-day
			day = x["dt_txt"].split(" ")[0]
			is_noon = "12:00:00" in x["dt_txt"]
			if not day in days:
				days[day] = {
					"main":x["main"],
					"weather":x["weather"],
					"day_count":1
				}
				continue
			# Day is in the list - let's check values
			if x["main"]["temp_min"] < days[day]["main"]["temp_min"]:
				days[day]["main"]["temp_min"] = x["main"]["temp_min"]
			if x["main"]["temp_max"] > days[day]["main"]["temp_max"]:
				days[day]["main"]["temp_max"] = x["main"]["temp_max"]
			# Add the temp
			days[day]["main"]["temp"] += x["main"]["temp"]
			days[day]["day_count"] += 1
			# Set the weather data if is noon
			if is_noon:
				days[day]["weather"] = x["weather"]
		fields = []
		for day in sorted(days):
			# Average the temp, strip weather duplicates
			days[day]["main"]["temp"]/=days[day]["day_count"]
			fields.append({
				"name":datetime.datetime.strptime(day,"%Y-%m-%d").strftime("%A, %b %d, %Y")+":",
				"value":self.get_weather_text(days[day], False),
				"inline":False
			})
		# Now we send our embed!
		await Message.Embed(
			title=title,
			fields=fields,
			color=interaction.user,
			footer="Powered by OpenWeatherMap"
		).send(interaction, message)