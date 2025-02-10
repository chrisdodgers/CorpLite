import asyncio, discord, aiohttp
from   discord.ext import commands
from   Cogs import Utils, Message, DisplayName, PickList
#from   lyricsgenius import Genius # TODO: Remove this line, and import in Install.py
from   urllib.parse import quote

def setup(bot):
    settings = bot.get_cog("Settings")
    if not bot.settings_dict.get("lyrics"):
        if not bot.settings_dict.get("suppress_disabled_warnings"):     
            print("\n!! Lyrics Cog has been disabled !!")
            print("* Lyrics API key is missing ('lyrics' in settings_dict.json)")
            print("* You can get a free Genius API key by signing up at:")
            print("   https://genius.com/api-clients")
            return
    bot.add_cog(Song(bot, settings))

class Song(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    @commands.command(aliases=['songinfo', 'music', 'musicinfo'])
    async def song(self, ctx, *, query : str):
        """Get data for a specific song."""
        print("Gathering song data for: " + query)
        headers = {"Authorization" : "Bearer " + self.bot.settings_dict.get("lyrics")}
        message = await ctx.send("Searching for song...")
        song = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.genius.com/search?q=' + query, headers = headers) as data:
                    if data.status != 200:
                        await message.edit(content=f"Error retrieving song data")
                        print("Error retrieving song data: "+str(data.status))
                        return
                    response = await data.json()
                    songs = response['response']['hits']
                    for hit in songs:
                        if hit['type'] == "song":
                            song = hit['result']
                            break

        except Exception as e:
            await message.edit(content=f"Error retrieving song data")
            print("Error retrieving song data")
            print(e)
            return
        
        if song != None:
            title = song['title']
            artist = song['primary_artist']['name']
            url = song['url']
            art = song['song_art_image_thumbnail_url']
            if art == None:
                art = song['header_image_thumbnail_url']
            embed = discord.Embed(
                title = "**{}**".format(title),
                color = ctx.author.color,
                description = artist,
                url = url
            )
            embed.set_thumbnail(url=art)
            embed.set_footer(text="Powered by Genius")
            await message.edit(content=None, embed=embed)
            print("Success: "+title+" by "+artist)
        else:
            message.edit(content="No results found for that query.")

    # This version of lyrics command depends on lyricsgenius library, which combines API key and scraping.
    """@commands.command(aliases=['lyric'])
    async def lyrics(self, ctx, *, query : str):
        Get lyrics for a song.
        genius = Genius(self.bot.settings_dict.get("lyrics"))
        message = await ctx.send("Searching for lyrics...")
        song = None
        try:
            song = genius.search_song(query)
        except Exception as e:
            await message.edit(content=f"Error retrieving lyrics")
            print(e)
            return
        if song != None:
            title = song.title
            artist = song.artist
            url = song.url
            lyrics = song.lyrics
            # Omit everything before the first occurrence of '[', as it contains data in weird format
            if '[' in lyrics:
                lyrics = lyrics.split('[', 1)[1]
                lyrics = '[' + lyrics  # Add the '[' back to the start
            # Remove "You might also likeEmbed" if it exists
            if "You might also likeEmbed" in lyrics:
                lyrics = lyrics.split("You might also likeEmbed")[0].strip()

            return await PickList.PagePicker(
                title="**{}** by **{}**".format(title, artist),
                ctx=ctx,
                description=lyrics,
                timeout=180,
                url=url,
                footer="Powered by Genius"
            ).pick()
        else:
            message.edit(content="No results found for that query.")"""
