from plusminus import ArithmeticParser
import regex as re
import math, random, discord
from discord import app_commands
from discord.ext import commands

async def setup(bot):
    # Add the bot
    await bot.add_cog(Calc(bot))

class CustomArithmeticParser(ArithmeticParser):
    
    def customize(self):
        # Ensure the ArithmeticParser class customizes first
        super().customize()
        # Add our customizations
        self.add_operator("&",2,ArithmeticParser.LEFT,lambda a,b:a&b)
        self.add_operator("|",2,ArithmeticParser.LEFT,lambda a,b:a|b)
        self.add_operator("^",2,ArithmeticParser.LEFT,lambda a,b:a^b)
        self.add_operator("~",1,ArithmeticParser.RIGHT,lambda a:~a)
        self.add_operator("<<",2,ArithmeticParser.LEFT,lambda a,b:a<<b)
        self.add_operator(">>",2,ArithmeticParser.LEFT,lambda a,b:a>>b)
        self.add_function("sqrt",1,lambda a:math.sqrt(a))
        self.add_function("rand",2,lambda a,b:random.randint(a,b))
        self.add_function("random",2,lambda a,b:random.randint(a,b))

class Calc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.hex_re = re.compile(r"(?i)(0x|#)[0-9a-f]+")

    # Calc Slash Command
    @app_commands.command(name="calc", description="Do some math.")
    @app_commands.describe(formula="Enter a formula: `28492+(285*15)`")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.user_install()
    async def calc(self, interaction: discord.Interaction, formula: str):
        """Do some math."""

        await interaction.response.defer(thinking=True)

        parser_lines = [x.strip() for x in formula.replace(";","\n").split("\n") if x.strip()]
        clean_lines = []
        parser = CustomArithmeticParser()
        try:
            for line in parser_lines:
                offset = 0
                # Let's regex our way through 0x and # integers
                for m in re.finditer(self.hex_re,line):
                    try:
                        start,end = m.span()
                        hex_int = str(int(m.group(0).replace("#","0x"),16))
                        current_len = len(line)
                        # Specifically replace this *one* instance
                        line = line[0:start+offset]+str(hex_int)+line[end+offset:]
                        # Get the offset - i.e. how much our line length
                        # changed after applying - so we know to adjust
                        offset += len(line)-current_len
                    except:
                        pass
                result = await self.bot.loop.run_in_executor(None,parser.evaluate,line)
                clean_lines.append("{} = {}".format(
                    " ".join(line.split()).replace("`","").replace("\\",""),
                    result
                ))
        except Exception as e:
            msg  = 'I couldn\'t parse that formula :(\n'
            msg += "```\n{}\n```\n".format(str(e).replace("`","back tick"))
            msg += 'Please see [this page](<https://github.com/pyparsing/plusminus/blob/master/doc/arithmetic_parser.md>) for parsing info.\n\n'
            msg += '__Additional syntax supported:__\n'
            msg += '* Newlines or semicolons (`;`) separate lines passed to the parser\n'
            msg += '* `0x` or `#` prefixes denote hexadecimal values\n'
            msg += '* `&` for bitwise AND\n'
            msg += '* `|` for bitwise OR\n'
            msg += '* `^` for bitwise XOR\n'
            msg += '* `~` for bitwise NOT\n'
            msg += '* `<<` bit shift left\n'
            msg += '* `>>` bit shift right\n'
            msg += '* `sqrt()` square root'
            return await interaction.followup.send(msg)
        # Save the cleaned lines as a string
        clean_lines = "\n".join(clean_lines)
        # Send the results
        over_amount = (len(clean_lines)+len(str(result))+8)-2000
        if over_amount > 0:
            clean_lines = "..."+clean_lines[over_amount+3:]
        await interaction.followup.send("```\n{}\n```".format(clean_lines))
