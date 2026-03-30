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

*Once added, you will see CorpLite available in your Discord App Directory. You will also see it if you type `/` anywhere within Discord and click/tap the Corp logo to see all the available commands. Additionally, you can use `/help` to also see all the available cogs/commands with their use descriptions.* 


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
Bot
└─ Bot
Calc
└─ Calc
Clippy
└─ Clippy
CogManager
└─ CogManager
Comic
└─ Comic
Encode
└─ Encode
Help
└─ Help
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
Settings
└─ Settings
Utils
└─ Utils
Weather
└─ Weather
Cogless
└─ ProgressBar
└─ GetImage
└─ Nullify
└─ FuzzySearch
└─ ReadableTime
└─ DL
└─ Message
```
[Bot](#bot), [Calc](#calc), [Clippy](#clippy), [CogManager](#cogmanager), [Comic](#comic), [Encode](#encode), [Help](#help), [Humor](#humor), [IntelArk](#intelark), [Jpeg](#jpeg), [OpenCore](#opencore), [PciUsb](#pciusb), [Settings](#settings), [Weather](#weather)

## Bot
####	Bot Cog (5 commands) - Bot.py Extension:
    /hostinfo
      └─ List info about the bot's host environment.
    /ping
      └─ Feeling lonely?
    /presence <playing_type> <content> <url>
      └─ Changes the bot's presence (owner-only).
    /reboot <install_or_update>
      └─ Reboots the bot (owner only).
    /uptime
      └─ Lists the bot's uptime.

## Calc
####	Calc Cog (1 command) - Calc.py Extension:
    /calc <formula>
      └─ Do some math.

## Clippy
####	Clippy Cog (1 command) - Clippy.py Extension:
    /clippy <text>
      └─ You should run this command. Can I help?

## CogManager
####	CogManager Cog (3 commands) - CogManager.py Extension:
    /extensions <extension>
      └─ Outputs the cogs and command count
    /imports <extension>
      └─ Outputs the extensions imported by the passed extension.
    /reload <extension>
      └─ Reloads the passed extension (owner only).

## Comic
####	Comic Cog (8 commands) - Comic.py Extension:
    /dilbert <date>
      └─ Get a Dilbert comic.
    /garfield <date>
      └─ Get a Garfield comic.
    /gmg <date>
      └─ Get a Garfield Minus Garfield comic.
    /peanuts <date>
      └─ Get a Peanuts comic.
    /randgarfield
      └─ Get a random Garfield comic.
    /randgmg
      └─ Get a random Garfield Minus Garfield comic.
    /randilbert
      └─ Get a random Dilbert comic.
    /randpeanuts
      └─ Get a random Peanuts comic.

## Encode
####	Encode Cog (3 commands) - Encode.py Extension:
    /encode <from_type> <to_type> <value>
      └─ Data converter that supports hex, decimal, binary, base64, and ascii.
    /hexswap <input_hex>
      └─ Enter a hex value to byte swap.
    /mem <input>
      └─ Convert between MiB and little-endian hex.

## Help
####	Help Cog (3 commands) - Help.py Extension:
    /dumphelp <cog_or_command>
      └─ Dumps and uploads a timestamped, formatted list of commands and descriptions.
    /dumpmarkdown <cog_or_command>
      └─ Dumps and uploads a timestamped, markdown-formatted list of commands and desc...
    /help <command>
      └─ Get Help

## Humor
####	Humor Cog (9 commands) - Humor.py Extension:
    /fart
      └─ Let some air out! Maybe on someone.
    /french
      └─ Excuse my French.
    /fry <image>
      └─ Fry an image to a crisp.
    /german
      └─ I think this is German.
    /meme <template_id> <text_1> <text_2>
      └─ Time for some memes.
    /memetemps <search_term>
      └─ Grab a meme template.
    /poke <user> <image>
      └─ C'mon, do something...
    /slap <user>
      └─ What did the 5 fingers say to the face?
    /zalgo <message>
      └─ Send a funny looking message.

## IntelArk
####	IntelArk Cog (1 command) - IntelArk.py Extension:
    /iark <cpu_model>
      └─ Get Intel CPU/iGPU info

## Jpeg
####	Jpeg Cog (1 command) - Jpeg.py Extension:
    /jpeg <image>
      └─ Do I look like I know what a JPEG is?

## OpenCore
####	OpenCore Cog (6 commands) - OpenCore.py Extension:
    /alc <search_term>
      └─ Search a codec name or device-id to get layouts for AppleALC
    /listcodecs <search_term>
      └─ Lists the codecs in the AppleALCCodecs.plist
    /occ <search_path>
      └─ Search OC Configuration.tex
    /plist <file>
      └─ Validates .plist file structure
    /slide <input_hex>
      └─ Calculates your slide boot-arg based on an input address (in hex).
    /weg <search_term>
      └─ Searches WhateverGreen IntelHD FAQ for device-id and connector info

## PciUsb
####	PciUsb Cog (2 commands) - PciUsb.py Extension:
    /pci <ven_dev>
      └─ Searches pci-ids.ucw.cz for the passed PCI ven:dev id.
    /usb <ven_dev>
      └─ Searches usb-ids.gowdy.us for the passed USB ven:dev id.

## Settings
####	Settings Cog (6 commands) - Settings.py Extension:
    /addowner <member>
      └─ Adds an owner to the owner list (owner only).
    /claim
      └─ Become a God!... Or something like that.
    /disown
      └─ Revokes all ownership of the bot (owner only).
    /flush
      └─ Flush the bot settings to disk (owner only).
    /owners
      └─ Lists the bot's current owners.
    /remowner <member>
      └─ Removes an owner from the owner list (owner only).

## Weather
####	Weather Cog (2 commands) - Weather.py Extension:
    /forecast <city_name>
      └─ Gets some weather, for 5 days or whatever.
    /weather <city_name>
      └─ Get some weather

# Known Issues/Random Notes:

- Using **/randgarfield** *(or any of the other random comic commands)* within private DMs may fail to embed. Sometimes it works, sometimes it doesn't. This also applies to **/meme** from my testing. Its a 50/50 if it embeds right within DMs.
- As of this writing, *any* of the Garfield commands no longer work.
- *"I can't reply or reference a URL from a message containing a file in use with /slide or /plist."*: This currently is a limitation that will most likely not be solved relating to DMs. The current workaround is *only* handling direct uploaded attachments and temporarily removing the handling for message URLs.
- *"Some comics are missing that were available in CorpBots Comic.py!"*: Due to keeping limits in mind of the max amount of slash commands that can be registered *(and trying to keep the bot a bit cleaner)*, I have commented out some comics that seemingly rarely or never get used. The code has been updated for said comics, but they just need to be uncommented if you intend to use them.
- *"I'm hosting CorpLite and its presence appears offline"*: This one is a fun instance of Discord being Discord. If your app has 0 guild installs and only user installs - this will happen. Solution: add CorpLite to at least one guild, even if just a "dummy" guild. Also with this said, `/status` will not be coming to CorpLite. Regardless of setting this, it will always show up as `online` if the app contains a single user install. Again, Discord problem and not a me problem.

*There could be some more known issues/limitations at the current time that I am forgetting to mention.*

# Credits:

- [CorpNewt](https://github.com/corpnewt) for creating CorpBot, and many of the amazing tools we use and love. Thanks for all the contributions you've made in the community over the years and for all you've taught me and others. 


