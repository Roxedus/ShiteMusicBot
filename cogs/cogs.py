import discord
import os
import json
import codecs
from discord.ext import commands
from cogs.utils import checks

class Cogs:
    def __init__(self, bot):
        self.bot = bot
        self.settings = self.bot.settings

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group(name='cogs')
    async def _cogs(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'),
                             ctx.command.qualified_name)

    @_cogs.command()
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.bot.load_extension(f'cogs.{module}')
            ctx.send(f'{module} loaded')
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc(e)}\n```')

    @_cogs.command()
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.bot.unload_extension(f'cogs.{module}')
            ctx.send(f'{module} unloaded')
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')

    @_cogs.command(name='reload')
    async def _reload(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.bot.unload_extension(f'cogs.{module}')
            self.bot.load_extension(f'cogs.{module}')
            ctx.send(f'{module} reloaded')
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')

    @_cogs.command(name='reloadall')
    async def _relaod_all(self, ctx):
        """Reloads all extensions"""
        try:
            for extension in self.bot.extensions:
                self.bot.unload_extension(f'cogs.{module}')
                self.bot.load_extension(f'cogs.{module}')
            ctx.send('Extensions reloaded')
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')


def setup(bot):
    bot.add_cog(Cogs(bot))