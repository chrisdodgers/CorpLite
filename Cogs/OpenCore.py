import discord, asyncio, re, io, os, datetime, plistlib, difflib, json, time, tempfile, shutil, math
from discord import app_commands
from discord.ext import commands
from Cogs import DL, PickList, Message, FuzzySearch

try:
    from . import OCD
except ImportError:
    OCD = None


async def setup(bot):
    # Add the bot and deps
    # Removed settings since its not being used with CorpLite at the current moment.
    await bot.add_cog(OpenCore(bot))


class OpenCore(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.sample = None
        self.sample_paths = []
        self.tex = None
        self.tex_version = "?.?.?"
        self.is_current = False  # Used for stopping loops
        self.wait_time = 21600  # Default of 6 hours (21600 seconds)
        self.alc_codecs = None
        self.alc_wait_time = 86400  # Default of 24 hours (86400 seconds)
        self.fbs = None
        self.fb_wait_time = 86400  # Default of 24 hours (86400 seconds)
        self.alc_alternate = {
            # Alternate codec names pulled from: https://github.com/acidanthera/AppleALC/wiki/Supported-codecs
            "ALC225": ["ALC3253"],
            "ALC233": ["ALC3236"],
            "ALC255": ["ALC3234"],
            "ALC256": ["ALC3246"],
            "ALC269": ["ALC271X"],
            "ALC282": ["ALC3227"],
            "ALC290": ["ALC3241"],
            "ALC292": ["ALC3226", "ALC3232"],
            "ALC298": ["ALC3268"],
            "ALC888": ["ALC1200"],
            "ALC891": ["ALC867"],
            "ALC898": ["ALC899"],
            "CX20751_2": ["CX20751", "CX20752"],
            "CX20753_4": ["CX20753", "CX20754"],
            "IDT92HD66C3_65": ["IDT92HD66C3/65"],
            "IDT92HD87B1_3": ["IDT92HD87B1/3"],
            "IDT92HD87B2_4": ["IDT92HD87B2/4"],
            "VT2020_2021": ["VT2020", "VT2021"]
        }
        self.message_regex = re.compile(
            r"(?i)https:\/\/(www\.)?(\w+\.)*discord(app)?\.com\/channels\/(@me|\d+)\/\d+\/\d+")
        self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
        self.nv_link = "https://gfe.nvidia.com/mac-update"
        # removed Utils since its not currently being used with CorpLite

    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")

    @commands.Cog.listener()
    async def on_unloaded_extension(self, ext):
        # Called to shut things down
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        self.is_current = False

    @commands.Cog.listener()
    async def on_loaded_extension(self, ext):
        # See if we were loaded
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        self.is_current = True
        # Load the local files first
        self._load_local()
        self._load_local_sample()
        self._load_local_alc()
        self._load_local_fb()
        # Start the update loops
        self.bot.loop.create_task(self.update_tex())
        self.bot.loop.create_task(self.update_alc())
        self.bot.loop.create_task(self.update_fb())

    async def update_tex(self):
        print("Starting Configuration.tex|Sample.plist update loop - repeats every {:,} second{}...".format(
            self.wait_time, "" if self.wait_time == 1 else "s"))
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if not self.is_current:
                # Bail if we're not the current instance
                return
            t = time.time()
            print("Updating Configuration.tex|Sample.plist: {}".format(datetime.datetime.now().time().isoformat()))
            if not await self._dl_tex():
                print("Could not download Configuration.tex!")
                if self._load_local():
                    print(" - Falling back on local copy!")
            if not await self._dl_sample():
                print("Could not download Sample.plist!")
                if self._load_local_sample():
                    print(" - Falling back on local copy!")
            print("Configuration.tex|Sample.plist - took {:,} seconds.".format(time.time() - t))
            await asyncio.sleep(self.wait_time)

    async def update_alc(self):
        print("Starting AppleALC codec loop - repeats every {:,} second{}...".format(self.alc_wait_time,
                                                                                     "" if self.alc_wait_time == 1 else "s"))
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if not self.is_current:
                # Bail if we're not the current instance
                return
            t = time.time()
            print("Updating AppleALCCodecs.plist: {}".format(datetime.datetime.now().time().isoformat()))
            if not await self._dl_alc():
                print("Could not download AppleALCCodecs.plist!")
                if self._load_local_alc():
                    print(" - Falling back on local copy!")
            print("AppleALCCodecs - took {:,} seconds.".format(time.time() - t))
            await asyncio.sleep(self.alc_wait_time)

    async def update_fb(self):
        print("Starting WhateverGreen framebuffer loop - repeats every {:,} second{}...".format(
            self.fb_wait_time,
            "" if self.fb_wait_time == 1 else "s"
        ))
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if not self.is_current:
                # Bail if we're not the current instance
                return
            t = time.time()
            print("Updating WhateverGreenFBs.plist: {}".format(datetime.datetime.now().time().isoformat()))
            if not await self._dl_fb():
                print("Could not download WhateverGreenFBs.plist!")
                if self._load_local_fb():
                    print(" - Falling back on local copy!")
            print("WhateverGreenFBs - took {:,} seconds.".format(time.time() - t))
            await asyncio.sleep(self.alc_wait_time)

    def _load_local(self):
        if not os.path.exists("Configuration.tex"): return False
        # Try to load it
        try:
            with open("Configuration.tex", "r") as f:
                self.tex = f.read()
        except:
            return False
        # Retain the version
        try:
            self.tex_version = self.tex.split("Reference Manual (")[1].split(")")[0]
        except:
            self.tex_version = "?.?.?"
        return True

    def _load_local_sample(self):
        if not os.path.exists("Sample.plist"): return False
        # Try to load it
        try:
            with open("Sample.plist", "rb") as f:
                self.sample = plistlib.load(f)
            # Gather all paths
            self.sample_paths = self._parse_sample()
        except:
            return False
        return True

    def _load_local_alc(self):
        if not os.path.exists("AppleALCCodecs.plist"): return False
        # Try to load it
        try:
            with open("AppleALCCodecs.plist", "rb") as f:
                self.alc_codecs = plistlib.load(f)
        except:
            return False
        return True

    def _load_local_fb(self):
        if not os.path.exists("WhateverGreenFBs.plist"): return False
        # Try to load it
        try:
            with open("WhateverGreenFBs.plist", "rb") as f:
                self.fbs = plistlib.load(f)
        except:
            return False
        return True

    async def _dl_tex(self):
        try:
            self.tex = await DL.async_text(
                "https://github.com/acidanthera/OpenCorePkg/raw/master/Docs/Configuration.tex")
            assert self.tex
        except:
            return False
        # Save to a local file
        with open("Configuration.tex", "w") as f:
            f.write(self.tex)
        # Retain the version
        try:
            self.tex_version = self.tex.split("Reference Manual (")[1].split(")")[0]
        except:
            self.tex_version = "?.?.?"
        return True

    async def _dl_sample(self):
        try:
            self.sample = plistlib.loads(
                await DL.async_dl("https://github.com/acidanthera/OpenCorePkg/raw/master/Docs/SampleCustom.plist"))
            assert self.sample
        except:
            return False
        # Save to a local file
        plistlib.dump(self.sample, open("Sample.plist", "wb"))
        # Gather all paths
        self.sample_paths = self._parse_sample()
        return True

    async def _dl_alc(self):
        try:
            resources = await DL.async_text("https://github.com/acidanthera/AppleALC/tree/master/Resources")
            assert resources
            # Attempt to extract the JSON data within
            try:
                resources = \
                resources.split('<script type="application/json" data-target="react-app.embeddedData">')[1].split(
                    "</script>")[0]
            except:
                pass
            payload_json = json.loads(resources)
            codec_list = [x["name"] for x in payload_json["payload"]["tree"]["items"] if
                          x["contentType"] == "directory" and not "/" in x["name"]]
            codecs = {}
            for codec in codec_list:
                codec_url = "https://raw.githubusercontent.com/acidanthera/AppleALC/master/Resources/{}/Info.plist".format(
                    codec)
                codec_plist = plistlib.loads(await DL.async_dl(codec_url))
                codecs[codec] = {
                    "CodecID": codec_plist["CodecID"],
                    "Layouts": [int(x["Id"]) for x in codec_plist["Files"]["Layouts"]],
                    "Vendor": codec_plist["Vendor"]
                }
                if "Revisions" in codec_plist:
                    codecs[codec]["Revisions"] = ["0x" + hex(int(x))[2:].upper() for x in codec_plist["Revisions"]]
        except:
            return False
        plistlib.dump(codecs, open("AppleALCCodecs.plist", "wb"))
        self.alc_codecs = codecs
        return True

    async def _dl_fb(self):
        try:
            weg_faq_html = await DL.async_text(
                "https://github.com/acidanthera/WhateverGreen/raw/master/Manual/FAQ.IntelHD.en.md")
            # We need to walk the markdown and look for some landmarks for organizing elements
            # Generation headers use a prefix of ##, then the graphics name, then ([codename](link) processors)
            framebuffer_dict = {}
            current_gen = current_url = current_gpu = None
            connector_string = ""
            dev_id_primed = connector_primed = False
            for line in weg_faq_html.split("\n"):
                line = line.strip()
                if line.startswith("## ") and line.endswith("processors)"):
                    current_gpu = line.split("## ")[1].split("([")[0].strip()
                    current_gen = "[" + "([".join(line.split("([")[1:])[:-1].replace(" processors", "")
                    framebuffer_dict[current_gen] = {}
                    framebuffer_dict[current_gen]["model"] = current_gpu
                    # Reset any primed values
                    dev_id_primed = connector_primed = False
                    continue
                if current_gen is not None and line.startswith("***Native supported DevID"):
                    # Got to the device id list - prime it
                    dev_id_primed = True
                    connector_primed = False
                    continue
                if current_gen is not None and line.endswith("connectors</summary>"):
                    # Got to the connectors list - prime it
                    connector_primed = True
                    dev_id_primed = False
                    continue
                if dev_id_primed:
                    # We got a potential device-id
                    if not line or not line.startswith("- `0x") or not line.endswith("`"):
                        continue  # Not valid
                    dev_id = line.split("`")[1]
                    if len(dev_id) > 6:
                        continue  # Too long - maybe it was a connector instead?
                    # Should have a device-id here - save it in a few formats
                    device_ids = framebuffer_dict[current_gen].get("device-ids", {})
                    dev_id = dev_id[2:].upper()  # Normalize case
                    device_ids[dev_id] = [
                        "0000" + dev_id,  # 32-bit big endian format
                        dev_id[2:] + dev_id[:2] + "0000",  # 32-bit little endian format
                    ]
                    framebuffer_dict[current_gen]["device-ids"] = device_ids
                    continue
                if connector_primed:
                    # Looking for connector data
                    if not line:
                        # Empty - if we have connector data, add it
                        if connector_string:
                            connectors = framebuffer_dict[current_gen].get("connectors", {})
                            # Gather all entries that are hex-only
                            id_string = connector_string.split("ID: ")[1].split(", ")[0]
                            connector_id_list = list(re.finditer(
                                r"(?i)\b(0x)?([\da-f]+)\b",
                                id_string
                            ))
                            for connector_match in connector_id_list:
                                # Extract the full match sans 0x prefix
                                connector_id = connector_match.group(2).upper()
                                # Ensure our id is padded to 32-bits
                                if len(connector_id) < 8:
                                    connector_id = connector_id.rjust(8, "0")
                                connectors[connector_id] = [
                                    connector_id,  # 32-bit big endian
                                    "{}{}{}{}".format(
                                        connector_id[6:],
                                        connector_id[4:6],
                                        connector_id[2:4],
                                        connector_id[:2]
                                    ),  # 32-bit little endian
                                    connector_string
                                ]
                                framebuffer_dict[current_gen]["connectors"] = connectors
                            connector_string = ""
                        continue
                    if line.endswith("kext`"):
                        # Got the framebuffer kext we're looking for
                        framebuffer_dict[current_gen]["kext"] = line.split("`")[1]
                        continue
                    if not connector_string and not line.startswith("ID: "):
                        continue  # Not a valid starter
                    # Gather lines until we hit an empty one
                    if not connector_string:
                        connector_string = line
                    else:
                        connector_string += "\n" + line
        except:
            return False
        plistlib.dump(framebuffer_dict, open("WhateverGreenFBs.plist", "wb"))
        self.fbs = framebuffer_dict
        return True

    def _parse_sample(self):
        # Helper function to get a list of all paths within the Sample.plist
        if not self.sample: return []  # Nothing to parse
        return self._sample_walk(self.sample, [])

    def _sample_walk(self, current_dict, parent_path):
        paths = []
        for key in current_dict:
            if " " in key or key.startswith("#"): continue  # Skip comments
            key_path = parent_path + [key]
            paths.append(key_path)
            if isinstance(current_dict[key], dict):
                paths.extend(self._sample_walk(current_dict[key], key_path))
            elif isinstance(current_dict[key], list) and len(current_dict[key]) and isinstance(current_dict[key][0],
                                                                                               dict):
                # Append a "*" to imply it's an array
                key_path.append("*")
                paths.extend(self._sample_walk(current_dict[key][0], key_path))
        return paths

    def _device_id(self, device_int):
        dev_id = hex(device_int)[2:].upper()
        if len(dev_id) % 2:  # Ensure it's an even number of chars
            dev_id = "0" + dev_id
        return "0x{} ({})".format(dev_id, device_int)

    def _get_codec_info(self, codec_name):
        m = {}
        matched = next((x for x in self.alc_codecs if x.lower() == codec_name.lower()), None)
        if not matched:  # Check alternate names
            matched = next((x for x in self.alc_alternate if codec_name.lower() in self.alc_alternate[x]), None)
        if matched:  # Got a match - build our dict
            m["name"] = matched
            m["vendor"] = self.alc_codecs[matched]["Vendor"]
            m["device_id"] = self._device_id(self.alc_codecs[matched]["CodecID"])
            m["layouts"] = ", ".join([str(x) for x in sorted(self.alc_codecs[matched]["Layouts"])])
            m["revisions"] = ", ".join(self.alc_codecs[matched].get("Revisions", []))
            m["alternate"] = ", ".join(self.alc_alternate.get(matched, []))
        return m

    def get_os(self, build_number):
        # Returns the best-guess OS version for the build number
        alpha = "abcdefghijklmnopqrstuvwxyz"
        os_version = "Unknown"
        major = minor = ""
        try:
            # Formula looks like this:  AAB; AA - 4 = 10.## version
            # B index in "ABCDEFGHIJKLMNOPQRSTUVXYZ" = 10.##.## version
            split = re.findall(r"[^\W\d_]+|\d+", build_number)
            major = int(split[0]) - 4
            minor = alpha.index(split[1].lower())
            os_version = "10.{}.{}".format(major, minor)
        except:
            pass
        return os_version

    def get_value(self, build_number):
        alpha = "abcdefghijklmnopqrstuvwxyz"
        # Split them up
        split = re.findall(r"[^\W\d_]+|\d+", build_number)
        start = split[0].rjust(4, "0")
        alph = split[1]
        end = split[2].rjust(6, "0")
        alpha_num = str(alpha.index(alph.lower())).rjust(2, "0")
        return int(start + alpha_num + end)


    async def download(self, url):
        url = url.strip("<>")
        # Set up a temp directory
        dirpath = tempfile.mkdtemp()
        tempFileName = url.rsplit('/', 1)[-1]
        # Strip question mark
        tempFileName = tempFileName.split('?')[0]
        filePath = dirpath + "/" + tempFileName
        rImage = None
        try:
            rImage = await DL.async_dl(url)
        except:
            pass
        if not rImage:
            self.remove(dirpath)
            return None
        with open(filePath, 'wb') as f:
            f.write(rImage)
        # Check if the file exists
        if not os.path.exists(filePath):
            self.remove(dirpath)
            return None
        return filePath

    def remove(self, path):
        if not path is None and os.path.exists(path):
            shutil.rmtree(os.path.dirname(path), ignore_errors=True)

    def get_slide(self, start_addr=0):
        slide = int(math.ceil((start_addr - 0x100000) / 0x200000))
        return max(0, slide)

    def get_available(self, line_list=[]):
        available = []
        for line in line_list:
            line_split = [x for x in line.split(" ") if len(x)]
            if not len(line_split):
                continue
            if len(line_split) == 1:
                # No spaces - let's make sure it's hex and add it
                try:
                    available.append({"start": int(line_split[0], 16)})
                except:
                    continue
            elif line_split[0].lower() == "available":
                # If our first item is "available", let's convert the others into ints
                new_line = []
                for x in line_split:
                    new_line.extend(x.split("-"))
                if len(new_line) < 3:
                    # Not enough info
                    continue
                try:
                    num_bytes = (int(new_line[2], 16) - int(new_line[1], 16)) if len(new_line) < 4 else int(new_line[3],
                                                                                                            16) * 4096
                    num_mb = round(num_bytes / 1024 ** 2, 2)
                    available.append({
                        "start": int(new_line[1], 16),
                        "end": int(new_line[2], 16),
                        "size": num_bytes,
                        "mb": "{} MB @ ".format(num_mb)
                    })
                except:
                    continue
        return available


    ### Search method for the Sample.plist pathing ###

    def search_sample(self, search_list):
        if not self.sample_paths: return None  # Nothing to search, bail
        ratio_min = 0.65
        # Let's try to build a list of close matches based on sequence matching the latter elements
        # of the parts lists
        match_list = []
        for i, path in enumerate(self.sample_paths):
            # Strip "*" from the path for matching
            path = [x for x in path if x != "*"]
            if len(path) < len(search_list): continue  # Not going to match, our search is longer
            # Get a fuzzy match ratio for each component counting back from the end
            check_ratios = [
                difflib.SequenceMatcher(None, search_list[j].lower(), x.lower()).quick_ratio() for j, x in
                enumerate(path[-len(search_list):])
            ]
            # Make sure we have a worthwhile ratio
            if any((x < ratio_min for x in check_ratios)): continue  # Skip any individually low ratios
            # Get the average of all of those matches
            avg_ratio = sum(check_ratios) / len(check_ratios)
            if avg_ratio < ratio_min: continue  # Not close enough
            match_list.append((i, avg_ratio))
        if not match_list: return None  # No match was close
        match_list = sorted(match_list, key=lambda x: x[1], reverse=True)
        exact_list = [x for x in match_list if x[1] == 1]
        # Strip any right-trailing
        cleaned_list = []
        for match in exact_list or match_list:
            p = self.sample_paths[match[0]]
            while len(p) and p[-1] == "*":
                p = p[:-1]
            if p: cleaned_list.append(p)
        return (not exact_list, cleaned_list)

    ### Helper methods adjusted from rusty_bits' config_tex_info.py from ProperTree's repo to search the Configuration.tex ###

    def tex_search(self, config_file, search_list, width=80, valid_only=False, show_urls=False):
        result = self.parse_configuration_tex(self.tex, search_list, width, valid_only, show_urls)
        if not result:
            return None

        # First we strip out any backticks to avoid accidental markdown
        result = result.replace("`", "'")
        # Translate '' into double quotes "
        result = result.replace("''", '"')

        style = "normal"
        in_escape = False
        esc_code = ""
        fixed_string = ""
        out = ""

        def dump_out(output, style):
            if not output: return output
            # Helper to bridge styles to markdown
            style_parser = {
                "bold": ("**", "**"),
                "bold_mono": ("`", "`"),
                "normal": ("", ""),
                "mono": ("`", "`"),
                "underline": ("__", "__"),
                "reverse": ("", ""),
                "url": ("", ""),
                "italic": ("*", "*")
            }
            header, footer = style_parser.get(style, ("", ""))
            return header + output + footer

        for c in result:
            # quick hack to decode the escape seqs ret from the parse
            # only including encodings needed for Configuration.tex and a
            # few others for now
            if in_escape:
                esc_code += c
                if c == "m":  # end of esc code
                    # should be using these to turn font attributes on and off
                    # but for now just have a style defined for current needs
                    if esc_code == '[0m':
                        style = "normal"
                    if esc_code == "[10m":  # switch to default family
                        style = "normal"
                    if esc_code == '[1m':  # bold on
                        if style == "mono":
                            style = "bold_mono"  # until a better method is found
                        else:
                            style = "bold"
                    if esc_code == "[22m":  # bold off
                        if style == "bold_mono":
                            style = "mono"
                        else:
                            style = "normal"
                    if esc_code == '[3m':  # italic on
                        style = "italic"
                    # [23m italic off
                    if esc_code == "[4m":  # underline on
                        style = "underline"
                    # [24m underline off
                    if esc_code == '[11m':  # switch to mono family
                        style = "mono"
                    if esc_code == '[7m':  # reverse on
                        style = "reverse"
                    # [27m not reverse
                    if esc_code == '[34m':  # foreground blue
                        if show_urls:
                            style = "url"
                        else:
                            style = "mono"
                    out = ""  # found valid esc - clear out
                    esc_code = ""
                    in_escape = False
                continue
            if c == '\x1b':
                # found end of one esc and start of another
                # dump formatted output to window
                # and start over
                fixed_string += dump_out(out, style)
                out = ""
                in_escape = True
                continue
            # Check for a newline and dump the output
            if c == "\n":
                fixed_string += dump_out(out, style)
                out = ""
            out += c
        if out:
            fixed_string += dump_out(out, style)
        # Strip more than one backtick in a row, or orphaned
        # back ticks surrounded by newlines
        fixed_string = re.sub("`{2,}", "`", fixed_string)
        fixed_string = re.sub("\\n`\\n", "", fixed_string)
        # Replace triple hyphens with an em dash
        fixed_string = fixed_string.replace("---", "—")
        # Return the built string
        return fixed_string

    def parse_configuration_tex(self, config_file, search_list, width, valid_only, show_urls):
        # valid_only: True - return only the valid config.plist options for the search term &
        # return an empty list if no valid options found
        #     False: return whole text of section
        #
        # show_urls: True - return full url of links in the text
        #     False - return only link text with no url
        config = io.StringIO(self.tex)

        result = []
        search_len = len(search_list)
        if search_len == 0:  # we shouldn't get here, but just in case
            return result

        search_terms = ["\\section{"]
        search_terms[0] += search_list[0]
        text_search = search_list[search_len - 1]  # ultimately looking for last item

        # set the search terms based on selected position
        if search_len == 1:
            # we're done
            pass
        elif search_len == 2:
            search_terms.append("\\subsection{Properties")
            search_terms.append("texttt{" + text_search + "}\\")
        elif search_len == 3:
            if search_list[0] == "NVRAM":  # look for value in Introduction
                search_terms.append("\\subsection{Introduction")
                search_terms.append("texttt{" + text_search + "}")
            else:
                search_terms.append(
                    "\\subsection{" + search_list[1] + " Properties")
                search_terms.append("texttt{" + text_search + "}\\")
        elif search_len == 4:
            item_zero = search_list[0]
            sub_search = "\\subsection{"
            if item_zero == "NVRAM":  # look for UUID:term in Introduction
                sub_search = "\\subsection{Introduction"
                text_search = search_list[2]
                text_search += ":"
                text_search += search_list[3]
                text_search += "}"
            elif item_zero == "DeviceProperties":  # look in Common
                sub_search += "Common"
                text_search += "}"
            elif item_zero == "Misc":  # Entry Properties or subsub
                if len(search_list[2]) < 3:
                    sub_search += "Entry Properties"
                else:
                    sub_search = "\\subsubsection{"
                    sub_search += search_list[1]
                text_search += "}"
            else:
                sub_search += search_list[1]
                sub_search += " Properties"
                text_search += "}\\"
            search_terms.append(sub_search)
            search_terms.append("texttt{" + text_search)
        elif search_len == 5:
            sub_search = "\\subsubsection{"
            sub_search += search_list[1]
            search_terms.append(sub_search)
            search_terms.append("texttt{" + text_search)

        # keep a set of prefixes that would break us out of our search
        disallowed = set()
        # move down the Configuration.tex to the section we want
        for i in range(0, len(search_terms)):
            while True:
                line = config.readline()
                if not line:
                    return result
                line = line.strip()
                # Check for disallowed
                if line.startswith(tuple(disallowed)) and (
                        search_terms[0] != "\\section{NVRAM" or not "\\label{nvram" in line):
                    # We've broken out of our current scope - bail
                    return result
                if search_terms[i] in line:
                    # Make sure parent search prefixes get added
                    # to the disallowed set
                    if not search_terms[i].startswith("texttt{"):
                        # Retain the prefix as needed
                        disallowed.add(search_terms[i].split("{")[0] + "{")
                    break

        align = False
        itemize = 0
        not_first_item = False
        in_listing = False
        enum = 0
        columns = 0
        lines_between_valid = 0
        last_line_ended_in_colon = False
        last_line_had_forced_return = False
        last_line_ended_in_return = False
        last_line_was_blank = False

        while True:
            # track document state & preprocess line before parsing
            line = config.readline()
            if not line:
                break
            line = line.strip()
            if line.startswith("%"):  # skip comments
                continue
            if "\\subsection{Introduction}" in line:
                continue
            if "\\begin{tabular}" in line:
                result.append("\x1b[11m")
                for c in line:
                    if c == "c":
                        columns += 1
                continue
            if "\\begin(align*}" in line:
                align = True
                continue
            if "\\end{align*}}" in line:
                align = False
                continue
            if "\\begin{itemize}" in line:
                itemize += 1
                continue
            if "\\begin{enumerate}" in line:
                enum += 1
                continue
            if "\\begin{lstlisting}" in line:
                in_listing = True
                result.append("\n\x1b[11m")
                continue
            if "\\begin{" in line:  # ignore other begins
                continue
            if "\\mbox" in line:
                continue
            if "\\end{tabular}" in line:
                result.append("\x1b[10m")
                columns = 0
                continue
            if "\\end{itemize}" in line:
                itemize -= 1
                if itemize == 0 and enum == 0:
                    not_first_item = False
                continue
            if "\\end{enumerate}" in line:
                enum = 0
                if itemize == 0:
                    not_first_item = False
                continue
            if "\\end{lstlisting}" in line:
                in_listing = False
                result.append("\x1b[10m\n")
                continue
            if "\\end{" in line:  # ignore other ends
                continue
            if "\\item" in line:
                if itemize == 0 and enum == 0:
                    break  # skip line, not itemizing, shouldn't get here
                else:
                    if not_first_item or not last_line_ended_in_return:
                        # newline before this item
                        result.append("\n")
                    not_first_item = True
                    if itemize == 0:  # in enum
                        if search_len == 1:  # first level enumerate, use numeric
                            replace_str = str(enum) + "."
                        else:  # use alpha
                            replace_str = "(" + chr(96 + enum) + ")"
                        line = line.replace("\\item", replace_str)
                        enum += 1
                    elif itemize == 1:  # first level item
                        line = line.replace("\\item", "*")
                    else:
                        line = line.replace("\\item", "-")
                    # fix indenting
                    line = "  " * (itemize - 1) + line
                    if enum != 0:
                        line = "  " + line
            else:
                if itemize > 0 or enum > 0:  # inside multi line item
                    if last_line_had_forced_return:
                        line = "  " * (itemize - 1) + line
                        line = "   " + line  # indent
            if "section{" in line:  # stop when next section is found
                # let's try only checking for "section{" instead of 3 checks
                #        if "\\section{" in line or "\\subsection{" in line or "\\subsubsection{" in line:
                # reached end of current section
                break

            if line.strip() == "":  # blank line, need linefeed, maybe two, maybe none
                if last_line_ended_in_colon:
                    parsed_line = "\n"
                else:
                    if last_line_was_blank:  # skip this blank line
                        continue
                    else:
                        parsed_line = "\n\n"
                last_line_was_blank = True
            else:
                last_line_was_blank = False
                parsed_line = self.parse_line(line, columns, width,
                                              align, valid_only, show_urls)
                if len(parsed_line) == 0:
                    continue
                # post process line
                last_line_had_forced_return = False
                last_line_ended_in_colon = False
                if parsed_line.endswith("\n"):
                    last_line_had_forced_return = True
                elif parsed_line.endswith(":"):
                    parsed_line += "\n"
                    if not_first_item:
                        # treat as forced return instead
                        last_line_had_forced_return = True
                    else:
                        last_line_ended_in_colon = True
                else:
                    parsed_line += " "  # add space for next word

            if parsed_line.endswith("\n"):
                # slightly different use than last_line_had_forced_return
                last_line_ended_in_return = True
            else:
                last_line_ended_in_return = False
            if valid_only:  # we only want to return valid plist options for the field
                if itemize > 0:
                    if "---" in line:
                        if lines_between_valid < 10:
                            result.append(parsed_line)
                else:
                    if len(result) > 0:
                        lines_between_valid += 1
            else:
                result.append(parsed_line)
                if in_listing:
                    result.append("\n")
        # Join the result into a single string and remove
        # leading, trailing, and excessive newlines
        # result = re.sub(r"\n{2,}",r"\n\n","".join(result))
        # return result.strip("\n")

        # leave all excess internal newlines for now for easier debugging
        return "".join(result).strip("\n")

    # return re.sub("\n{2,}", "\n\n", "".join(result)).strip("\n")

    def parse_line(self, line, columns, width, align, valid_only, show_urls):
        ret = ""
        build_key = False
        key = ""
        col_width = 0
        if columns > 0:
            col_width = int(width / (columns + 1))
        ignore = False
        col_contents_len = 0
        line = line.rstrip()
        for c in line:
            if build_key:
                if c in "{[":
                    build_key = False
                    if not valid_only:
                        if key == "text":
                            ret += "\x1b[0m"
                        elif key == "textit":
                            ret += "\x1b[3m"
                        elif key == "textbf":
                            ret += "\x1b[1m"
                        elif key == "emph":
                            ret += "\x1b[3m"
                        elif key == "texttt":
                            ret += "\x1b[11m"
                        elif key == "href":
                            if show_urls:
                                ret += "\x1b[34m"
                            else:
                                ignore = True
                        else:
                            ignore = True
                    if key != "href":
                        key = ""
                elif c in " ,()\\0123456789$&":
                    build_key = False
                    ret += self.special_char(key)
                    col_contents_len += 1
                    if c in ",()0123456789$":
                        ret += c
                    if c == "\\":
                        if len(key) > 0:
                            build_key = True
                    key = ""
                elif c in "_^#":
                    build_key = False
                    ret += c
                    col_contents_len += 1
                    key = ""
                else:
                    key += c
            else:
                if c == "\\":
                    build_key = True
                elif c in "}]":
                    if not ignore:
                        if not valid_only:
                            if columns > 0:
                                ret += "\x1b[22m"
                            else:
                                ret += "\x1b[0m"
                            if key == "href":
                                # ret += " "
                                key = ""
                            elif c == "]":
                                ret += "]"
                    ignore = False
                elif c == "{":
                    if not valid_only:
                        ret += "\x1b[11m"
                elif c == "&":
                    if columns > 0:
                        pad = col_width - col_contents_len - 1
                        if pad > 0:
                            ret += " " * pad
                        col_contents_len = 0
                        ret += "|"
                    else:
                        if not align:
                            ret += "&"
                else:
                    if not ignore:
                        ret += c
                        col_contents_len += 1

        if len(key) > 0:
            ret += self.special_char(key)

        if not valid_only:
            if key == "tightlist":
                ret = ""
            else:
                if key == "hline":
                    ret = "-" * (width - 4)
                    ret += "\n"
            if line.endswith("\\\\"):
                ret += "\n"
        return ret

    def special_char(self, key):
        if key == "kappa":
            return u"\u03f0"
        elif key == "lambda":
            return u"\u03bb"
        elif key == "mu":
            return u"\u03bc"
        elif key == "alpha":
            return u"\u03b1"
        elif key == "beta":
            return u"\u03b2"
        elif key == "gamma":
            return u"\u03b3"
        elif key == "leq":
            return u"\u2264"
        elif key == "cdot":
            return u"\u00b7"
        elif key == "in":
            return u"\u220a"
        elif key == "infty":
            return u"\u221e"
        elif key == "textbackslash":
            return "\\"
        elif key == "hline":
            return u"\u200b"
        else:
            return " "

    # Called for both /alc and /listcodecs. - moved defering the response to be handled in both commands instead of here. See more notes in /alc command.
    async def codec(self, interaction: discord.Interaction, search_term: str):
        """Searches the AppleALCCodecs.plist file in memory for the passed search term.

        Will search for the codec name, the hex device-id if prefixed with 0x, or the integer device-id.

        e.g. $codec ALC662
            $codec 2304
            $codec 0x0900"""

        # usage = "Usage: `{}codec [search_term]`" - dont need this anymore see below. Will probably end up deleting this, and what is commented below later.
        if not self.alc_codecs: return await interaction.followup.send(
            "It looks like I was unable to get the AppleALCCodecs.plist :(")

        # Not used anymore, but left this if search_term came optional.
        # if search_term is None: return await interaction.followup.send(usage)

        # See if it's a hex value first
        if search_term.lower().startswith("0x"):
            # Strip the 0x prefix and then get up to 4 characters
            # for the device-id
            try:
                search_term = int(search_term[2:][-4:], 16)
            except:
                pass
        # If not - check if it's a decimal
        else:
            try:
                search_term = int(search_term)
            except:
                pass
        # Try to walk our codec list and see if we get a name match, a decimal match, or a hex match
        matched = None
        for codec in self.alc_codecs:
            if isinstance(search_term, str) and (
                    search_term.upper() == codec.upper() or search_term.upper() in self.alc_alternate.get(codec, [])):
                matched = codec
                break
            elif self.alc_codecs[codec]["CodecID"] == search_term:
                matched = codec
                break
        if not matched: return await interaction.followup.send("Nothing was found for that search :(")
        m = self._get_codec_info(matched)
        fields = [
            {"name": "Vendor", "value": "`{}`".format(m["vendor"]), "inline": False},
            {"name": "Layout IDs", "value": "`{}`".format(m["layouts"]), "inline": False},
            {"name": "Device ID", "value": "`{}`".format(m["device_id"]), "inline": False}
        ]
        if m.get("alternate"):
            fields.append({"name": "Alternate Names", "value": "`{}`".format(m["alternate"]), "inline": False})
        if m.get("revisions"):
            fields.append({"name": "Revisions", "value": "`{}`".format(m["revisions"]), "inline": False})
        # Something was found - let's give the info
        return await Message.Embed(
            title="AppleALC Info For {}".format(matched),
            url="https://github.com/acidanthera/AppleALC/blob/master/Resources/{}/Info.plist".format(matched),
            fields=fields,
            color=interaction.user
        ).send(interaction)

    # Config.plist Validator Slash Command
    @app_commands.command(name="plist", description="Validates .plist file structure")
    @app_commands.describe(file="Upload a config.plist file to validate")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def plist(self, interaction: discord.Interaction, file: discord.Attachment):
        """Validates plist file structure.  Accepts a .plist file attachment"""

        # Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
        await interaction.response.defer(thinking=True)

        # Validate file extension
        if not file.filename.lower().endswith((".plist")):
            return await interaction.followup.send(
                "The uploaded file does not appear to be a `.plist`. Please upload a `.plist` file.")

        # Download the attachment
        message = None  # await Message.Embed(description="Downloading...", color=interaction.user).send(interaction) - removed this for now. See similar notes in iark slash command of why this is set to none for now....

        try:
            data = await file.read()  # direct bytes of the uploaded attachment
        except Exception as e:
            return await Message.Embed(
                title="⚠ An error occurred!",
                description=f"I couldn't download the uploaded file: {e}",
                color=interaction.user
            ).send(interaction, message)

        try:
            plist_data = plistlib.loads(data)
        except Exception as e:
            return await Message.Embed(title="❌ Plist format invalid!", description=str(e), color=interaction.user).send(
                interaction,
                message)

        # Check for OpenCore specifics - list out entries enabled in
        # ACPI -> Add, ACPI -> Patch, Kernel -> Add, Kernel -> Patch,
        # Misc -> Tools, UEFI -> Drivers
        title = "✅ Plist format OK!"
        cont = "'".join(str(type(plist_data)).split("<class '")[1].split("'")[:-1])
        foot = "Plist root type: {}".format(cont)
        desc = ""
        if not isinstance(plist_data, dict):
            # Not a dict - nothing really to check
            return await Message.Embed(
                title=title,
                footer=foot,
                color=interaction.user
            ).send(interaction, message)
        else:
            # Now we walk our entries to list them as needed
            acpi_add = acpi_patch = kernel_add = kernel_patch = misc_tools = uefi_drivers = None
            booter_q = None
            boot_args = boot_args_d = None
            try:
                acpi_add = [x for x in plist_data["ACPI"]["Add"] if isinstance(x, dict) and x.get("Enabled")]
            except:
                pass
            try:
                acpi_patch = [x for x in plist_data["ACPI"]["Patch"] if isinstance(x, dict) and x.get("Enabled")]
            except:
                pass
            try:
                kernel_add = [x for x in plist_data["Kernel"]["Add"] if isinstance(x, dict) and x.get("Enabled")]
            except:
                pass
            try:
                kernel_patch = [x for x in plist_data["Kernel"]["Patch"] if isinstance(x, dict) and x.get("Enabled")]
            except:
                pass
            try:
                misc_tools = [x for x in plist_data["Misc"]["Tools"] if isinstance(x, dict) and x.get("Enabled")]
            except:
                pass
            try:
                uefi_drivers = [x for x in plist_data["UEFI"]["Drivers"] if
                                (isinstance(x, dict) and x.get("Enabled")) or isinstance(x, str)]
            except:
                pass
            try:
                booter_q = plist_data["Booter"]["Quirks"]
            except:
                pass
            try:
                boot_args = plist_data["NVRAM"]["Add"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]["boot-args"]
            except:
                pass
            try:
                boot_args_d = "boot-args" in plist_data["NVRAM"]["Delete"]["7C436110-AB2A-4BBB-A880-FE41995C9F82"]
            except:
                pass

            if any((acpi_add, acpi_patch, kernel_add, kernel_patch, misc_tools, uefi_drivers, booter_q, boot_args,
                    boot_args_d)):
                desc = "\\- Appears to belong to OpenCore"
                # Regex slightly adjusted from here: https://github.com/ocwebutils/sc_rules
                names = []
                try:
                    if any((re.match(r"^([Vv]\d+\.\d+(\.\d+)?(\s*\|\s*.+)?).*", x["Comment"]) for x in kernel_add if
                            isinstance(x.get("Comment"), str))):
                        names.append("configurator")
                except:
                    pass
                try:
                    if any((re.match(r"(?i).*(mald(o|0)n|olarila).*\.(aml|dat|bin)", x["Path"]) for x in acpi_add if
                            isinstance(x.get("Path"), str))):
                        names.append("distro")
                except:
                    pass
                try:
                    name = OCD.check_match(plist_data)
                    if name:
                        names.append(name)
                except:
                    pass
                if names:
                    name_string = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
                    foot += " | Possible {}".format(
                        name_string
                    )
                # Get the totals as well
                aa_total = ap_total = ka_total = kp_total = mt_total = ud_total = None
                try:
                    aa_total = len(plist_data["ACPI"]["Add"])
                except:
                    pass
                try:
                    ap_total = len(plist_data["ACPI"]["Patch"])
                except:
                    pass
                try:
                    ka_total = len(plist_data["Kernel"]["Add"])
                except:
                    pass
                try:
                    kp_total = len(plist_data["Kernel"]["Patch"])
                except:
                    pass
                try:
                    mt_total = len(plist_data["Misc"]["Tools"])
                except:
                    pass
                try:
                    ud_total = len(plist_data["UEFI"]["Drivers"])
                except:
                    pass
                # We'll parse these in order:
                # names_data -> booter_q -> names_data2 -> boot_args -> names_data3
                names_data = (
                    ("ACPI -> Add", acpi_add, "Path", aa_total),
                    ("ACPI -> Patch", acpi_patch, "Comment", ap_total),
                )
                names_data2 = (
                    ("Kernel -> Add", kernel_add, "BundlePath", ka_total),
                    ("Kernel -> Patch", kernel_patch, "Comment", kp_total),
                    ("Misc -> Tools", misc_tools, "Path", mt_total),
                )
                names_data3 = (
                    ("UEFI -> Drivers", uefi_drivers, "Path", ud_total),
                )
                try:
                    driver_warning = " - [Using Older OC Schema]" if all(isinstance(x, str) for x in uefi_drivers) \
                        else " - [Using mixed OC Schema!]" if any(isinstance(x, str) for x in uefi_drivers) else ""
                except:
                    driver_warning = ""

                # Set up a helper to parse
                def parse_tuple(n_d, desc, driver_warning=""):
                    for n, d, k, t in n_d:
                        if t is None or d is None:
                            continue  # Didn't exist in the source, skip
                        desc += "\n### {} ({:,}/{:,} Enabled){}{}\n".format(
                            n,
                            len(d),
                            t,
                            driver_warning if n == "UEFI -> Drivers" else "",
                            ":" if len(d) else ""
                        )
                        for i, v in enumerate(d, start=1):
                            desc += "\n{}. `{}`".format(
                                i,
                                v.get(k, "'{}' key not present!").format(k) if isinstance(v, dict) else v
                            )
                            # Check for min/max kernel and add them as needed
                            try:
                                min_kernel = v.get("MinKernel", "")
                                max_kernel = v.get("MaxKernel", "")
                                match_kernel = v.get("MatchKernel", "")
                            except:
                                continue
                            if not any((min_kernel, max_kernel, match_kernel)):
                                continue
                            # We got *something* - check min/max first
                            if min_kernel and max_kernel:
                                desc += " ({} -> {})".format(min_kernel, max_kernel)
                            elif min_kernel:
                                desc += " ({} and newer)".format(min_kernel)
                            elif max_kernel:
                                desc += " (up to {})".format(max_kernel)
                            elif match_kernel:
                                desc += " (MatchKernel: {})".format(match_kernel)
                    return desc

                # Parse the data in chunks to keep things more-or-less in order
                desc = parse_tuple(names_data, desc)
                # List the Booter -> Quirks, and boot-args as needed
                if isinstance(booter_q, dict):
                    desc += "\n### Booter -> Quirks ({:,}):\n".format(len(booter_q))
                    # List the elements of the dict and their values
                    for i, v in enumerate(booter_q, start=1):
                        desc += "\n{}. `{}` = `{}`".format(
                            i,
                            v,
                            booter_q[v]
                        )
                desc = parse_tuple(names_data2, desc)
                if boot_args:
                    desc += "\n### Boot-args (NVRAM -> Add {}):\n`{}`".format(
                        "only" if not boot_args_d else "and Delete",
                        boot_args
                    )
                desc = parse_tuple(names_data3, desc, driver_warning=driver_warning)
        if not desc:
            # Use a regular embed - as we're not picking anything
            return await Message.Embed(
                title=title,
                footer=foot,
                color=interaction.user
            ).send(interaction, message)
        # Show the page picker results
        await PickList.PagePicker(
            title=title,
            description=desc,
            max=20,
            timeout=300,
            color=interaction.user,
            message=message,
            footer=foot,
            ctx=interaction
        ).pick()

    # OC Configuration.tex search Slash Command
    @app_commands.command(name="occ", description="Search OC Configuration.tex")
    @app_commands.describe(search_path="(e.g. 'Kernel Quirks DisableIoMapper', 'SecureBootModel')")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def occ(self, interaction: discord.Interaction, search_path: str):
        """Searches the Configuration.tex file in memory for the passed path.  Must include the full path separated by spaces, /, >, or ->.

        eg.  `/occ Kernel Quirks DisableIoMapper`"""

        # Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
        await interaction.response.defer(thinking=True)

        if not self.tex: return await interaction.followup.send(
            "It looks like I was unable to get the Configuration.tex :(")


        # Let's split up the search path and ensure we have a qualified path to give to the parser
        # search_path = search_path.replace("->"," ").replace(">"," ").replace("/"," ")
        search_path = re.sub(r"(?i)(?<!PciRoot\(0x[0-9a-f]\))(?<!Pci\(0x[0-9a-f],0x[0-9a-f]\))(?<!\\)(-?>|\/| )", " ",
                             search_path)
        search_path = re.sub(" {2,}", " ", search_path)
        search_parts = search_path.split()


        # Search for matches in our Sample
        matches = self.search_sample(search_parts)
        message = None
        if matches:
            fuzzy, matches = matches  # Expand the vars
            if len(matches) > 1 or fuzzy:  # Multiple matches - show a list
                if fuzzy:
                    limit = 3
                    title = "There were no exact matches for that search, perhaps you meant {}the following:".format(
                        "one of " if len(matches) > 1 else ""
                    )
                else:
                    limit = 5
                    leftover = len(matches) - 5 if len(matches) > 5 else 0
                    title = "There were multiple results for that search, please pick from the following list{}:".format(
                        " ({:,} more omitted)".format(leftover) if leftover else ""
                    )
                    # I need to revisit this. .
                index, message = await PickList.Picker(
                    title=title,
                    list=[" -> ".join([y for y in x if y != "*"]) for x in matches[:3 if fuzzy else 5]],
                    ctx=interaction
                ).pick()
                if index < 0:
                    return await message.edit(content="Search cancelled.")
                matches = matches[index]
            else:
                matches = matches[0]
        else:
            # Fall back on the original search in case we don't have a Sample.plist,
            # or there's a version mismatch - or similar.
            matches = search_parts
        search_results = self.tex_search(self.tex, matches)
        if not search_results: return await interaction.followup.send("Nothing was found for that search :(")

        # We got something to show - let's build a page-picker
        return await PickList.PagePicker(
            title="Results For: " + " -> ".join([x for x in matches if x != "*"]),
            description=search_results,
            timeout=300,  # Allow 5 minutes before we stop watching the picker
            footer="From Configuration.tex for OpenCore v{}".format(self.tex_version),
            ctx=interaction,
            message=message
        ).pick()

    # Slide Calculation Slash Command
    @app_commands.command(name="slide", description="Calculates your slide boot-arg based on an input address (in hex).")
    @app_commands.describe(input_hex="Upload your memmap.txt dump.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def slide(self, interaction: discord.Interaction, input_hex: discord.Attachment):
        """Calculates your slide boot-arg based on an input address (in hex)."""

        # Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
        await interaction.response.defer(thinking=True)

        if input_hex is None:
            return await interaction.followup.send("Usage: `/slide input_hex:(*memmap.txt)*`")
        data = await input_hex.read()  # direct bytes of the uploaded attachment
        input_hex = data.decode("utf-8", "ignore").replace("\x00", "").replace("\r", "")
        # Removed handling for URLs like done in /plist. Have not yet figured out a way to get this working...

        # At this point - we might have a url, a table of data, or a single hex address
        # Let's split by newlines first, then by spaces
        available = self.get_available(input_hex.replace("`", "").split("\n"))
        if not len(available):
            return await interaction.followup.send("No available space was found in the passed values.")
        # Let's sort our available by their size - then walk the list until we find the
        # first valid slide
        available = sorted(available, key=lambda x: x.get("size", 0), reverse=True)
        slides = {}
        for x in available:
            slide = self.get_slide(x["start"])
            if slide >= 256 or x["start"] == 0: continue  # Out of range
            # Got a good one - spit it out
            hex_str = "{:x}".format(x["start"]).upper()
            hex_str = "0" * (len(hex_str) % 2) + hex_str
            if not slide in slides:
                slides[slide] = ("0x" + hex_str, x.get("mb", ""))
        if not len(slides):
            # If we got here - we have no applicable slides
            return await interaction.followup.send("No valid slide values were found for the passed info.")
        # Format the slides
        pad1 = max([len(x[0]) for x in slides.values()])
        pad2 = max([len(x[1]) for x in slides.values()])
        return await PickList.PagePicker(
            title="Applicable Slide Values:",
            description="\n".join(
                ["{}{}: slide={}".format(y[1].rjust(pad2), y[0].rjust(pad1), x) for x, y in slides.items()]),
            timeout=300,  # Allow 5 minutes before we stop watching the picker
            d_header="```\n",
            d_footer="```",
            ctx=interaction
        ).pick()


    # AppleALC Slash Command
    @app_commands.command(name="alc", description="Search a codec name or device-id to get layouts for AppleALC")
    @app_commands.describe(search_term="Enter a codec name or hex device-id (prefixed with 0x, or the int device-id)(e.g. 'ALC622', '0x900', '2304')")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def alc(self, interaction: discord.Interaction, search_term: str):
        # Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
        await interaction.response.defer(thinking=True)

        # No longer defering in codec, and instead defering here. Did this as if we defered in codec which is also used for
        # listcodecs - it would try re-defer when listcodecs called codec - as it already deferred the response.
        # Had to move the function as if buried in app_commands the function was not callable.

        # Run codec
        return await self.codec(interaction, search_term)

    # List Codecs Slash Command
    @app_commands.command(name="listcodecs", description="Lists the codecs in the AppleALCCodecs.plist")
    @app_commands.describe(search_term="(Optional) Enter a codec name to get the 3 closest search results:")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def listcodecs(self, interaction: discord.Interaction, search_term: str | None = None):
        """Lists the codecs in the AppleALCCodecs.plist - can optionally take a codec name as a search term and will list the 3 closest results."""

        # Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
        await interaction.response.defer(thinking=True)

        if not self.alc_codecs: return await interaction.followup.send("It looks like I was unable to get the AppleALCCodecs.plist :(")

        fields = []
        if search_term:
            search_list = list(self.alc_codecs)
            for codec in self.alc_alternate:
                search_list.extend(self.alc_alternate[codec])
            codec_search = FuzzySearch.search(search_term.upper(), search_list)
            full_match = next((x["Item"] for x in codec_search if x.get("Ratio") == 1), None)
            if full_match:  # Got an exact match - just run codec
                return await self.codec(interaction, search_term)
            title = "Search Results For \"{}\"".format(search_term)
            for i, x in enumerate(codec_search, start=1):
                m = self._get_codec_info(x["Item"])
                fields.append({
                    "name": "{}. {}".format(i, x["Item"]),
                    "value": "` └─ Vendor: {}`\n` └─ Layout IDs: {}`\n` └─ Device ID: {}`{}{}".format(
                        m["vendor"],
                        m["layouts"],
                        m["device_id"],
                        "\n` └─ Revisions: {}`".format(m["revisions"]) if m.get("revisions") else "",
                        "\n` └─ Alternate Names: {}`".format(m["alternate"]) if m.get("alternate") else ""
                    ),
                    "inline": False})
        else:
            title = "Currently Supported AppleALC Codecs ({:,} total)".format(len(self.alc_codecs))
            for i, x in enumerate(self.alc_codecs, start=1):
                m = self._get_codec_info(x)
                fields.append({
                    "name": "{}. {}".format(i, x),
                    "value": "` └─ Vendor: {}`\n` └─ Layout IDs: {}`\n` └─ Device ID: {}`{}{}".format(
                        m["vendor"],
                        m["layouts"],
                        m["device_id"],
                        "\n` └─ Revisions: {}`".format(m["revisions"]) if m.get("revisions") else "",
                        "\n` └─ Alternate Names: {}`".format(m["alternate"]) if m.get("alternate") else ""
                    ),
                    "inline": False})
        return await PickList.PagePicker(
            title=title,
            list=fields,
            timeout=300,  # Allow 5 minutes before we stop watching the picker
            max=5,
            ctx=interaction
        ).pick()

    # WhateverGreen Slash Command:
    @app_commands.command(name="weg", description="Searches WhateverGreen IntelHD FAQ for device-id and connector info")
    @app_commands.describe(search_term="Can enter a big/little endian device-id, AAPL,ig-platform-id, or AAPL,snb-platform-id")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def weg(self, interaction: discord.Interaction, search_term: str | None = None):
        """Search the WhateverGreen IntelHD FAQ for device-id and connector info.
        Can take a big or little endian device-id, AAPL,ig-platform-id, or AAPL,snb-platform-id as a search term."""

        # Avoids "interaction did not respond" and also avoids a NoneType.to_dict() error
        await interaction.response.defer(thinking=True)

        if not self.fbs:
            return await interaction.followup.send("It looks like I was unable to get the WhateverGreenFBs.plist :(")

        def list_ids(id_list, cols=4):
            id_list = ["`0x{}`".format(d) for d in id_list]
            id_rows = [" ".join(id_list[0 + i:cols + i]) for i in range(0, len(id_list), cols)]
            return "\n".join(id_rows)

        title = desc = ""
        url = "https://github.com/acidanthera/WhateverGreen/blob/master/Manual/FAQ.IntelHD.en.md"

        if search_term is not None:
            # We have a search term - let's find out if it's a device-id, or AAPL,(ig|snb)-platform-id
            # and list relevant info accordingly
            # Normalize the search term display - make sure we strip <>, 0x, spaces, and commmas - and
            # convert it to a number
            search_adj = search_term.lower().replace("<", "").replace(">", "").replace("0x", "").replace(" ",
                                                                                                         "").replace(
                ",", "")
            try:
                search_int = int(search_adj, 16)
            except:
                return await interaction.followup.send("That doesn't appear to be a valid hexadecimal value.")
            search_adj = hex(search_int)[2:].upper()  # More normalization
            # Pad to 8 chars as everything is justified that way
            search_adj = search_adj.rjust(8, "0")
            search_rev = "{}{}{}{}".format(
                search_adj[6:],
                search_adj[4:6],
                search_adj[2:4],
                search_adj[:2]
            )
            # Walk our data and search for any matches
            search_tuple = (search_adj, search_rev)

            for proc in self.fbs:
                kext = self.fbs[proc].get("kext")
                gpus = self.fbs[proc].get("model")
                name = f"AAPL,{'ig' if not kext or 'SNB' not in kext else 'snb'}-platform-id"

                # Check connectors - then device-ids
                for con in sorted(self.fbs[proc].get("connectors", {})):
                    # Extract the big endian and little endian values
                    try:
                        big, lil, info = self.fbs[proc]["connectors"][con]
                    except:
                        # Broken or missing info - skip
                        continue
                    if big in search_tuple or lil in search_tuple:
                        title = "Connector Match for 0x{}".format(search_adj)
                        desc = "### Architecture\n{}".format(proc)
                        if gpus:
                            desc += "\n### GPUs\n{}".format(gpus)
                        desc += "\n### {}\n`0x{}` (Big Endian)\n`0x{}` (Little Endian)".format(
                            name,
                            big,
                            lil
                        )
                        if kext:
                            desc += "\n### Framebuffer Kext\n`{}`".format(kext)
                        if self.fbs[proc].get("device-ids"):
                            # List the platforms as well
                            desc += "\n### Supported Device-IDs\n{}".format(
                                list_ids(self.fbs[proc]["device-ids"], cols=4)
                            )
                        desc += "\n### Connector Info\n```\n{}```".format(info)
                        break
                # Try the device-ids
                for dev in sorted(self.fbs[proc].get("device-ids", {})):
                    try:
                        big, lil = self.fbs[proc]["device-ids"][dev]
                    except:
                        continue
                    if big in search_tuple or lil in search_tuple:
                        title = "Device-ID Match for 0x{}".format(search_adj)
                        desc = "### Architecture\n{}".format(proc)
                        if gpus:
                            desc += "\n### GPUs\n{}".format(gpus)
                        desc += "\n### Device-ID\n`0x{}` (Big Endian)\n`0x{}` (Little Endian)".format(
                            big,
                            lil
                        )
                        if kext:
                            desc += "\n### Framebuffer Kext\n`{}`".format(kext)
                        if self.fbs[proc].get("connectors"):
                            # List the platforms as well
                            desc += "\n### {} List\n{}".format(
                                name,
                                list_ids(self.fbs[proc]["connectors"], cols=3)
                            )
                        break
            # Send our message accordingly
            if title and desc:
                return await Message.Embed(
                    title=title,
                    url=url,
                    description=desc,
                    color=interaction.user
                ).send(interaction)
            else:
                return await interaction.followup.send(f"Nothing was found for that search term.")

        # No search term - just gather a list of arch, gpus, kexts, device-ids, and platform-ids
        arch_sort = []
        for proc in self.fbs:
            dec_devs = []
            for dev in self.fbs[proc].get("device_ids", {}):
                try:
                    dec_devs.append(int(dev, 16))
                except:
                    continue
            if not dec_devs:
                # Append 0xFFFF for sorting purposes
                dec_devs.append(0xFFFF)
            arch_sort.append((proc, max(dec_devs)))
        for proc, i in sorted(arch_sort, key=lambda x: x[1]):
            kext = self.fbs[proc].get("kext")
            gpus = self.fbs[proc].get("model")
            name = "AAPL,{}-platform-id".format(
                "ig" if not kext or not "SNB" in kext else "snb"
            )
            desc = "" if not desc else desc + "\n"  # Ensure padding
            desc += "### {}:".format(proc)
            if gpus:
                desc += "\n### GPUs\n{}".format(gpus)
            if kext:
                desc += "\n### Framebuffer Kext\n`{}`".format(kext)
            if self.fbs[proc].get("device-ids"):
                # List the platforms as well
                desc += "\n### Supported Device-IDs\n{}".format(
                    list_ids(self.fbs[proc]["device-ids"], cols=4)
                )
            if self.fbs[proc].get("connectors"):
                # List the platforms as well
                desc += "\n### {} List\n{}".format(
                    name,
                    list_ids(self.fbs[proc]["connectors"], cols=3)
                )
        if not desc:
            return await interaction.followup.send("Something went wrong gathering data... :(")
        return await PickList.PagePicker(
            title="Framebuffer List from WEG's IntelHD FAQ",
            url=url,
            description=desc,
            timeout=300,  # Allow 5 minutes before we stop watching the picker
            ctx=interaction
        ).pick()
