import asyncio, discord
from   discord.ext import commands
from   Cogs import Utils, Message, DisplayName, PickList
from   lyricsgenius import Genius

def setup(bot):
    settings = bot.get_cog("Settings")
    if not bot.settings_dict.get("lyrics"):
        if not bot.settings_dict.get("suppress_disabled_warnings"):     
            print("\n!! Lyrics Cog has been disabled !!")
            print("* Lyrics API key is missing ('lyrics' in settings_dict.json)")
            print("* You can get a free Genius API key by signing up at:")
            print("   https://genius.com/api-clients")
            return
    bot.add_cog(Lyrics(bot, settings))

class Lyrics(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    @commands.command(aliases=['lyric'])
    async def lyrics(self, ctx, *, query : str):
        """Get lyrics for a song."""
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

            if len(lyrics) < 1500:
                await Message.EmbedText(
                    title="**{}** by **{}**".format(title, artist),
                    description=lyrics,
                    color=ctx.author,
                    footer="Powered by Genius",
                    url=url
                ).send(ctx, message)
            else:
                return await PickList.PagePicker(
                    title="**{}** by **{}**".format(title, artist),
                    ctx=ctx,
                    description=lyrics,
                    timeout=180,
                    url=url,
                    footer="Powered by Genius"
                ).pick()
        else:
            message.edit(content="No results found for that query.")
