import lavalink
import codecs
import yaml
from hurry.filesize import size, alternative

from cogs.utils.mixplayer import MixPlayer
from cogs.utils.checks import is_sub_cmd
import cogs.utils.timeformatter as tf

import discord
from discord.ext import commands


class Linker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = self.bot.main_logger.bot_logger.getChild("Lavalinker")
        if not hasattr(bot, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            bot.lavalink = self.linker(bot)

    def linker(self, bot):
        bot.lavalink = lavalink.Client(bot.user.id, player=MixPlayer)
        bot.lavalink = self.default_nodes(bot.lavalink)
        bot.add_listener(bot.lavalink.voice_update_handler, 'on_socket_response')

        return bot.lavalink

    def default_nodes(self, lavalink):
        with codecs.open(f"{self.bot.datadir}/config.yaml", 'r', encoding='utf8') as f:
            conf = yaml.load(f, Loader=yaml.SafeLoader)

        for node in conf['lavalink nodes']:
            lavalink.add_node(**conf['lavalink nodes'][node])
            self.logger.debug("Adding node %s to pool" % node)
        return lavalink

    def load(self):
        """Loads music modules."""
        music_extentions = [
                'cogs.music',
                'cogs.musicevents'
        ]

        for extension in music_extentions:
            try:
                self.logger.debug("Loading extension %s" % extension)
                self.bot.load_extension(extension)
            except Exception:
                self.logger.exception("Loading of extension %s failed" % extension)

    def regioner(self, node):
        flags = {
            'us': ':flag_us:',
            'eu': ':flag_eu:',
            'singapore': ':flag_sg:',
            'london': ':flag_gb:',
            'sydeny': ':flag_au:',
            'amsterdam': ':flag_nl:',
            'frankfurt': ':flag_de:',
            'brazil': ':flag_br:',
            'japan': ':flag_jp:',
            'russia': ':flag_ru:',
            'southafrica': ':flag_za:',
            'hongkong': ':flag_hk:',
            'india': ':flag_in:'
            }
        region = str(node.region)
        if region.startswith('us'):
            region = 'us'
        elif region.startswith('eu'):
            region = 'eu'
        elif region.startswith('amsterdam'):
            region = 'amsterdam'
        try:
            flag = flags[region]
        except KeyError:
            flag = ':question:'
        return flag

    @is_sub_cmd()
    @commands.group(name='node', hidden=True)
    async def _node(self, ctx):
        if ctx.invoked_subcommand is None:
            if self.bot.lavalink.player_manager.get(ctx.guild.id) is not None:
                await self.current_nodes.invoke(ctx)
            else:
                await self._nodes.invoke(ctx)

    @is_sub_cmd()
    @_node.command(name="add")
    async def _add(self, ctx, host, port, password, region, name):
        self.bot.lavalink.add_node(host, port, password, region, name=name)
        self.logger.debug("Adding node %s to pool" % name)
        await ctx.send(f"Added node {name}")

    @is_sub_cmd()
    @commands.guild_only()
    @_node.command(name="remove")
    async def _remove(self, ctx, name):
        removed_nodes = []
        for node in self.bot.lavalink.node_manager:
            if node.name.lower() == name.lower():
                self.bot.lavalink.node_manager.remove_node(node)
                self.logger.debug("Adding node %s to pool" % node.name)
                removed_nodes.append(node.name)
        await ctx.send(f"Removed nodes: {removed_nodes}\nNodes left:")
        await self._nodes.invoke(ctx)

    @is_sub_cmd()
    @commands.guild_only()
    @_node.command(name="reload")
    async def _reload(self, ctx):
        for node in self.bot.lavalink.node_manager:
            self.bot.lavalink.node_manager.remove_node(node)
        self.bot.lavalink = self.default_nodes(self.bot.lavalink)

    @is_sub_cmd()
    @commands.guild_only()
    @_node.command(name="nodes")
    async def _nodes(self, ctx):
        embed = discord.Embed(title=f"Nodes", color=ctx.me.color)
        for node in self.bot.lavalink.node_manager:
            value = f"⏰: {tf.format(node.stats.uptime)} | " \
                    f"🗄️: {size(node.stats.memory_used, system=alternative)}/" \
                    f"{size(node.stats.memory_allocated, system=alternative)} | " \
                    f"🖥️: {str(float(node.stats.system_load) / float(node.stats.cpu_cores))[0:4]}"
            embed.add_field(name=f"{self.regioner(node)} - {node.name}", value=value)
        await ctx.send(embed=embed)

    @is_sub_cmd()
    @commands.guild_only()
    @_node.command(name='current')
    async def current_nodes(self, ctx):
        node = self.bot.lavalink.player_manager.get(ctx.guild.id).node
        if self.bot.lavalink.player_manager.get(ctx.guild.id) is not None:
            pass
        else:
            await ctx.send("No players for this guild")

        listeners = 0
        for player in node.players:
            listeners += len(player.listeners)

        memory = f"{size(node.stats.memory_used, system=alternative)}/" \
                 f"{size(node.stats.memory_allocated, system=alternative)}"

        embed = discord.Embed(title=f"{node.name.replace('-',' ').title()}", color=ctx.me.color)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name='Node Uptime', value=tf.format(node.stats.uptime))
        embed.add_field(name='Node Memory', value=memory)
        embed.add_field(name='Node Region', value=self.regioner(node))
        embed.add_field(name='Node Players', value=len(node.players))
        embed.add_field(name='Node listeners', value=listeners)

        await ctx.send(embed=embed)


def setup(bot):
    n = Linker(bot)
    n.load()
    bot.add_cog(n)
