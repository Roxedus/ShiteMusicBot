import discord
import os
import asyncio
import time
import random
import platform

from discord.ext import commands
from cogs.utils import checks
from lavalink import __version__ as LavalinkVersion

class Misc:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping', hidden=True)
    @checks.is_mod()
    async def _ping(self, ctx):
            start = time.perf_counter()
            message = await ctx.send('Ping...')
            end = time.perf_counter()
            duration = int((end - start) * 1000)
            edit = f'Pong!\nPing: {duration}ms' \
                + f' | websocket: {int(self.bot.latency * 1000)}ms'
            await message.edit(content=edit)

    @commands.command(name='uptime', hidden=True)
    async def _uptime(self, ctx):
        now = time.time()
        diff = int(now - self.bot.uptime)
        days, remainder = divmod(diff, 24 * 60 * 60)
        hours, remainder = divmod(remainder, 60 * 60)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(f'{days}d {hours}h {minutes}m {seconds}s')

    @commands.command(name='guilds')
    @checks.is_owner()
    async def _guilds(self, ctx):
        guilds = f"{self.bot.user.name} is in:\n"
        for guild in self.bot.guilds:
            guilds += f"{guild.name}\n"
        await ctx.send(guilds)
    

    @commands.command(name="reloadlocale")
    async def reload_locale(self, ctx):
        self.bot.localizer.index_localizations()
        self.bot.localizer.load_localizations()
        await ctx.send("Localizations reloaded.")

    @commands.command()
    async def info(self, ctx):
        """
        Info om Shite Music Bot
        """
        membercount = []
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id in membercount:
                    pass
                else:
                    membercount.append(member.id)
        guilds = len(self.bot.guilds)
        members = len(membercount)
        now = time.time()
        diff = int(now - self.bot.uptime)
        days, remainder = divmod(diff, 24 * 60 * 60)
        hours, remainder = divmod(remainder, 60 * 60)
        minutes, seconds = divmod(remainder, 60)
        avatar = self.bot.user.avatar_url_as(format=None,
                                                static_format='png',
                                                size=1024)
        infotext = '{info.infotext}'
        spectext = self.bot.localizer.get("info.spectext").format(_python_v=platform.python_version, _discord_v=discord.__version__, _lavalink_v=LavalinkVersion)
        stattext = self.bot.localizer.get("info.stattext").format(_guilds=guilds, _members=members)
        uptimetext = f'{days}d {hours}t {minutes}m {seconds}s'
        embed = discord.Embed(color=0xD9C04D)
        embed.set_author(name=self.bot.user.name, icon_url=avatar)
        embed.set_thumbnail(url=avatar)
        embed.add_field(name="{info.what}",
                        value=infotext, inline=False)
        embed.set_footer(icon_url="https://cdn.discordapp.com/icons/297798952538079233/0198dc7b01ccf288b985b8a394cb1d44.jpg?size=64",
                            text="{info.footer_text}")
        embed.add_field(name="{info.how}",
                        value=spectext)
        embed.add_field(name="{info.how_many}",
                        value=stattext)
        embed.add_field(name="{info.how_long}",
                        value=uptimetext)

        embed = self.bot.localizer.format_embed(embed, self.bot.settings.get_locale(ctx.guild.id))
        await ctx.send(embed=embed)

        @commands.command()
        @checks.is_even()
        async def only_me(self, ctx):
            await ctx.send('Only you!')


def setup(bot):
    bot.add_cog(Misc(bot))
