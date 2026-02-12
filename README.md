# CorpLite (Beta)
A forked, light version of [CorpBot.py](https://github.com/corpnewt/CorpBot.py) that is intended to be used as a Discord user app with slash commands. Full credits to [CorpNewt](https://github.com/corpnewt) for making CorpBot and the many other tools we use and love.

## What the fork is this?
The idea behind this fork is I thought to myself, *"hmmm, wouldn't it be kind of neat to use a few functions of CorpBot within private DMs and also in public servers that don't have CorpBot?"*. Well, that is what CorpLite does. 

- Currently, CorpLite has a *few* cogs that have been updated to use slash commands and Discord Interactions.
- CorpLite works within private DMs, and also servers that allow the use of external apps. 

>![NOTE]
> CorpLite is intended to be light, as the name suggests. This is NOT a "replacement" of CorpBot, nor will never be that. Its sole intentions is to be used as a user app which you can use a few functions from CorpBot in areas where CorpBot might not be available.
> 
> - Some cogs I'd like to eventually add are currently missing and it is in the roadwork plans for a future update. Example: Utils, DisplayName, Settings, Humor, Music, etc.
> - Being solely a user app introduces new limitations related to permissions/intents. Once again, some cogs and/or functions will *never* be coming to CorpLite outside of just the intention of being light. 
> - This is still very much a beta. There are some known limits and items that need to be addressed in the future. However, CorpLite in its current state is pretty usable and useful. Future updates will be made.
> 


## Don't want nor care to host your own instance?
### [Click here to add CorpLite as a Discord User App.](https://discord.com/oauth2/authorize?client_id=1430625110947004506)

*Once added, you will see CorpLite available in your Discord App Directory. You will also see it if you type `/` anywhere and click/tap the Corp logo to see all available commands. Use `/help` to also see all available commands and descriptions of each commands use.* 


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



# Credits:

- [CorpNewt](https://github.com/corpnewt) for creating CorpBot, and many of the amazing tools we use and love. Thanks for all the contributions you've made in the community over the years and for all you've taught me and others. 


