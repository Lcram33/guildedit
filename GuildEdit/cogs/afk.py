import discord
from discord.ext import commands
from datetime import datetime
from datetime import timedelta
import asyncio


class Afk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = bot.cogs["Database"]
        self.last_ping = []

    def datetime_to_str(self, date: datetime):
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def str_to_datetime(self, text: str):
        return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")

    def format_datetime(self, date: datetime):
        week = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]
        day = week[int(date.strftime("%w"))]
        return date.strftime("Le %d/%m/%Y ({}) à %Hh%M".format(day))

    def check_last_ping(self, ID: int):
        for entry in self.last_ping:
            if entry["ID"] == ID:
                if datetime.now() - entry["date"] < timedelta(days=0, hours=0, minutes=30, seconds=0):
                    return True
                else:
                    self.last_ping.remove(entry)
        newentry = {
            "ID": ID,
            "date": datetime.now()
        }
        self.last_ping.append(newentry)
        return False

    def remove_afk(self, ID: int):
        return  self.database.delete_request("guildedit", "afk", ("user_id",), (ID))

    def add_afk(self, ID: int, until, reason: str, logpings: bool):
        return self.database.insert_request("guildedit", "afk", ("user_id", "until", "reason", "log_pings"), (ID, self.datetime_to_str(until), reason, logpings))

    def is_afk(self, ID: int):
        return True if self.database.select_request("guildedit", "afk", "*", ("user_id",), (ID)) is not None else False

    def get_ending_date(self, duration: str):
        errormessage = "**:x: Veuillez entrer une durée correcte (D pour des jours, H pour des heures, M pour des " \
                                                            "minutes) !\n*Ex : 3D -> 3j, 4M->4min*\nCommande annulée**"
        if not duration.find("D") > -1 and not duration.find("H") > -1 and not duration.find("M") > -1:
            return errormessage

        tdelta = None
        try:
            if duration.find("D") > -1:
                d = int(duration.replace("D", ""))
                if d > 14:
                    return "**:x: Vous ne pouvez pas être afk plus de deux semaines !\nCommande annulée**"
                tdelta = timedelta(days=d, hours=0, minutes=0, seconds=0)
            elif duration.find("H") > -1:
                h = int(duration.replace("H", ""))
                if h > 24:
                    return "**:x: Pour un afk de plus d'un jour, entrez `<nombres de jours>D`.\nCommande annulée**"
                tdelta = timedelta(days=0, hours=h, minutes=0, seconds=0)
            elif duration.find("M") > -1:
                m = int(duration.replace("M", ""))
                if m > 60:
                    return "**:x: Pour un afk de plus d'une heure, entrez `<nombres d'heures>H`.\nCommande annulée**"
                tdelta = timedelta(days=0, hours=0, minutes=m, seconds=0)
        except Exception:
            return errormessage

        return datetime.now() + tdelta

    def afk_end_in(self, date: datetime):
        tdelta = date - datetime.now()
        strdelta = "dans "
        tminutes = tdelta.seconds // 60

        days = tdelta.days
        hours = tminutes // 60
        minutes = tminutes % 60

        if days > 0:
            strdelta += "{}j ".format(str(days))

        if hours > 0:
            strdelta += "{}h ".format(str(hours))

        if minutes > 0:
            strdelta += "{}min ".format(str(minutes))

        return strdelta[:-1]

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.DMChannel):
            return

        if message.author.bot:
            return

        if len(message.mentions) == 0:
            return

        for m in message.mentions:
            isafk = self.is_afk(m.id)
            if isafk:
                if isafk["until"] < datetime.now():
                    self.remove_afk(m.id)
                    return

                result = self.check_last_ping(message.author.id)
                if result:
                    return

                embed = discord.Embed(
                    title=":warning: **{}#{} est actuellement AFK !**".format(m.name, str(m.discriminator)),
                    description="""
**Raison :** {}
**Ne sera plus AFK :** {} ({})
                """.format(isafk["reason"] if isafk["reason"] != "aucune" else "Aucune raison fournie.",
                           self.format_datetime(isafk["until"]), self.afk_end_in(isafk["until"])), color=0xff0000)
                await message.channel.send(content=message.author.mention, embed=embed)

                if isafk["logpings"]:
                    embed = discord.Embed(title="Nouvelle mention", color=0xff0000)
                    embed.set_thumbnail(url="https://discordemoji.com/assets/emoji/ping.png")
                    embed.add_field(name="Utilisateur",
                                    value="<@{}> ({}#{}, {})".format(str(message.author.id), message.author.name,
                                                                     str(message.author.discriminator),
                                                                     str(message.author.id)), inline=False)
                    embed.add_field(name="Contenu du message", value=message.content, inline=False)
                    embed.add_field(name="Serveur",
                                    value="**{}** ({})".format(message.guild.name, str(message.guild.id)), inline=False)
                    embed.add_field(name="Salon",
                                    value="<#{}> (#{}, {})".format(str(message.channel.id), message.channel.name,
                                                                   str(message.channel.id)), inline=False)
                    embed.add_field(name="Date", value=self.format_datetime(datetime.now()), inline=False)
                    await m.send(embed=embed)

    @commands.command()
    @commands.cooldown(2, 5 * 60, type=commands.BucketType.user)
    async def afk(self, ctx):
        if self.is_afk(ctx.author.id):
            self.remove_afk(ctx.author.id)
            await ctx.send("**:white_check_mark: AFK retiré!**")
            return

        def check(m):
            return m.author == ctx.author

        embed = discord.Embed(title="Définir votre AFK",
                              description="Veuillez dans un premier temps entrer une durée (votre afk sera retiré après cette durée)",
                              color=0x004080)
        embed.set_thumbnail(url="https://image.flaticon.com/icons/svg/217/217187.svg")
        embed.add_field(name="Format",
                        value="- Pour indiquer un nombre de jours : `<nombre de jours>D`\n- Pour indiquer un nombre d'heures : `<nombre d'heures>H`\n- Pour indiquer un nombre de minutes : `<nombre de minutes>M`",
                        inline=True)
        embed.set_footer(text="Remarque : si vous ne répondez pas dans 1min, la commande sera annulée.")
        msg1 = await ctx.send(embed=embed)

        duration = None
        try:
            duration = await self.bot.wait_for('message', check=check, timeout=60)
            duration = duration.content
        except asyncio.TimeoutError:
            await msg1.edit(content=":x: **Temps écoulé.**", embed=None)
            return

        duration = self.get_ending_date(duration)
        if isinstance(duration, str):
            await ctx.send(duration)
            return

        embed2 = discord.Embed(title="Définir votre AFK",
                               description="Veuillez ensuite donner une raison (elle sera affichée si l'on vous mentionne). Pour ne pas en donner, entrer `aucune`.",
                               color=0x004080)
        embed2.set_thumbnail(url="https://image.flaticon.com/icons/svg/217/217187.svg")
        embed2.set_footer(text="Remarque : si vous ne répondez pas dans 1min, la commande sera annulée.")
        msg2 = await ctx.send(embed=embed2)

        reason = None
        try:
            reason = await self.bot.wait_for('message', check=check, timeout=60)
            reason = reason.content
            reason = reason.replace("@everyone", "X")
            reason = reason.replace("@here", "X")
            reason = reason.replace("discord.gg/", "X")
        except asyncio.TimeoutError:
            await msg2.edit(content=":x: **Temps écoulé.**", embed=None)
            return

        embed3 = discord.Embed(title="Définir votre AFK",
                               description="Pour finir, veuillez indiquer par `oui` ou par `non` si vous souhaitez recvoir un mp à chaque ping, de manière à en conserver une trace (le spam étant ignoré).",
                               color=0x004080)
        embed3.set_thumbnail(url="https://image.flaticon.com/icons/svg/217/217187.svg")
        embed3.set_footer(text="Remarque : si vous ne répondez pas dans 1min, la commande sera annulée.")
        msg3 = await ctx.send(embed=embed3)

        ping = None
        try:
            ping = await self.bot.wait_for('message', check=check, timeout=60)
            ping = ping.content
        except asyncio.TimeoutError:
            await msg3.edit(content=":x: **Temps écoulé.**", embed=None)
            return
        if ping != "oui" and ping != "non":
            await msg3.edit(content=":x: **Veuillez entrer `oui` ou `non`.\nCommande annulée**", embed=None)
            return
        ping = True if ping == "oui" else False

        self.add_afk(ctx.author.id, duration, reason, ping)
        await ctx.send("**:white_check_mark: AFK défini !**")


def setup(bot):
    bot.add_cog(Afk(bot))
