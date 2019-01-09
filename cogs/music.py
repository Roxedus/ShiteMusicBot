#!/usr/bin/env python3

"""
This is an example code that shows how you would setup a simple music bot for Lavalink v3.
This example is only compatible with the discord.py rewrite branch.
Because of the F-Strings, you also must have Python 3.6 or higher installed.
"""

import logging
import math
import re

import time
import asyncio
from cogs.utils import RoxUtils

import discord
import lavalink
from discord.ext import commands
from lavasettings import *

time_rx = re.compile('[0-9]+')
url_rx = re.compile('https?:\/\/(?:www\.)?.+')


class Music:
	def __init__(self, bot):
		self.bot = bot

		if not hasattr(bot, 'lavalink'):
			lavalink.Client(bot=bot, password='youshallnotpass',
			                loop=bot.loop, log_level=logging.INFO,
			                host=host, ws_port=ws_port,
			                rest_port=rest_port)
			self.bot.lavalink.register_hook(self._track_hook)

	def __unload(self):
		for guild_id, player in self.bot.lavalink.players:
			self.bot.loop.create_task(player.disconnect())
			player.cleanup()
		# Clear the players from Lavalink's internal cache
		self.bot.lavalink.players.clear()
		self.bot.lavalink.unregister_hook(self._track_hook)

	async def _track_hook(self, event):
		if isinstance(event, lavalink.Events.StatsUpdateEvent):
			return
		channel = self.bot.get_channel(event.player.fetch('channel'))
		if not channel:
			return

		if isinstance(event, lavalink.Events.TrackStartEvent):
			embed = discord.Embed(title='Now playing:', description=event.track.title, color=discord.Color.blurple())
			thumbnail_url = RoxUtils.thumbnailer(self, event.player.current.identifier, event.player.current.uri)
			if thumbnail_url:
				embed.set_thumbnail(url=thumbnail_url)
			await channel.send(embed=embed)
		elif isinstance(event, lavalink.Events.QueueEndEvent):
			await channel.send('Queue ended! Why not queue more songs?')

	@commands.command(name='play', aliases=['p'])
	@commands.guild_only()
	async def _play(self, ctx, *, query: str):
		""" Searches and plays a song from a given query. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		query = query.strip('<>')

		if not url_rx.match(query):
			query = f'ytsearch:{query}'

		results = await self.bot.lavalink.get_tracks(query)

		if not results or not results['tracks']:
			return await ctx.send('Nothing found!')

		embed = discord.Embed(color=discord.Color.blurple())

		if results['loadType'] == 'PLAYLIST_LOADED':
			tracks = results['tracks']

			for track in tracks:
				player.add(requester=ctx.author.id, track=track)

			embed.title = 'Playlist Enqueued!'
			embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
			await ctx.send(embed=embed)
		else:
			track = results['tracks'][0]
			embed.title = 'Track Enqueued'
			print(track)
			thumbnail_url = RoxUtils.thumbnailer(self, track['info']['identifier'], track['info']['uri'])
			if thumbnail_url:
				embed.set_thumbnail(url=thumbnail_url)

			embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
			await ctx.send(embed=embed)
			player.add(requester=ctx.author.id, track=track)

		if not player.is_playing:
			await player.play()

	@commands.command(name='previous', aliases=['pv'])
	@commands.guild_only()
	async def _previous(self, ctx):
		""" Plays the previous song. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		try:
			await player.play_previous()
		except lavalink.NoPreviousTrack:
			await ctx.send('There is no previous song to play.')

	@commands.command(name='playnow', aliases=['pn'])
	@commands.guild_only()
	async def _playnow(self, ctx, *, query: str):
		""" Plays immediately a song. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.queue and not player.is_playing:
			return await ctx.invoke(self._play, query=query)

		query = query.strip('<>')

		if not url_rx.match(query):
			query = f'ytsearch:{query}'

		results = await self.bot.lavalink.get_tracks(query)

		if not results or not results['tracks']:
			return await ctx.send('Nothing found!')

		tracks = results['tracks']
		track = tracks.pop(0)

		if results['loadType'] == 'PLAYLIST_LOADED':
			for _track in tracks:
				player.add(requester=ctx.author.id, track=_track)

		await player.play_now(requester=ctx.author.id, track=track)

	@commands.command(name='playat', aliases=['pa'])
	@commands.guild_only()
	async def _playat(self, ctx, index: int):
		""" Plays the queue from a specific point. Disregards tracks before the index. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if index < 1:
			return await ctx.send('Invalid specified index.')

		if len(player.queue) < index:
			return await ctx.send('This index exceeds the queue\'s length.')

		await player.play_at(index-1)

	@commands.command(name='seek')
	@commands.guild_only()
	async def _seek(self, ctx, *, time: str):
		""" Seeks to a given position in a track. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.is_playing:
			return await ctx.send('Not playing.')

		seconds = time_rx.search(time)
		if not seconds:
			return await ctx.send('You need to specify the amount of seconds to skip!')

		seconds = int(seconds.group()) * 1000
		if time.startswith('-'):
			seconds *= -1

		track_time = player.position + seconds
		await player.seek(track_time)

		await ctx.send(f'Moved track to **{lavalink.Utils.format_time(track_time)}**')

	@commands.command(name='skip', aliases=['forceskip', 'fs'])
	@commands.guild_only()
	async def _skip(self, ctx):
		""" Skips the current track. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.is_playing:
			return await ctx.send('Not playing.')

		await player.skip()
		await ctx.send('⏭ | Skipped.')

	@commands.command(name='stop')
	@commands.guild_only()
	async def _stop(self, ctx):
		""" Stops the player and clears its queue. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.is_playing:
			return await ctx.send('Not playing.')

		player.queue.clear()
		await player.stop()
		await ctx.send('⏹ | Stopped.')

	@commands.command(name='now', aliases=['np', 'n', 'playing'])
	@commands.guild_only()
	async def _now(self, ctx):
		""" Shows some stats about the currently playing song. """
		player = self.bot.lavalink.players.get(ctx.guild.id)
		song = 'Nothing'

		if player.current:
			position = lavalink.Utils.format_time(player.position)
			if player.current.stream:
				duration = '🔴 LIVE'
			else:
				duration = lavalink.Utils.format_time(player.current.duration)
			song = f'**[{player.current.title}]({player.current.uri})**\n({position}/{duration})'

		embed = discord.Embed(color=discord.Color.blurple(),
		                      title='Now Playing', description=song)

		thumbnail_url = RoxUtils.thumbnailer(self, player.current.identifier, player.current.uri)
		if thumbnail_url:
			embed.set_thumbnail(url=thumbnail_url)

		await ctx.send(embed=embed)

	@commands.command(name='queue', aliases=['q'])
	@commands.guild_only()
	async def _queue(self, ctx, page: int = 1):
		""" Shows the player's queue. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.queue:
			return await ctx.send('There\'s nothing in the queue! Why not queue something?')

		items_per_page = 10
		pages = math.ceil(len(player.queue) / items_per_page)

		start = (page - 1) * items_per_page
		end = start + items_per_page

		queue_list = ''
		for index, track in enumerate(player.queue[start:end], start=start):
			queue_list += f'`{index + 1}.` [**{track.title}**]({track.uri})\n'

		embed = discord.Embed(colour=discord.Color.blurple(),
		                      description=f'**{len(player.queue)} tracks**\n\n{queue_list}')
		embed.set_footer(text=f'Viewing page {page}/{pages}')
		await ctx.send(embed=embed)

	@commands.command(name='pause', aliases=['resume'])
	@commands.guild_only()
	async def _pause(self, ctx):
		""" Pauses/Resumes the current track. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.is_playing:
			return await ctx.send('Not playing.')

		if player.paused:
			await player.set_pause(False)
			await ctx.send('⏯ | Resumed')
		else:
			await player.set_pause(True)
			await ctx.send('⏯ | Paused')

	@commands.command(name='volume', aliases=['vol'])
	@commands.guild_only()
	async def _volume(self, ctx, volume: int = None):
		""" Changes the player's volume. Must be between 0 and 1000. Error Handling for that is done by Lavalink. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not volume:
			return await ctx.send(f'🔈 | {player.volume}%')

		await player.set_volume(volume)
		await ctx.send(f'🔈 | Set to {player.volume}%')

	@commands.command(name='shuffle')
	@commands.guild_only()
	async def _shuffle(self, ctx):
		""" Shuffles the player's queue. """
		player = self.bot.lavalink.players.get(ctx.guild.id)
		if not player.is_playing:
			return await ctx.send('Nothing playing.')

		player.shuffle = not player.shuffle
		await ctx.send('🔀 | Shuffle ' + ('enabled' if player.shuffle else 'disabled'))

	@commands.command(name='repeat', aliases=['loop'])
	@commands.guild_only()
	async def _repeat(self, ctx):
		""" Repeats the current song until the command is invoked again. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.is_playing:
			return await ctx.send('Nothing playing.')

		player.repeat = not player.repeat
		await ctx.send('🔁 | Repeat ' + ('enabled' if player.repeat else 'disabled'))

	@commands.command(name='remove')
	@commands.guild_only()
	async def _remove(self, ctx, index: int):
		""" Removes an item from the player's queue with the given index. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.queue:
			return await ctx.send('Nothing queued.')

		if index > len(player.queue) or index < 1:
			return await ctx.send(f'Index has to be **between** 1 and {len(player.queue)}')

		index -= 1
		removed = player.queue.pop(index)

		await ctx.send(f'Removed **{removed.title}** from the queue.')

	@commands.command(name='find')
	@commands.guild_only()
	async def _find(self, ctx, *, query):
		""" Lists the first 10 search results from a given query. """
		await ctx.trigger_typing()
		not_reacted = True
		react_emoji = {1: "\u0030\u20E3", 2: "\u0031\u20E3", 3: "\u0032\u20E3", 4: "\u0033\u20E3", 5: "\u0034\u20E3",
		               6: "\u0035\u20E3", 7: "\u0036\u20E3", 8: "\u0037\u20E3", 9: "\u0038\u20E3", 10: "\u0039\u20E3"}

		if not query.startswith('ytsearch:') and not query.startswith('scsearch:'):
			query = 'ytsearch:' + query

		results = await self.bot.lavalink.get_tracks(query)

		if not results or not results['tracks']:
			return await ctx.send('Nothing found')

		tracks = results['tracks'][:10]  # First 10 results

		o = ''
		for index, track in enumerate(tracks, start=1):
			track_title = track["info"]["title"]
			track_uri = track["info"]["uri"]

			o += f'{react_emoji[index]} [{track_title}]({track_uri})\n'

		embed_start = discord.Embed(color=discord.Color.blurple(), description=o)
		start_msg = await ctx.send(embed=embed_start)
		await ctx.trigger_typing()
		for num_index in range(min(len(tracks), 10)):
			index = num_index + 1
			await start_msg.add_reaction(react_emoji[index])
		await start_msg.add_reaction("\u274C")
		# React does shit
		time_start = time.time()

		while not_reacted:
			await ctx.trigger_typing()
			embed = discord.Embed(color=discord.Color.blurple())
			timer = time.time() - time_start
			msg_id = await ctx.get_message(start_msg.id)
			if int(timer) >= 10:
				await start_msg.clear_reactions()
				embed.title = "Sorry"
				embed.description = "Timer expired"
				await start_msg.edit(embed=embed)
				ping = await ctx.send(content=f"{ctx.author.mention}")
				await asyncio.sleep(10)
				await ctx.message.delete()
				await ping.delete()
				await msg_id.delete()
				break
			for react in msg_id.reactions:
				async for user in react.users():
					if user is ctx.author:
						if react.emoji[:-1].isdigit():
							not_reacted = False
							track_num = int(react.emoji[:-1])
							track_ = tracks[track_num]
							await self.send_to_play(ctx, track_)
							embed.title = "Song sent to queue"
							thumb_url = RoxUtils.thumbnailer(self, track_['info']['identifier'],track_['info']['uri'])
							if thumb_url:
								embed.set_thumbnail(url=thumb_url)
							embed.description = f'[{track_["info"]["title"]}]({track_["info"]["uri"]})'
							await start_msg.edit(embed=embed)
							await start_msg.clear_reactions()
							break
						if react.emoji == "\u274C":
							not_reacted = False
							await start_msg.clear_reactions()
							embed.title = "Sorry"
							embed.description = "Search cancelled by user"
							await start_msg.edit(embed=embed)
							ping = await ctx.send(content=f"{user.mention}")
							await asyncio.sleep(10)
							await ctx.message.delete()
							await ping.delete()
							await msg_id.delete()
							break


	@commands.command(name='disconnect', aliases=['dc'])
	@commands.guild_only()
	async def _disconnect(self, ctx):
		""" Disconnects the player from the voice channel and clears its queue. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.is_connected:
			return await ctx.send('Not connected.')

		if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
			return await ctx.send('You\'re not in my voicechannel!')

		player.queue.clear()
		await player.disconnect()
		await ctx.send('*⃣ | Disconnected.')

	async def send_to_play(self, ctx, track):
		await self.ensure_voice_real(ctx)
		player = self.bot.lavalink.players.get(ctx.guild.id)
		player.add(requester=ctx.author.id, track=track)
		if not player.is_playing:
			await player.play()

	@_playnow.before_invoke
	@_previous.before_invoke
	@_play.before_invoke
	async def ensure_voice(self, ctx):
		await self.ensure_voice_real(ctx)

	async def ensure_voice_real(self, ctx):
		""" A few checks to make sure the bot can join a voice channel. """
		player = self.bot.lavalink.players.get(ctx.guild.id)

		if not player.is_connected:
			if not ctx.author.voice or not ctx.author.voice.channel:
				await ctx.send('You aren\'t connected to any voice channel.')
				raise commands.CommandInvokeError(
					'Author not connected to voice channel.')

			permissions = ctx.author.voice.channel.permissions_for(ctx.me)

			if not permissions.connect or not permissions.speak:
				await ctx.send('Missing permissions `CONNECT` and/or `SPEAK`.')
				raise commands.CommandInvokeError(
					'Bot has no permissions CONNECT and/or SPEAK')

			player.store('channel', ctx.channel.id)
			await player.connect(ctx.author.voice.channel.id)
		else:
			if player.connected_channel.id != ctx.author.voice.channel.id:
				return await ctx.send('Join my voice channel!')


def setup(bot):
	bot.add_cog(Music(bot))
