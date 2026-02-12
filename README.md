# CorpLite (Beta)
A forked, light version of [CorpBot.py](https://github.com/corpnewt/CorpBot.py) that is intended to be used as a Discord user app with slash commands. Full credits to [CorpNewt](https://github.com/corpnewt) for making CorpBot and the many other tools we use and love.

## What the fork is this?
The idea behind this fork is I thought to myself, *"hmmm, wouldn't it be kind of neat to use a few functions of CorpBot within private DMs and also in public servers that don't have CorpBot?"*. Well, that is what CorpLite does. 

- Currently, CorpLite has a *few* cogs that have been updated to use slash commands and Discord Interactions.
- CorpLite works within private DMs, and also servers that allow the use of external apps. 

>[!NOTE]
> CorpLite is intended to be light, as the name suggests. This is NOT a "replacement" of CorpBot, nor will ever be that. Its sole intentions is to be used as a user app which you can then use a few functions from CorpBot in areas where CorpBot might not be available.
> 
> - Some cogs I'd like to eventually add are currently missing and it is in the roadwork plans for a future update. Example: Utils, DisplayName, Settings, Humor, Music, etc.
> - Being solely a user app introduces new limitations related to permissions/intents. Once again, some cogs and/or functions will *never* be coming to CorpLite outside of just the intention of being light. 
> - This is still very much a beta. There are some known limits and items that need to be addressed in the future. However, CorpLite in its current state is pretty usable and useful. Future updates will be made.
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
CogManager
└─ CogManager
Comic
└─ Comic
Encode
└─ Encode
IntelArk
└─ IntelArk
OpenCore
└─ OpenCore
PciUsb
└─ PciUsb
PickList
└─ PickList
Weather
└─ Weather
Cogless
└─ Nullify
└─ FuzzySearch
└─ DL
└─ Message

```
- **/iark** to search an Intel CPU model (e.g. i7-10700K) to get CPU/iGPU info.,
- **/weg** to search WhateverGreen's IntelHD FAQ for device-id and connector info. Use the optional search_term to search using a big/little endian device-id, AAPL,ig-platform-id, or AAPL,snb-platform-id.,
- **/alc** to search a codec name or device-id to get layouts for AppleALC.,
- **/listcodec** to list all codecs available (or optionally search for one).,
- **/occ** to search OC Configuration.tex. You can search a path (e.g. Kernel Quirks DisableIoMapper) or can search for a specific item (e.g. SecureBootModel).,
- **/plist** to upload a config.plist to validate its plist structure.,
- **/slide** to upload a memmap.txt dump to calculate a slide value.,
- **/pci** to look up a PCI device using pci-ids.ucw.cz. Use vvvv:dddd where vvvv is the vendor id, and dddd is the device id (e.g. 8086:3E30).,
- **/usb** to look up a USB device using usb-ids.gowdy.us. Use vvvv:dddd where vvvv is the vendor id, and dddd is the device id (e.g. 8086:A36D).,
- **/encode** to convert data (hex, decimal, binary, base64, and ascii).,
- **/hexswap** to byte swap a hex value.,
- **/mem** to convert MiB to lhex (or vise-versa).,
- **/weather** to get some weather.,
- **/forecast** to get some weather, for 5 days or whatever.,
- **/garfield** (or **/gmg**, **/peanuts**, **/dilbert**) for getting some comics! Optionally, can specify a date (e.g. 02-11-2026).,
- **/randgarfield** (or **/randgmg**, **/randpeanuts**, **/randilbert**) for getting some comics (using a random date)!,
- **/extensions** to view what cogs are running.

# Known Issues/Random Notes:

- Using **/randgarfield** *(or any of the other random comic commands)* within private DMs may fail. Especially more or so when DMing CorpLite directly. So far this behavior has not been observed with non-random comic commands nor random comic commands used within a server *(as an external app)*. 
- Hosting an instance and seeing `"Ignore This Until A Future Update Failed!"` in logs. This is due to very temporarily not defining any cogs within `self.preload` in CogManager. This will be addressed and Settings will at some point be added back here instead of this silly placeholder.
- *"I can't reply or reference a URL from a message containing a file in use with /slide or /plist."* This currently is a limitation I have not figured out, nor might not be able to figure out. The current workaround is *only* handling direct uploaded attachments and temporarily removing the handling for URLs. If I find a way to fix this functionality - I will bring it back.
- *"Some comics are missing that were available in CorpBots Comic.py!"* Due to keeping limits in mind of the max amount of slash commands that can be registered *(and trying to keep the bot a bit cleaner)*, I have commented out some comics that seemingly rarely or never get used. The code has been updated for said commics, but they just need to be uncommented if you intend to use them.

*There could be some more known issues/limitations at the current time that I am forgetting to mention.*

# Credits:

- [CorpNewt](https://github.com/corpnewt) for creating CorpBot, and many of the amazing tools we use and love. Thanks for all the contributions you've made in the community over the years and for all you've taught me and others. 


