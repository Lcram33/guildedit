from datetime import datetime
import discord
from discord.ext import commands


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = bot.cogs["Settings"]

    def format_datetime(self, date: datetime):
        week = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]
        day = week[int(date.strftime("%w"))]
        return date.strftime("Le %d/%m/%Y ({}) à %Hh%M".format(day))

    def is_admin():
        def predicate(ctx):
            if str(ctx.author.id) in ctx.cog.bot.config["Admin"]:
                return True
            raise commands.DisabledCommand()

        return commands.check(predicate)

    async def update_status(self):
        if self.bot.rmode:
            await self.bot.change_presence(
                activity=discord.Game(name=">help & >infos | {} serveurs".format(str(len(self.bot.guilds))), type=1),
                status=discord.Status.idle)
        if self.bot.mmode:
            await self.bot.change_presence(activity=discord.Game(name="Mode maintenance, bot indisponible.", type=0),
                                           status=discord.Status.do_not_disturb)
        if not self.bot.rmode and not self.bot.mmode:
            new_message = ">help & >infos | {} serveurs".format(str(len(self.bot.guilds)))
            await self.bot.change_presence(
                activity=discord.Streaming(name=new_message, url="https://www.twitch.tv/lcram33"),
                status=discord.Status.online)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])
        if member.guild == supguild:
            user = supguild.get_member(member.id)
            if member.bot:
                brole = discord.utils.get(supguild.roles, name='Bot🤖')
                await user.add_roles(brole)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if isinstance(reaction.message.channel, discord.DMChannel):
            return

        if reaction.message.author.bot:
            return

        if reaction.message.channel.name == "fil-des-likes":
            return

        if reaction.emoji != "❤":
            return

        if reaction.count != 15:
            return

        if not self.settings.like_system_enabled(reaction.message.guild.id):
            return

        result = await self.settings.get_like_channel(reaction.message.guild)
        if isinstance(result, str):
            await reaction.message.channel.send(content=result)
            return

        ilist = []
        attlist = ""
        for a in reaction.message.attachments:
            attlist += a.url + "\n"
            if a.url.endswith(".jpg") or a.url.endswith(".png"):
                ilist.append(a.url)

        if attlist == "":
            attlist = "Pas de fichier join"

        embed = discord.Embed(title="Contenu", description=reaction.message.content, color=0xf15f3a)
        embed.set_thumbnail(
            url="https://assets-auto.rbl.ms/653c82493ada18a6df47aad341eb52741873d6db8c8fbea91d88735302f0cedc")
        embed.add_field(name="Fichiers joints", value=attlist, inline=False)
        embed.set_footer(
            text="Message de {}#{}".format(reaction.message.author.name, str(reaction.message.author.discriminator)))
        await result.send(embed=embed)

        if len(ilist) > 0:
            for i in ilist:
                try:
                    embedi = discord.Embed(title="Image du message précédent", color=0xf15f3a)
                    embedi.set_thumbnail(url=i)
                    await result.send(embed=embedi)
                except Exception:
                    pass

        await reaction.message.clear_reactions()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])
        for member in guild.members:
            if member.guild_permissions.administrator or member == guild.owner:
                done = False

                try:
                    await supguild.fetch_ban(member)

                    try:
                        await member.send(
                            ":x: Vous êtes banni de **{}**. Vous ne pouvez en conséquence ni ajouter ce bot, ni l'utiliser.".format(
                                str(supguild.name)))
                    except Exception:
                        pass

                    await guild.leave()
                    embed = discord.Embed(title="Tentative d'un ajout au serveur bloquée",
                                          description=guild.name + " (" + str(guild.id) + ")", color=0xff0000)
                    embed.set_thumbnail(url=guild.icon_url_as(format='jpg'))
                    embed.add_field(name="Membre banni",
                                    value=member.name + "#" + str(member.discriminator) + " (" + str(member.id) + ")",
                                    inline=False)
                    embed.add_field(name="Banni du serveur", value=str(supguild.name), inline=False)
                    lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
                    await lChan.send(embed=embed)
                    return
                except Exception:
                    pass

        member_that_added = ""
        member_to_send = guild.owner
        try:
            async for a in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                member_to_send = guild.get_member(a.user.id)
                member_that_added = "{}#{} ({})".format(a.user.name, str(a.user.discriminator), str(a.user.id))
        except Exception:
            pass

        lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
        embed = discord.Embed(title="Serveur rejoint", description=guild.name + " (" + str(guild.id) + ")",
                              color=0x008000)
        embed.set_thumbnail(url=guild.icon_url_as(format='jpg'))
        if len(member_that_added) > 0:
            embed.add_field(name="Ajouté par", value=member_that_added, inline=False)
        embed.add_field(name="Propriétaire", value=guild.owner.name + "#" + str(guild.owner.discriminator) + " (" + str(
            guild.owner.id) + ")", inline=False)
        embed.add_field(name="Nombre de membres", value=str(len(guild.members)), inline=False)
        await lChan.send(embed=embed)

        await self.update_status()

        jembed = discord.Embed(title="☑️ Merci de m'avoir ajouté à {} !".format(guild.name),
                               description="Faites `>help` pour prendre connaissances des commandes par catégories.",
                               color=0x0000ff)
        jembed.set_thumbnail(url="https://cdn1.iconfinder.com/data/icons/flat-business-icons/128/server-512.png")
        jembed.add_field(name="Liens utiles", value="""
Inviter le bot : `>invite`
[Serveur de support]({})
[Site](https://guildedit.wordpress.com/)
        """.format(self.bot.config["links"]["support"]), inline=False)
        try:
            await member_to_send.send(embed=jembed)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
        embed = discord.Embed(title="Serveur quitté", description=guild.name + " (" + str(guild.id) + ")",
                              color=0xff0000)
        embed.set_thumbnail(url=guild.icon_url_as(format='jpg'))
        embed.add_field(name="Propriétaire", value=guild.owner.name + "#" + str(guild.owner.discriminator) + " (" + str(
            guild.owner.id) + ")", inline=False)
        embed.add_field(name="Nombre de membres", value=str(len(guild.members)), inline=False)
        await lChan.send(embed=embed)
        await self.update_status()
        self.settings.remove_entry(guild.id)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if type(channel) == discord.TextChannel and channel.name == "ge-news":
            embed = discord.Embed(title="✅ Merci !",
                                  description="Une actualité proposée par le créateur du bot sera occasionnellement envoyée dans ce salon.\nSi vous ne souhaitez plus recevoir cette actualité, supprimez tout simplerment ce salon.",
                                  color=0x008040)
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Events(bot))
