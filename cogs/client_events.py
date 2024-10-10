import discord
from discord.ext import commands
from discord import app_commands
from utils.timeparsetool import convert_seconds
from datetime import datetime, timezone
from typing import Optional
import calendar
from db import db
import time



class ClientEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    


async def setup(bot):
    await bot.add_cog(ClientEvents(bot))
