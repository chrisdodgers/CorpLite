import asyncio, discord, math, textwrap
from discord.ext import commands
from Cogs import Message


async def setup(bot):
    # Add the bot and deps
    await bot.add_cog(PickList(bot))


class PickList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Removed reaction listeners and related reaction functions.
    # This was done since this is being used solely as a user app. If used in DMs - perm issues would of course occur with using reactions. Now using UI buttons.
    # See Pager class below and PickButtons class.

class Picker:
    def __init__(self, **kwargs):
        self.list = kwargs.get("list", [])
        self.title = kwargs.get("title", None)
        self.timeout = kwargs.get("timeout", 60)
        self.ctx = kwargs.get("ctx", None)
        self.message = kwargs.get("message", None)  # message to edit
        self.self_message = None
        self.max = 10  # Don't set programmatically - as we don't want this overridden

    async def pick(self):
        # This actually brings up the pick list and handles the nonsense
        # Returns a tuple of (return_code, message)
        # The return code is -1 for cancel, -2 for timeout, -3 for error, 0+ is index
        # Let's check our prerequisites first
        if self.ctx is None or not self.list or len(self.list) > self.max:
            return (-3, None)

        msg = (self.title + "\n" if self.title else "") + "```\n"
        for i, item in enumerate(self.list, start=1):
            msg += f"{i}. {item}\n"
        msg += "```"

        # Send or edit the message
        if self.message:
            self.self_message = self.message
            await self.self_message.edit(content=msg, embed=None)
        else:
            if hasattr(self.ctx, "send"):
                self.self_message = await self.ctx.send(msg)
            elif hasattr(self.ctx, "response"):
                if not self.ctx.response.is_done():
                    await self.ctx.response.send_message(msg)
                    self.self_message = await self.ctx.original_response()
                else:
                    self.self_message = await self.ctx.followup.send(msg)


        # UI Button picker that replaces the reaction based picklist reaction
        class PickButtons(discord.ui.View):
            def __init__(self, outer, timeout):
                super().__init__(timeout=timeout)
                self.outer = outer
                self.value = None

                # Add numeric buttons (up to 10)
                for i in range(len(outer.list)):
                    label = str(i + 1)
                    self.add_item(PickButtons.NumButton(label, self))

                # Add cancel button
                self.add_item(PickButtons.CancelButton(self))

            class NumButton(discord.ui.Button):
                def __init__(self, label, view_ref):
                    super().__init__(label=label, style=discord.ButtonStyle.primary)
                    self.view_ref = view_ref

                async def callback(self, interaction: discord.Interaction):
                    # Only allow the invoking user
                    if interaction.user != self.view_ref.outer.ctx.user:
                        return await interaction.response.send_message(
                            "This selection isn’t for you.", ephemeral=True
                        )
                    self.view_ref.value = int(self.label) - 1
                    for child in self.view_ref.children:
                        child.disabled = True
                    await interaction.response.edit_message(view=self.view_ref)
                    self.view_ref.stop()

            class CancelButton(discord.ui.Button):
                def __init__(self, view_ref):
                    super().__init__(emoji="🛑", style=discord.ButtonStyle.danger)
                    self.view_ref = view_ref

                async def callback(self, interaction: discord.Interaction):
                    if interaction.user != self.view_ref.outer.ctx.user:
                        return await interaction.response.send_message(
                            "This selection isn’t for you.", ephemeral=True
                        )
                    self.view_ref.value = -1
                    for child in self.view_ref.children:
                        child.disabled = True
                    await interaction.response.edit_message(view=self.view_ref)
                    self.view_ref.stop()

        # Attach the pick buttons to the existing message.
        view = PickButtons(self, timeout=self.timeout)
        await self.self_message.edit(view=view)
        await view.wait()

        # Remove buttons once a selection is made
        try:
            await self.self_message.edit(view=None)
        except:
            pass

        # Handle timeout
        if view.value is None:
            try:
                await self.self_message.edit(content=f"{msg}\n*Timed out.*", view=None)
            except:
                pass
            view.stop
            return (-2, self.self_message)
        return (view.value, self.self_message)


class PagePicker(Picker):
    def __init__(self, **kwargs):
        Picker.__init__(self, **kwargs)
        # Expects self.list to contain the fields needed - each a dict with {"name":name,"value":value,"inline":inline}
        self.max = kwargs.get("max", 10 if self.list else 20)  # Used defaults of 10 and 20 respectively
        max_val = 25 if self.list else 2048  # Must be between 1 and 25 for fields, 1 and 2048 for desc rows
        self.max = 1 if self.max < 1 else max_val if self.max > max_val else self.max
        self.max_chars = kwargs.get("max_chars", 2048)
        self.max_chars = 1 if self.max_chars < 1 else 2048 if self.max_chars > 2048 else self.max_chars
        self.url = kwargs.get("url", None)  # The URL the title of the embed will link to
        self.description = kwargs.get("description", None)
        self.image = kwargs.get("image", None)
        self.footer = kwargs.get("footer", None)
        self.thumbnail = kwargs.get("thumbnail", None)
        self.timestamp = kwargs.get("timestamp", None)
        self.author = kwargs.get("author", None)
        self.color = kwargs.get("color", None)
        # Description-based args
        self.newline_split = kwargs.get("newline_split", True)
        self.d_header = kwargs.get("d_header", "")
        self.d_footer = kwargs.get("d_footer", "")

    def _get_desc_page_list(self):
        # Returns the list of pages based on our settings
        # Let's sanitize the description, header, and footer
        d = self.description if isinstance(self.description, str) else ""
        h = self.d_header if isinstance(self.d_header, str) else ""
        f = self.d_footer if isinstance(self.d_footer, str) else ""
        adj_max = self.max_chars - len(h) - len(h)
        if self.newline_split:
            chunks = []
            curr = ""
            row = 0
            for line in d.split("\n"):
                test = curr + "\n" + line if len(curr) else line
                row += 1
                if len(line) > adj_max:  # The line itself is too long
                    if len(curr): chunks.append(h + curr + f)
                    chunks.extend([h + x + f for x in textwrap.wrap(
                        line,
                        adj_max,
                        break_long_words=True
                    )])
                    curr = ""
                elif len(test) >= adj_max or row > self.max:  # Exact or too big - adjust
                    chunks.append(h + (test if len(test) == adj_max else curr) + f)
                    curr = "" if len(test) == adj_max else line
                    row = 0 if len(test) == adj_max else 1
                else:  # Not big enough yet - just append
                    curr = test
            if len(curr): chunks.append(h + curr + f)
            return chunks
        # Use textwrap to wrap the words, not newlines
        return [h + x + f for x in textwrap.wrap(
            d,
            adj_max,
            break_long_words=True,
            replace_whitespace=False
        )]

    def _get_page_contents(self, page_number):
        # Returns the contents of the page passed
        if self.list:
            start = self.max * page_number
            return self.list[start:start + self.max]
        return self._get_desc_page_list()[page_number]

    def _get_footer_text(self, text, page, pages):
        return "[{:,}/{:,}] - {}".format(page + 1, pages, text) if text else "Page {:,} of {:,}".format(page + 1, pages)

    def _get_footer(self, page, pages):
        if pages <= 1:
            return self.footer
        if isinstance(self.footer, dict):
            # Shallow copy so we don't override the original values
            new_footer = {}
            for key in self.footer:
                new_footer[key] = self.footer[key]
            # Update the text
            new_footer["text"] = self._get_footer_text(
                self.footer.get("text", ""),
                page,
                pages
            )
            return new_footer
        return self._get_footer_text(self.footer, page, pages)

    async def pick(self):
        # This brings up the page picker and handles the events
        # It will return a tuple of (last_page_seen, message)
        # The return code is -1 for cancel, -2 for timeout, -3 for error, 0+ is index
        # Let's check our prerequisites first
        if self.ctx == None or (not self.list and not self.description):
            return (-3, None)
        page = 0  # Set the initial page index
        if self.list:
            pages = int(math.ceil(len(self.list) / self.max))
        else:
            pages = len(self._get_desc_page_list())
        embed_class = Message.Embed if self.list else Message.EmbedText
        # Let's ensure our description, header, and footer are setup properly
        desc = None if not isinstance(self.description, str) or self.description == "" else self.description
        if desc is not None:  # Check if we have a description - then attempt to append our header + footer
            desc = (self.d_header if isinstance(self.d_header, str) else "") + desc + (
                self.d_footer if isinstance(self.d_footer, str) else "")
        # Setup the embed
        embed = {
            "title": self.title,
            "url": self.url,
            "description": desc if self.list else self._get_page_contents(page),
            "image": self.image,
            "footer": self._get_footer(page, pages),
            "thumbnail": self.thumbnail,
            "timestamp": self.timestamp,
            "author": self.author,
            "color": self.color or getattr(self.ctx, "author", getattr(self.ctx, "user", None)),
            "pm_after_fields": -1,  # Disable pm_after entirely
            "fields": self._get_page_contents(page) if self.list else None
        }
        # Check if an embed already exist. If so - edit it. If not then create it.
        if self.message:
            self.self_message = self.message
            await embed_class(**embed).edit(self.ctx, self.self_message)
        else:
            self.self_message = await embed_class(**embed).send(self.ctx)


        # The point of this is since this is bot is now being used as a user app within private DMs for example. Buttons are needed instead of reactions due to perm issues.
        # New UI button view that replaces the old reaction nav
        class Pager(discord.ui.View):
            def __init__(self, outer, *, timeout=300):
                super().__init__(timeout=timeout)
                self.outer = outer
                self.page = page
                self.pages = pages

            async def refresh(self, interaction: discord.Interaction):
                #Acknowledge the interaction so Discord doesn't show "This interaction failed"
                if not interaction.response.is_done():
                    await interaction.response.defer()

                # Rebuild and edit the existing embed message
                embed["fields" if self.outer.list else "description"] = self.outer._get_page_contents(self.page)
                embed["footer"] = self.outer._get_footer(self.page, self.pages)
                await Message.Embed(**embed).edit(self.outer.ctx, self.outer.self_message)

            @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.secondary)
            async def first(self, interaction, button):
                self.page = 0
                await self.refresh(interaction)

            @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary)
            async def prev(self, interaction, button):
                self.page = max(self.page - 1, 0)
                await self.refresh(interaction)

            @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary)
            async def next(self, interaction, button):
                self.page = min(self.page + 1, self.pages - 1)
                await self.refresh(interaction)

            @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary)
            async def last(self, interaction, button):
                self.page = self.pages - 1
                await self.refresh(interaction)

            async def on_timeout(self):
                # When timeout hits - remove all the buttons.
                try:
                    await self.outer.self_message.edit(view=None)
                except:
                    pass
                super().stop()

            @discord.ui.button(emoji="🛑", style=discord.ButtonStyle.danger)
            async def stop(self, interaction, button):
                for child in self.children:
                    child.disabled = True
                await interaction.response.edit_message(view=None)
                super().stop()

        # Attach the navigation view to the message if there is more than 1 page.
        if pages > 1:
            view = Pager(self, timeout=self.timeout)
            await self.self_message.edit(view=view)

            # Wait for buttons and return
            await view.wait()
            return (view.page, self.self_message)
