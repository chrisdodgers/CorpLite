# CorpLite (Beta)
A forked, light version of [CorpBot.py](https://github.com/corpnewt/CorpBot.py) that is intended to be used as a Discord user app with slash commands. Full credits to [CorpNewt](https://github.com/corpnewt) for making CorpBot and the many other tools we use and love.

## What the fork is this?
The idea behind this fork is I thought to myself, *"hmmm, wouldn't it be kind of neat to use a few functions of CorpBot within private DMs and also in public servers that don't have CorpBot?"*. Well, that is what CorpLite does. 

- Currently, CorpLite has a *few* cogs that have been updated to use slash commands and Discord Interactions.
- CorpLite works within private DMs, and also servers that allow the use of external apps. 

>[!NOTE]
> CorpLite is intended to be light, as the name suggests. This is NOT a "replacement" of CorpBot, nor will ever be that. Its sole intentions is to be used as a user app which you can then use a few functions from CorpBot in areas where CorpBot might not be available.
> 
> - There is still a few more cogs that I'd like to eventually bring to CorpLite. Being solely a user app introduces new limitations/hurdles related to permissions and reliance on functions meant for server guilds for example. Once again, some cogs and/or functions will *never* be coming to CorpLite outside of just the intention of being light. 
> - This is still very much a beta. There are some known limits and items that need to be addressed in the future. However, CorpLite in its current state is pretty usable and useful. Future to be made.
> 


## Don't want nor care to host your own instance?
### [Click here to add CorpLite as a Discord User App.](https://discord.com/oauth2/authorize?client_id=1430625110947004506)

*Once added, you will see CorpLite available in your Discord App Directory. You will also see it if you type `/` anywhere within Discord and click/tap the Corp logo to see all the available commands. Additionally, you can use `/help` to also see all the available commands with their descriptions.* 


### *I want to host my own instance*:

The bot's basic settings should be in a file called `settings_dict.json` in the same folder as the `Main.py` file.  Some basic formatting of this file would look like so:

```json
{
    "token": "your_token_here",
    "weather": "your_weather_api_key_here",
}
```
Create a venv and use `Requirements.txt` to install the required packages.

# Demo:

![Screenshot1](https://github.com/chrisdodgers/CorpLite/blob/main/Demos/Screenshot1.png)

![Screenshot2](https://github.com/chrisdodgers/CorpLite/blob/main/Demos/Screenshot2.png)

![Screenshot3](https://github.com/chrisdodgers/CorpLite/blob/main/Demos/Screenshot3.png)

# Current Extensions and Commands:
```
Clippy
└─ Clippy
CogManager
└─ CogManager
Comic
└─ Comic
Encode
└─ Encode
Humor
└─ Humor
IntelArk
└─ IntelArk
Jpeg
└─ Jpeg
OpenCore
└─ OpenCore
PciUsb
└─ PciUsb
PickList
└─ PickList
Utils
└─ Utils
Weather
└─ Weather
Cogless
└─ GetImage
└─ Nullify
└─ FuzzySearch
└─ DL
└─ Message
```
- **/iark** to search an Intel CPU model (e.g. i7-10700K) to get CPU/iGPU info.
- **/weg** to search WhateverGreen's IntelHD FAQ for device-id and connector info. Use the optional search_term to search using a big/little endian device-id, AAPL,ig-platform-id, or AAPL,snb-platform-id.
- **/alc** to search a codec name or device-id to get layouts for AppleALC.
- **/listcodec** to list all codecs available (or optionally search for one).
- **/occ** to search OC Configuration.tex. You can search a path (e.g. Kernel Quirks DisableIoMapper) or can search for a specific item (e.g. SecureBootModel).
- **/plist** to upload a config.plist to validate its plist structure.
- **/slide** to upload a memmap.txt dump to calculate a slide value.
- **/pci** to look up a PCI device using pci-ids.ucw.cz. Use vvvv:dddd where vvvv is the vendor id, and dddd is the device id (e.g. 8086:3E30).
- **/usb** to look up a USB device using usb-ids.gowdy.us. Use vvvv:dddd where vvvv is the vendor id, and dddd is the device id (e.g. 8086:A36D).
- **/encode** to convert data (hex, decimal, binary, base64, and ascii).
- **/hexswap** to byte swap a hex value.
- **/mem** to convert MiB to lhex (or vise-versa).
- **/weather** to get some weather.
- **/forecast** to get some weather, for 5 days or whatever.
- **/garfield** (or **/gmg**, **/peanuts**, **/dilbert**) for getting some comics! Optionally, can specify a date (e.g. 02-11-2026).
- **/randgarfield** (or **/randgmg**, **/randpeanuts**, **/randilbert**) for getting some comics (using a random date)!
- **/clippy** to make Clippy say something.
- **/fart** to make CorpLite fart.
- **/french** to make CorpLite say something in French.
- **/german** to make CorpLite say something in German - probably.
- **/fry** to burn an uploaded image to a crisp.
- **/jpeg** to jpegify an uploaded image.
- **/poke** to hopefully make something do...something...
- **/memetemp** to search and grab a meme template.
- **/meme** to use a meme template id and to make some memes.
- **/slap** to slap someone by specifying who you want to slap (e.g. *@chris_dodgers*).
- **/zalgo** to enter a message that turns into something...interesting.
- **/extensions** to view what cogs are running.

# Known Issues/Random Notes:

- Using **/randgarfield** *(or any of the other random comic commands)* within private DMs may fail to embed. Sometimes it works, sometimes it doesn't. This also applies to **/meme** from my testing. Its a 50/50 if it embeds right within DMs.
- Hosting an instance and seeing `"Ignore This Until A Future Update Failed!"` in logs. This is due to very temporarily not defining any cogs within `self.preload` in CogManager. This will be addressed and Settings will at some point be added back here instead of this silly placeholder.
- *"I can't reply or reference a URL from a message containing a file in use with /slide or /plist."* This currently is a limitation that will most likely not be solved relating to DMs. The current workaround is *only* handling direct uploaded attachments and temporarily removing the handling for message URLs.
- *"Some comics are missing that were available in CorpBots Comic.py!"* Due to keeping limits in mind of the max amount of slash commands that can be registered *(and trying to keep the bot a bit cleaner)*, I have commented out some comics that seemingly rarely or never get used. The code has been updated for said comics, but they just need to be uncommented if you intend to use them.

*There could be some more known issues/limitations at the current time that I am forgetting to mention.*

# Credits:

- [CorpNewt](https://github.com/corpnewt) for creating CorpBot, and many of the amazing tools we use and love. Thanks for all the contributions you've made in the community over the years and for all you've taught me and others. 


