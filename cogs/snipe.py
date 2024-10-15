from discord.ext import commands
import discord
from typing import Optional
from discord import app_commands
from utils import PaginationView
import time

class Snipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages = {}
        self.edited_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild and not message.author.bot:
            if message.guild.id not in self.deleted_messages:
                self.deleted_messages[message.guild.id] = []
            self.deleted_messages[message.guild.id].append((message, discord.utils.utcnow()))
            if len(self.deleted_messages[message.guild.id]) > 8:
                self.deleted_messages[message.guild.id].pop(0)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild and not before.author.bot:
            if before.guild.id not in self.edited_messages:
                self.edited_messages[before.guild.id] = []
            self.edited_messages[before.guild.id].append((before, after))
            if len(self.edited_messages[before.guild.id]) > 8:
                self.edited_messages[before.guild.id].pop(0)

    @commands.hybrid_group(name="snipe", fallback="deleted")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(count="Number of messages to snipe (default: 1, max: 8)")
    async def snipe(self, ctx, count: int = 1):
        """Snipe the last deleted message(s) in the server"""
        await self._snipe_deleted(ctx, min(count, 8))

    @snipe.command(name="edited")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(count="Number of edited messages to show (default: 1, max: 8)")
    async def snipe_edited(self, ctx, count: int = 1):
        """Shows info about the last edited message(s)"""
        count = min(count, 8)
        if not self.edited_messages.get(ctx.guild.id):
            await ctx.send("No edited messages found.")
            return

        edited_messages = self.edited_messages[ctx.guild.id][-count:]
        embeds = []
        for before, after in reversed(edited_messages):
            embed = discord.Embed(color=discord.Color.dark_grey())
            embed.description = f"✏️ Message edited by {before.author.mention} in {before.channel.mention} at <t:{int(after.edited_at.timestamp())}:T>\n\n"
            embed.description += f"Before: ||{before.content[:1024] or 'None'}||\n"
            embed.description += f"After: {after.content[:1024] or 'None'}"

            if before.attachments:
                embed.description += f"\n\nAttachments: {', '.join([f'[{a.filename}]({a.url})' for a in before.attachments])}"

            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            view = PaginationView(embeds)
            view.message = await ctx.send(embed=embeds[0], view=view)

    @snipe.command(name="suiiki")
    @commands.has_permissions(manage_messages=True)
    async def snipe_suiiki(self, ctx):
        """Shows the last 3 deleted messages"""
        await self._snipe_deleted(ctx, 3)

    @snipe.command(name="user")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(user="The user to snipe messages from")
    async def snipe_user(self, ctx, user: discord.Member):
        """Shows the last deleted message of a specific user"""
        if not self.deleted_messages.get(ctx.guild.id):
            await ctx.send("No deleted messages found.")
            return

        user_messages = [msg for msg, _ in self.deleted_messages[ctx.guild.id] if msg.author == user]
        if not user_messages:
            await ctx.send(f"No deleted messages found for {user.mention}.")
            return

        message = user_messages[-1]
        await self._send_snipe_embed(ctx, message)

    async def _snipe_deleted(self, ctx, count: int):
        if not self.deleted_messages.get(ctx.guild.id):
            await ctx.send("No deleted messages found.")
            return

        messages = self.deleted_messages[ctx.guild.id][-count:]
        embeds = []
        for message, deleted_at in messages:
            embed = await self._create_snipe_embed(message, deleted_at)
            embeds.append(embed)

        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            view = PaginationView(embeds)
            view.message = await ctx.send(embed=embeds[0], view=view)

    async def _create_snipe_embed(self, message, deleted_at):
        embed = discord.Embed(color=discord.Color.dark_grey())
        embed.description = f"🚮 Message sent by {message.author.mention} deleted in {message.channel.mention}"
        embed.description += f" at <t:{int(deleted_at.timestamp())}:T>\n\n"
        embed.description += f"Content: {message.content[:1024]}" if message.content else "Content: None"

        if message.attachments:
            embed.description += f"\n\nAttachments: {', '.join([f'[{a.filename}]({a.url})' for a in message.attachments])}"

        if message.reference:
            try:
                ref_message = await message.channel.fetch_message(message.reference.message_id)
                embed.description += f"\n\nReplying to: [this message]({ref_message.jump_url})"
            except discord.NotFound:
                embed.description += "\n\nReplying to: [a deleted message]()"

        return embed

    async def _send_snipe_embed(self, ctx, message):
        embed = await self._create_snipe_embed(message, discord.utils.utcnow())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Snipe(bot))