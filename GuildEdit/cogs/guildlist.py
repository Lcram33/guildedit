import discord
from discord.ext import commands
import asyncio
from datetime import datetime


class GuildList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = bot.cogs["Settings"]

    #évite les injections SQL (oui, ça n'est pas la meilleur des méthodes, je le reconnaît.)
    def check_password(self, passwd: str, clean: bool = False):
        forbidden_terms = ['ADD', 'COLUMN', 'ALTER', 'TABLE', 'ALL', 'AND', 'ANY', 'AS', 'ASC', 'BACKUP', 'DATABASE',
                           'BETWEEN', 'CASE', 'CHECK', 'CONSTRAINT', 'CREATE', 'INDEX', 'OR', 'REPLACE', 'VIEW',
                           'PROCEDURE', 'UNIQUE', 'DEFAULT', 'DELETE', 'DESC', 'DISTINCT', 'DROP', 'EXEC', 'EXISTS',
                           'FOREIGN', 'KEY', 'FROM', 'FULL', 'OUTER', 'JOIN', 'GROUP', 'BY', 'HAVING', 'IN', 'INNER',
                           'INTO', 'SELECT', 'IS', 'NOT', 'NULL', 'LEFT', 'LIKE', 'LIMIT', 'ORDER', 'PRIMARY', 'RIGHT',
                           'ROWNUM', 'TOP', 'SET', 'TRUNCATE', 'UNION', 'UPDATE', 'VALUES', 'WHERE', 'add', 'column',
                           'alter', 'table', 'all', 'and', 'any', 'as', 'asc', 'backup', 'database', 'between', 'case',
                           'check', 'constraint', 'create', 'index', 'or', 'replace', 'view', 'procedure', 'unique',
                           'default', 'delete', 'desc', 'distinct', 'drop', 'exec', 'exists', 'foreign', 'key', 'from',
                           'full', 'outer', 'join', 'group', 'by', 'having', 'in', 'inner', 'into', 'select', 'is',
                           'not', 'null', 'left', 'like', 'limit', 'order', 'primary', 'right', 'rownum', 'top', 'set',
                           'truncate', 'union', 'update', 'values', 'where']
        for term in forbidden_terms:
            if term in passwd:
                if not clean:
                    return term
                passwd = passwd.replace(term, "")
        return None if not clean else passwd

    def format_datetime(self, date: datetime):
        week = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]
        day = week[int(date.strftime("%w"))]
        return date.strftime("Le %d/%m/%Y ({}) à %Hh%M".format(day))

    def get_time_spent(self, date: datetime):
        tdelta = datetime.now() - date
        strdelta = "unknown"

        if tdelta.days > 0:
            strdelta = "Il y a {} jours".format(str(tdelta.days))
            years = tdelta.days // 365
            days = tdelta.days % 365

            if years > 0:
                strdelta += " (approximativement "
                if years == 1:
                    strdelta += "1 an"
                else:
                    strdelta += "{} ans".format(str(years))

                if days == 0:
                    strdelta += ")"
                elif days == 1:
                    strdelta += ", 1 jour)"
                else:
                    strdelta += ", {} jours)".format(str(days))
        else:
            strdelta = "Il y a"
            hours = tdelta.seconds // 3600
            hours -= 2
            seconds = tdelta.seconds % 3600
            minutes = seconds // 60
            seconds = seconds % 60

            if hours > 0:
                strdelta += " {}h".format(str(hours))
            if minutes > 0:
                strdelta += " {}min".format(str(minutes))
            if seconds > 0:
                strdelta += " {}s".format(str(seconds))

        return strdelta

    @commands.command(aliases=['gs'])
    @commands.cooldown(3, 10 * 60, type=commands.BucketType.user)
    @commands.guild_only()
    async def guildset(self, ctx, *, id=None):
        if id is None:
            id = ctx.message.guild.id

        try:
            id = int(id)
        except Exception:
            await ctx.message.delete()
            embed = discord.Embed(title=":x: Veuillez entrer un id valide !", color=0xff0000)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        target = self.bot.get_guild(id)
        if target is None:
            await ctx.message.delete()
            embed = discord.Embed(title=":x: Serveur introuvable !", color=0xff0000)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        if target.id in self.settings.locked_guilds():
            embed = discord.Embed(title=":x: Les informations concernant ce serveur sont privées.", color=0x36393f)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        embed = discord.Embed(title="Informations sur un serveur",
                              description="{} ({})".format(target.name, str(target.id)), color=0xff8000)

        botinfo = ""
        entry = self.settings.get_entry(target.id)
        if entry is not None:
            if entry["identified"]:
                botinfo += ":white_check_mark: Recensée"
            else:
                botinfo += ":x: Recensée"
            if entry["password"] == "":
                botinfo += "\n:x: Mot de passe à l'entrée"
            else:
                botinfo += "\n:white_check_mark: Mot de passe à l'entrée"
            if entry["likesys"]:
                botinfo += "\n:white_check_mark: Système de like"
            else:
                botinfo += "\n:x: Système de like"
            if entry["banraidbots"]:
                botinfo += "\n:white_check_mark: Bannissement des bots détectés comme malveillants"
            else:
                botinfo += "\n{} Bannissement des bots détectés comme malveillants".format(
                    ":white_check_mark:⚠️" if entry["heuristic"] else ":x:")
            if entry["perms_lock"]:
                botinfo += "\n:white_check_mark: Restriction des permissions"
            else:
                botinfo += "\n:x: Restriction des permissions"

            if entry["heuristic"]:
                embed.set_footer(text="L'emoji ⚠️ indique que le mode heuristique est activé.")
        else:
            botinfo = ":x: Recensée\n:x: Mot de passe à l'entrée\n:x: Système de like\n:white_check_mark: Bannissement des bots détectés comme " \
                      "malveillants\n:white_check_mark: Restriction des permissions"

        embed.set_thumbnail(url=target.icon_url_as(format='jpg'))
        embed.add_field(name="Date de création", value="{}\n{}".format(self.format_datetime(target.created_at),
                                                                       self.get_time_spent(target.created_at)),
                        inline=False)
        embed.add_field(name="Propriétaire",
                        value="{}#{} ({})".format(target.owner.name, str(target.owner.discriminator),
                                                  str(target.owner.id)), inline=False)

        bcount = 0
        for m in target.members:
            if m.bot:
                bcount += 1
        bpercentage = round(100 * bcount / len(target.members))

        embed.add_field(name="Membres", value=":bust_in_silhouette: {} ({} %)\n:robot: {} ({} %)".format(
            str(len(target.members) - bcount), str(100 - bpercentage), str(bcount), str(bpercentage)), inline=True)
        embed.add_field(name="Région", value=str(target.region), inline=True)

        embed.add_field(name="Salons", value=":speech_left: {}\n:speaker: {}".format(str(len(target.text_channels)),
                                                                                     str(len(target.voice_channels))),
                        inline=True)
        embed.add_field(name="Rôles", value=":triangular_flag_on_post: {}".format(str(len(target.roles))), inline=True)

        bcount = "Permissions insuffisantes"
        try:
            bans = await target.bans()
            bcount = str(len(bans))
        except Exception:
            pass
        embed.add_field(name="Bannissments", value=bcount, inline=True)

        icount = "Permissions insuffisantes"
        try:
            invites = await target.invites()
            icount = str(len(invites))
        except Exception:
            pass
        embed.add_field(name="Invitations", value=icount, inline=True)

        emojis = ""
        animated_emojis = ""
        more = 0
        more_animated = 0
        if len(target.emojis) > 0:
            for e in target.emojis:
                if e.animated:
                    if len(animated_emojis) < 800:
                        animated_emojis += str(e)
                    else:
                        more_animated += 1
                else:
                    if len(emojis) < 800:
                        emojis += str(e)
                    else:
                        more += 1
            if more > 0:
                emojis += "\nEt {} autre(s).".format(str(more))
            if more_animated > 0:
                animated_emojis += "\nEt {} autre(s).".format(str(more_animated))
            if len(emojis) == 0:
                emojis = "Aucun emoji :rolling_eyes:"
            if len(animated_emojis) == 0:
                animated_emojis = "Aucun emoji :rolling_eyes:"
        else:
            emojis = "Aucun emoji :rolling_eyes:"
            animated_emojis = "Aucun emoji :rolling_eyes:"
        embed.add_field(name="Emojis", value=emojis, inline=False)
        embed.add_field(name="Emojis animés", value=animated_emojis, inline=False)

        embed.add_field(name="Paramètres du bot", value=botinfo, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def changepsw(self, ctx, *, password=None):
        await ctx.message.delete()

        if password is None:
            password = ""
        else:
            password = str(password)

        if len(password) > 30:
            response = await ctx.send(":x: Le mot de passe est trop long.")
            await asyncio.sleep(3)
            await response.delete()
            return

        if len(password) > 0:
            check = self.check_password(password)
            if type(check) == str:
                response = await ctx.send(":x: Le mot de passe ne peut pas contenir le mot `{}` !".format(check))
                await asyncio.sleep(5)
                await response.delete()
                return

        self.settings.edit_password(ctx.message.guild.id, password)
        if len(password) > 0:
            response = await ctx.send(":white_check_mark: Mot de passe changé !")
            await asyncio.sleep(3)
            await response.delete()
        else:
            response = await ctx.send(":white_check_mark: Mot de passe supprimé !")
            await asyncio.sleep(3)
            await response.delete()

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def hsguild(self, ctx):
        await ctx.send(self.settings.edit_identified(ctx.message.guild.id))

    @commands.command()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.user)
    async def join(self, ctx):
        if not isinstance(ctx.message.channel, discord.DMChannel):
            await ctx.send(":x: Cette commande ne s'effectue qu'en DM (afin d'éviter tout flood)")
            return

        content = ctx.message.content.replace(">join ", "")

        id = None
        password = ""
        if len(content) > 18:
            id, password = content.split(" ")
            id = int(id)
            password = str(password)
        else:
            id = int(content)

        target = self.bot.get_guild(id)
        if target is None:
            embed = discord.Embed(title=":x: Erreur", description="Le bot n'est pas sur ce serveur.", color=0xff8000)
            await ctx.send(embed=embed)
            return

        try:
            entry = self.settings.get_entry(id)

            if entry is None:
                embed = discord.Embed(title=":x: Erreur",
                                      description="Ce serveur n'est pas rejoignable, la fonctionnalité n'est pas activée.",
                                      color=0xff8000)
                await ctx.send(embed=embed)
                return

            if entry["identified"] == False:
                embed = discord.Embed(title=":x: Erreur",
                                      description="Ce serveur n'est pas rejoignable, un administrateur a désactivé la fonctionnalité.",
                                      color=0xff8000)
                await ctx.send(embed=embed)
                return

            if len(entry["password"]) > 0:
                if entry["password"] != password:
                    embed = discord.Embed(title=":x: Erreur",
                                          description="Vous devez entrer le bon mot de passe pour rejoindre ce serveur.",
                                          color=0xff8000)
                    await ctx.send(embed=embed)
                    return

            invite = await target.text_channels[0].create_invite(destination=target.text_channels[0], xkcd=True,
                                                                 max_uses=1, max_age=600)
            await ctx.send(str(invite))
        except Exception as e:
            await ctx.send(":x: Erreur : " + str(e))

    @commands.command()
    @commands.cooldown(1, 8 * 60, type=commands.BucketType.user)
    async def guildlist(self, ctx):
        if not isinstance(ctx.message.channel, discord.DMChannel):
            await ctx.send(":x: Cette commande ne s'effectue qu'en DM (afin d'éviter tout flood)")
            return

        totallen = 0
        content = ""
        for g in self.bot.guilds:
            entry = self.settings.get_entry(g.id)
            if entry is not None:
                if entry["identified"] == True:
                    newline = "**" + g.name + "** (" + str(g.id) + ")"
                    if entry["password"] != "":
                        newline += "*"
                    totallen += len(newline)
                    if len(content) + len(newline) + 1 > 2000:
                        await ctx.author.send(content)
                        content = ""
                        content += newline + chr(13)
                    else:
                        content += newline + chr(13)

        if len(content) > 0:
            await ctx.author.send(content)
        if totallen == 0:
            await ctx.author.send(":x: Liste vide !")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def likesys(self, ctx):
        result = self.settings.edit_likesys(ctx.message.guild.id)
        await ctx.send(result)
        if result.find("désactivé") == -1:
            result2 = await self.settings.get_like_channel(ctx.guild)
            if isinstance(result2, str):
                await ctx.send(content=result2)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def banraidbots(self, ctx):
        await ctx.send(self.settings.edit_ban_raidbots(ctx.guild.id))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def hmode(self, ctx):
        await ctx.send(self.settings.edit_heuristic(ctx.guild.id))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def lockperms(self, ctx):
        await ctx.send(self.settings.edit_perms_lock(ctx.guild.id))


def setup(bot):
    bot.add_cog(GuildList(bot))
