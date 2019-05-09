import discord
import asyncio
import itertools
import inspect

from .paginator import *

class Selector(TextPaginator):
    def __init__(self, ctx, identifiers, functions, arguments, terminate_on_select=True, num_selections=3, max_size=2000, **embed_base):
        self.ctx = ctx
        self.bot = ctx.bot
        self.cmdmsg = ctx.message
        self.message = ctx.message
        self.channel = ctx.channel
        self.author = ctx.author

        self.localizer = ctx.localizer

        self.num_selections = num_selections
        self.terminate_on_select = terminate_on_select

        assert len(identifiers) == len(functions) == len(arguments)
        super().__init__(max_size=max_size, max_lines=num_selections, **embed_base)

        self.selections = list(zip(identifiers, functions, arguments))


        for i, selection in enumerate(self.selections):
            self.add_line(f"{i%num_selections+1}\N{combining enclosing keycap} {selection[0]}")
        self.close_page()

        if len(self.pages) > 1:
            self.scrolling = True
        else:
            self.scrolling = False

        self.select_emojis = [f"{i+1}\N{combining enclosing keycap}" for i in range(num_selections)]

        self.control_emojis = [
            ('\N{BLACK LEFT-POINTING TRIANGLE}', self.previous_page),
            ('\N{BLACK RIGHT-POINTING TRIANGLE}', self.next_page),
            ('❌', self.stop_scrolling),
        ]

        self.timeout = 30
        self.args = None
        self.control_input = False

        self.add_page_indicator(self.localizer, "{queue.pageindicator}")



    async def scroll(self, page):
        if page < 0 or page >= len(self.pages):
            return
        self.current_page = page
        await self.message.edit(embed=self.pages[page])

    async def next_page(self):
        await self.scroll(self.current_page + 1)

    async def previous_page(self):
        await self.scroll(self.current_page - 1)

    async def stop_scrolling(self):
        self.scrolling = False
        await self.message.clear_reactions()

    def react_check(self, reaction, user):
        if user is None or user.id != self.author.id:
            return False

        if reaction.message.id != self.message.id:
            return False

        for i, emoji in enumerate(self.select_emojis):
            if emoji == reaction.emoji:
                choice = i + self.current_page * self.num_selections
                if choice >= len(self.selections):
                    return True
                self.match = self.selections[choice][1]
                self.args = self.selections[choice][2]
                return True

        for (emoji, func) in self.control_emojis:
            if reaction.emoji == emoji:
                self.match = func
                self.control_input = True
                return True
        return False


    async def send(self):
        self.current_page = 0
        # No embeds to scroll through
        if not self.pages:
            return
        if not self.scrolling:
            return await self.channel.send(embed=self.pages[0])

        self.message = await self.channel.send(embed=self.pages[0])
        for reaction in itertools.chain(self.select_emojis, list(zip(*self.control_emojis))[0]):
            await self.message.add_reaction(reaction)

    async def start_scrolling(self):
        result = None
        if not self.scrolling:
            await self.send()
        else:
            self.bot.loop.create_task(self.send())

        while self.scrolling:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=self.react_check, timeout=self.timeout)
            except asyncio.TimeoutError:
                self.scrolling = False
                try:
                    await self.message.clear_reactions()
                except:
                    pass
                finally:
                    break

            try:
                await self.message.remove_reaction(reaction, user)
            except:
                pass
            if self.match:
                if inspect.iscoroutinefunction(self.match):
                    if self.args:
                        result = await self.match(*self.args)
                    else:
                        result = await self.match()
                else:
                    if self.args:
                        result = self.match(*self.args)
                    else:
                        result = self.match()

            if self.terminate_on_select and not self.control_input:
                await self.message.clear_reactions()
                break
            self.match = None
            self.args = None
            self.control_input = False

        return self.message, self.pages[self.current_page], result