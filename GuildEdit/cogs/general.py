import asyncio
import random
from datetime import datetime
import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_ping = None

# les images ci-dessous ne sont absolument pas de moi, et tout crédit revient à leurs auteurs.
        self.settings = bot.cogs['Settings']
        self.public_names = ["Baloon guild", "Cake guild", "Party guild", "Spaceship guild", "Rainbow guild",
                             "Fire guild", "Lightning guild", "Snow guild"]
        self.public_icons = [
            "https://cdn3.iconfinder.com/data/icons/christmas-enjoyment-monocolor-white-circle-multico/2048/708_-_Balloons-512.png",
            "http://icons.iconarchive.com/icons/flat-icons.com/flat/512/Cake-icon.png",
            "http://icons.iconarchive.com/icons/webalys/kameleon.pics/512/Party-Poppers-icon.png",
            "http://icons.iconarchive.com/icons/google/noto-emoji-travel-places/512/42598-rocket-icon.png",
            "http://icons.iconarchive.com/icons/google/noto-emoji-travel-places/512/42682-rainbow-icon.png",
            "http://icons.iconarchive.com/icons/google/noto-emoji-travel-places/512/42697-fire-icon.png",
            "http://icons.iconarchive.com/icons/google/noto-emoji-travel-places/512/42689-high-voltage-icon.png",
            "http://icons.iconarchive.com/icons/google/noto-emoji-travel-places/512/42691-snowflake-icon.png"]
        self.gaming_icons = [] #il faudra en trouver !
        self.gaming_names = ["The Dynamic Sharks", "Buzzing Flashers", "Junk Yellow Epidemic", "Big Test Icicles",
                             "Terrifying Sweat Hurricanes", "Laughing Goats", "Victorious Destroyers",
                             "The Silent Squirrels", "Elfin Penguins", "The Stark Toucans", "Les Koalas Sensationnels",
                             "Les Requins Fougueux", "Les Trolls Nobles", "Les Extraterrestres Tranquilles",
                             "Les Phacocheres Caches", "Les Ratons Fantastiques"]
        self.pub_icons = ["https://www.wptouch.com/wp-content/themes/wptouch4site/woocommerce/img/icons/basic-ads.png",
                          "https://www.pngkit.com/png/full/231-2319167_print-advertising-icon-print-media-advertising-icon.png",
                          "https://www.shareicon.net/data/128x128/2016/08/18/809311_multimedia_512x512.png"]

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

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(create_instant_invite=True)
    @commands.cooldown(2, 10 * 60, type=commands.BucketType.guild)
    async def cinvite(self, ctx, uses_amount, duration="INF", channel: discord.TextChannel = None):
        try:
            uses_amount = int(uses_amount)
        except Exception:
            await ctx.send(":x: **Veuillez entrer un nombre !**")
            return

        if channel is None:
            channel = ctx.message.channel

        if duration.find("H") == -1 and duration.find("M") == -1 and duration.find("S") == -1 and duration != "INF":
            await ctx.send(":x: **Veuillez entrer une durée valide !**")
            return

        if duration == "INF":
            duration = 0

        if type(duration) == str and duration.find("H") > -1:
            try:
                duration = 3600 * int(duration.replace("H", ""))
            except Exception:
                await ctx.send(":x: **Veuillez entrer une durée valide !**")
                return

        if type(duration) == str and duration.find("M") > -1:
            try:
                duration = 60 * int(duration.replace("M", ""))
            except Exception:
                await ctx.send(":x: **Veuillez entrer une durée valide !**")
                return

        if type(duration) == str and duration.find("S") > -1:
            try:
                duration = int(duration.replace("S", ""))
            except Exception:
                await ctx.send(":x: **Veuillez entrer une durée valide !**")
                return

        if duration > 86400:
            await ctx.send(":x: **La durée ne doit pas dépasser 1j. Laisser vide pour une invitation infinie.**")
            return

        if uses_amount > 100:
            await ctx.send(":x: **Le nombre d'utilisations ne doit pas dépasser 100.**")
            return

        try:
            invite = await channel.create_invite(max_age=duration, max_uses=uses_amount,
                                                 reason="Créée par {}#{} ({}) : {} utilisations, dure {}s.".format(
                                                     ctx.author.name, str(ctx.author.discriminator), str(ctx.author.id),
                                                     str(uses_amount), str(duration)))
            await ctx.send(str(invite))
        except Exception as e:
            await ctx.send(":x: **Impossible de créer l'invitation :** `{}`".format(str(e)))

    @commands.command()
    @commands.cooldown(3, 10 * 60, type=commands.BucketType.user)
    async def ping(self, ctx):
        new_ping = round(self.bot.latency * 1000) + 1
        old_ping = self.last_ping
        self.last_ping = new_ping

        embed = discord.Embed(title=":ping_pong: **Pong ! `{}` ms**".format(str(new_ping)), color=0x36393f)
        if old_ping is not None:
            percent = round(100 - 100 * old_ping / new_ping, 2)
            if percent < 0:
                percent = "↘️" + str(percent) + "%"
            elif percent == 0:
                percent = "🔄" + str(percent) + "%"
            else:
                percent = "🔼+" + str(percent) + "%"
            embed.set_footer(text="Ping précédent : {} ms {}".format(str(old_ping), percent))
        response = await ctx.send(embed=embed)

        try:
            await ctx.message.delete()
        except Exception:
            pass

        await asyncio.sleep(6)
        await response.delete()

    @commands.command(aliases=['ui'])
    @commands.guild_only()
    @commands.cooldown(3, 10 * 60, type=commands.BucketType.user)
    async def userinfos(self, ctx, *, member=None):
        user = None
        if len(ctx.message.mentions) > 0:
            member = ctx.message.mentions[0]
        else:
            if member is not None and not isinstance(member, discord.Member):
                try:
                    member = int(member)
                except Exception:
                    await ctx.send(
                        ":x: Veuillez entrer un ID, mentionner un utilisateur, ou laisser vide pour votre compte.")
                    return
                intm = member
                member = ctx.message.guild.get_member(intm)
                if member is None:
                    try:
                        user = await self.bot.fetch_user(intm)
                    except Exception:
                        await ctx.send(":x: Impossible de trouver cet utilisateur !")
                        return
            if member is None:
                member = ctx.message.guild.get_member(ctx.author.id)

        ecolor = 0x008000
        footer = ""
        if user is not None:
            if str(user.id) in self.bot.config["Staff"]:
                footer = "Cet utilisateur est staff sur le bot"
                ecolor = 0xff8000
            if str(user.id) in self.bot.config["Admin"]:
                footer = "Cet utilisateur est administrateur sur le bot"
                ecolor = 0xff0000
        else:
            if str(member.id) in self.bot.config["Staff"]:
                footer = "Ce membre est staff sur le bot"
                ecolor = 0xff8000
            if str(member.id) in self.bot.config["Admin"]:
                footer = "Ce membre est administrateur sur le bot"
                ecolor = 0xff0000

        embed = None
        if user is not None:
            embed = discord.Embed(title="Utilisateur", description="{}#{}".format(user.name, str(user.discriminator)),
                                  color=ecolor)
        else:
            embed = discord.Embed(title="Membre", description="{}#{}".format(member.name, str(member.discriminator)),
                                  color=ecolor)
        if user is not None:
            embed.set_thumbnail(url=user.avatar_url_as(format='gif' if user.is_avatar_animated() else 'jpg'))
        else:
            embed.set_thumbnail(url=member.avatar_url_as(format='gif' if member.is_avatar_animated() else 'jpg'))
        if user is not None:
            embed.add_field(name="Création du compte", value="{}\n{}".format(self.format_datetime(user.created_at),
                                                                             self.get_time_spent(user.created_at)),
                            inline=True)
        else:
            embed.add_field(name="Création du compte", value="{}\n{}".format(self.format_datetime(member.created_at),
                                                                             self.get_time_spent(member.created_at)),
                            inline=True)
        if user is not None:
            embed.add_field(name="ID", value=str(user.id), inline=True)
        else:
            embed.add_field(name="ID", value=str(member.id), inline=True)
        if user is None:
            embed.add_field(name="A rejoint le", value="{}\n{}".format(self.format_datetime(member.joined_at),
                                                                       self.get_time_spent(member.joined_at)),
                            inline=True)
        if user is not None:
            embed.add_field(name="Bot", value="Oui" if user.bot else "Non", inline=True)
        else:
            embed.add_field(name="Bot", value="Oui" if member.bot else "Non", inline=True)

        guild_count = 0
        if user is None:
            for g in self.bot.guilds:
                if g.get_member(member.id) is not None:
                    guild_count += 1
        else:
            for g in self.bot.guilds:
                if g.get_member(user.id) is not None:
                    guild_count += 1
        embed.add_field(name="Serveurs en commun", value=str(guild_count), inline=False)

        if footer != "":
            embed.set_footer(text=footer)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.user)
    async def invite(self, ctx):
        embed = discord.Embed(title="Inviter le bot",
                              description="[Lien]({})\nVous pouvez également utiliser le qr code.".format(self.bot.config["links"]["botInvite"]), color=0x36393f)
        embed.add_field(name="⚠️Attention !", value="Vérifiez bien la présence de l'étiquette \"Bot certifié\" après l'ajout du bot. Si ce n'est pas le cas, ce n'est pas le bot officiel, il faut l'exclure au plus vite !")
        embed.set_footer(text="Remarque : tous les liens du bot sont dans `>help`.")
        embed.set_thumbnail(url=self.bot.config["links"]["qrcode"])
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.user)
    async def infos(self, ctx):
        supguild = self.bot.get_guild(int(self.bot.config["supportGuild"]["ID"]))
        lcram = supguild.get_member(303191513372950529)
        m_count = 0
        maxuser = 0
        maxuser_guildname = None
        for g in self.bot.guilds:
            m_count += len(g.members)
            if len(g.members) > maxuser:
                maxuser = len(g.members)
                maxuser_guildname = g.name
        auc = round(m_count / len(self.bot.guilds))

        embed = discord.Embed(title="Infos", description="""
Version : {}
Propriétaire : {}#{} (303191513372950529)
Contact : contact.guildedit@gmail.com
[Icône du bot (liberté d'usage)](https://www.iconfinder.com/icons/1287513/database_hosting_internet_rack_server_storage_icon)

__Partenaires :__

Bots :
X

Serveur :
X
        """.format(self.bot.version, lcram.name, str(lcram.discriminator)), color=0x36393f)
        embed.set_thumbnail(url="https://cdn1.iconfinder.com/data/icons/flat-business-icons/128/server-512.png")
        embed.set_footer(text="Les liens utiles sont dans `>help` et `>invite`")

        try:
            await ctx.author.send(embed=embed)

            await ctx.message.add_reaction(emoji="📩")
        except Exception as e:
            await ctx.send(
                ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))

    @commands.command()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.user)
    async def help(self, ctx):
        content = """
__Les commandes par catégories :__

Générales : **>helpgeneral**
Modération : **>helpmoderation**
Gestion du serveur : **>helpguild**
Paramétrage du bot : **>helpsettings**
Backup : **>helpbackup**
        """
        if str(ctx.author.id) in self.bot.config["Staff"]:
            content += "Outils du bot (commandes réservées aux staffs) : **>helpstaff**"
        if str(ctx.author.id) in self.bot.config["Admin"]:
            content += "\nGestion du bot (commandes réservées aux admins) : **>helpadmin**"
        content += "\n\nInviter le bot : **>invite**\n\nPour recevoir une actualité occasionnelle (concernant discord) proposée par le créateur du bot, créez simplement un salon textuel avec le nom `ge-news`."

        embed = discord.Embed(title="Commandes", description=content, color=0x36393f)
        embed.add_field(name="Liens", value="""
[Serveur de support]({})
[Site](https://guildedit.wordpress.com/)
[Faire un don](http://paypal.me/lcram33)
        """.format(self.bot.config["links"]["support"]), inline=False)
        embed.set_thumbnail(url="https://cdn1.iconfinder.com/data/icons/flat-business-icons/128/server-512.png")
        embed.set_footer(text="Remarque : si une commande est en cooldown, le bot réagira à votre message avec ⏰")

        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction(emoji="📩")
        except Exception as e:
            await ctx.send(
                ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))

    @commands.command()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.user)
    async def helpgeneral(self, ctx):
        embed = discord.Embed(title="Commandes", description="""
__Catégorie : Générales__

**>infos** : Les infos sur le bot. Cooldown : 5min/user.
**>ping** : Donne la latence du bot. Cooldown : 3 en 10min/user.
**>afk** : Définir votre afk. Cooldown : 2 en 5min/user.
**>userinfos (ID/mention)** *(ou ui)* : Informations sur l'utilisateur. Si l'ID n'est pas fourni, donne les infos de l'auteur du message. Cooldown : 3 en 10min/user.
**>health** : Vérifie les permissions du bot, et la position de son rôle, de manière à prévenir des bugs. Cooldown : 3 en 10min/serveur.
**>createguild (empty, personnal, public, gaming, pub, community)** : Crée un serveur. Selon le mot clé, configure le serveur automatiquement lorsque vous le rejoignez. Cooldown : 8min/user.
**>randominvite** : Invitation aléatoire pour un serveur recensé (10 utilisations, 5min). Cooldown : 3 en 15min/user.
**>randomguild** : Serveur aléatoire sur lequel est le bot. Cooldown : 3 en 10min/user.
**>randomuser** : Utilisateur aléatoire. Cooldown : 3 en 10min/user.
**>guildlist** : Affiche la liste des serveurs. Uniquement en mp. Cooldown : 8min/user.
**>guildset (ID)** : Donne les infos disponibles sur un serveur. Si aucun ID n'est donné, donne celles du serveur actuel. Cooldown : 3 en 10min/user.
**>join (ID) (mot de passe, optionnel)** : Donne une invitation au serveur. Si aucun mot de passe (pas de * après le nom du serveur), s'arrêter à l'ID. Cooldown : 2min/user.
**>cinvite (utilisations) (durée : INF pour infinie, S pour secondes, M pour minutes, H pour heures) (mention salon)** : Crée une invitation avec les paramètres spécifiés. Cooldown : 2 en 10min/serveur.
        """, color=0x36393f)
        embed.set_footer(text="Remarque : si une commande est en cooldown, le bot réagira à votre message avec ⏰")

        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction(emoji="📩")
        except Exception as e:
            await ctx.send(
                ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))

    @commands.command()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.user)
    async def helpmoderation(self, ctx):
        embed = discord.Embed(title="Commandes", description="""
__Catégorie : Modération__

**>kick @mention1 @mention2 ... @mention30 (raison)** : Expulse les personnes mentionnées avec la raison donnée. Cooldown : 2min/serveur.
**>ban @mention1 @mention2 ... @mention30 (raison)** : Bannit les personnes mentionnées avec la raison donnée. Cooldown : 2min/serveur.
**>banid ID1 ID2 ... ID30 (raison)** : Bannit les personnes dont l'ID a été donné avec la raison indiquée. __Les personnes ne doivent pas être sur le serveur__ (utiliser >ban dans ce cas). Cooldown : 2min/serveur.
**>isbanned (ID)** : Vérifie si un utilisateur est banni du serveur, et indique la raison si cela est le cas. Permission : Bannir des membres. Cooldown : 3 en 3min/serveur.
**>unban (ID)** : Révoque le bannissement d'ID spécifié. Permission : Bannir des membres. Cooldown : 3 en 3min/serveur.
**>masskick (nom)** : Expulse tous les membres de nom donné. Permission : Expulser des membres. Cooldown : 2min/serveur.
**>massban (nom)** : Bannit tous les membres de nom donné. Permission : Bannir des membres. Cooldown : 2min/serveur.
        """, color=0x36393f)
        embed.set_footer(text="Remarque : si une commande est en cooldown, le bot réagira à votre message avec ⏰")

        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction(emoji="📩")
        except Exception as e:
            await ctx.send(
                ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))

    @commands.command()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.user)
    async def helpguild(self, ctx):
        embed = discord.Embed(title="Commandes", description="""
__Catégorie : Gestion du serveur__

**>clone (ID serveur cible)** : Copie le serveur où est executée la commande sur le serveur d'ID donné (cible). Attention, cela supprime tous les salons/rôles du serveur cible. Conditions : être administrateur sur le serveur à cloner et propriétaire sur le 2e serveurs. Cooldown : 15min/serveur.
**>configguild (emtpy, personnal, public, gaming, pub, community) (ID)** : Selon le mot clé, configure le serveur d'ID donné (laisser vide pour le serveur où la commande est effectuée). Attention, cela supprime tout les salon/rôle sur le serveur indiqué ! Permission : Administrateur. Cooldown : 10min/user.
**>addemoji (nom) (lien d'image)** : Crée un emoji avec le nom et l'image indiquée. Permission : Gérer les emojis. Cooldown : 3 en 6min/serveur.
**>setperms (mention role 1) (mention role 2) ... (mention role 10) (valeur)** : Met à jour les permissions des rôles avec la valeur indiquée (vous pouvez l'obtenir [ici](https://discordapi.com/permissions.html)). Permission : Gérer le serveur. Cooldown : 5min/serveur.
**>addeveryone (mention role)** : Donne le rôle mentionné à tout membre du serveur. Permission : Gérer les rôles. Cooldown : 5min/serveur.
**>removeeveryone (mention role)** : Retire le rôle mentionné à tout membre du serveur. Permission : Gérer les rôles. Cooldown : 5min/serveur.
**>clearchannel (nom)** : Supprime tous les salons de nom donné. Permission : Gérer les salons. Cooldown : 2min/serveur.
**>clearrole (nom)** : Supprime tous les rôles de nom donné. Permission : Gérer les rôles. Cooldown : 2min/serveur.
**>rainbow** : Crée des rôles de toutes les couleurs. Trop kawaiii ! Le rôle du bot doit être au plus haut. Permission : Gérer les rôles. Cooldown : 10min/serveur.
        """, color=0x36393f)
        embed.set_footer(text="Remarque : si une commande est en cooldown, le bot réagira à votre message avec ⏰")

        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction(emoji="📩")
        except Exception as e:
            await ctx.send(
                ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))

    @commands.command()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.user)
    async def helpsettings(self, ctx):
        embed = discord.Embed(title="Commandes", description="""
__Catégorie : Paramétrage__

**>hsguild** : Définit si un utilisateur peut rejoindre votre serveur par l'intermédiaire du bot. Par défaut désactivé. Permission : Gérer le serveur. Cooldown : 2min/serveur.
**>changepsw (nouveau mot de passe)** : Définit le mot de passe demandé lorsqu'un utilisateur demande à entrer sur le serveur par l'intermédiare du bot. Laisser vide pour désactiver. Permission : Gérer le serveur. Cooldown : 2min/serveur.
**>banraidbots** : Active ou désactive le bannissement de bots détectés comme bots de raid (création en masse de salons/roles, spam). Par défaut activé. Permission : Gérer le serveur. Cooldown : 2min/serveur.
**>hmode** : Active ou désactive la détection heuristique des bots de raid. Permission : Gérer le serveur. Cooldown : 2min/serveur.
**>likesys** : Active ou désactive le fil de likes (quand il y a 15 réactions :heart: sur un message, le bot envoie son contenu dans un channel automatiquement créé). Permission : Gérer le serveur. Cooldown : 2min/serveur.
**>lockperms** : Restreint (ou révoque la restriction) l'utilisation de certaines commandes de modification du serveur (telle que `>clone` ou `>configguild` au propriétaire de celui-ci uniquement. Par défaut activé. Cooldown : 2min/serveur.
        """, color=0x36393f)
        embed.set_footer(text="Remarque : si une commande est en cooldown, le bot réagira à votre message avec ⏰")

        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction(emoji="📩")
        except Exception as e:
            await ctx.send(
                ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))

    @commands.command()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.user)
    async def helpbackup(self, ctx):
        embed = discord.Embed(title="Commandes", description="""
__Catégorie : Backup__

**>createbackup** : Crée une sauvegarde de votre serveur. Permissions : Administrateur. Cooldown : 3min/serveur.
**>updatebackup (nom)** : Crée une sauvegarde et remplace la sauvegarde indiquée. Les noms des serveurs doivent être identiques. Permissions : Administrateur. Cooldown : 3min/serveur.
**>backuplist** : Liste des sauvegardes disponibles. Les noms sont de la sorte : `ID serveur-jour-mois-année-heure-minute`. Cooldown : 2min/user.
**>backupinfos (nom)** : Infos sur une sauvegarde. Cooldown : 2min/user.
**>renamebackup (nom) "(nouveau nom)"** : Renomme la sauvegarde. Cooldown : 2 en 3min/user.
**>deletebackup (nom)** : Supprime la sauvegarde indiquée. Cooldown : 2 en 3min/user.
**>roleslist (nom)** : Donne la liste des rôles d'une sauvegarde. Cooldown : 2min/user.
**>channelslist (nom)** : Donne la liste des salons d'une sauvegarde. Cooldown : 2min/user.
**>roleinfo (nom) (nom rôle)** : Donne les caractéristiques d'un rôle d'une sauvegarde. Cooldown : 2min/user.
**>loadbackup (nom)** : Charge la sauvegarde indiquée. **Attention, cela écrase le serveur.** Permissions : Administrateur. Cooldown : 5min/serveur.
**>loadroles (nom)** : Charge les rôles de la sauvegarde indiquée. Permissions : Administrateur. Cooldown : 5min/serveur.
**>loadchannels (nom)** : Charge les salons de la sauvegarde indiquée. Permissions : Administrateur. Cooldown : 5min/serveur.
**>loadbans (nom)** : Charge les bannissemnts de la sauvegarde indiquée. Permissions : Administrateur. Cooldown : 5min/serveur.
**>loademojis (nom)** : Charge les emojis de la sauvegarde indiquée. Permissions : Administrateur. Cooldown : 5min/serveur.
**>loadsettings (nom)** : Charge les paramètres de la sauvegarde indiquée. Permissions : Administrateur. Cooldown : 5min/serveur.
**>newguild (nom)** : Crée un serveur et charge la sauvegarde indiquée sur ce dernier. Cooldown : 15min/user.
            """, color=0x36393f)
        embed.set_footer(text="Remarque : si une commande est en cooldown, le bot réagira à votre message avec ⏰")

        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction(emoji="📩")
        except Exception as e:
            await ctx.send(
                ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))

    @commands.command()
    @commands.cooldown(3, 15 * 60, type=commands.BucketType.user)
    async def randominvite(self, ctx):
        glist = []
        for g in self.bot.guilds:
            entry = self.settings.get_entry(g.id)
            if entry is not None:
                if entry["identified"] == True and len(entry["password"]) == 0:
                    glist.append(g.id)

        if len(glist) == 0:
            await ctx.send("Aucun serveur recensé :confused:")
            return

        i = random.randint(0, len(glist) - 1)
        ig = self.bot.get_guild(glist[i])
        invite = "Impossible de créer l'invitation :confused:"
        try:
            invObj = await ig.text_channels[0].create_invite(destination=ig.text_channels[0], xkcd=True, max_uses=10,
                                                             max_age=300)
            invite = str(invObj)
        except Exception:
            pass

        if invite.find("discord.gg") > -1:
            embed = discord.Embed(title="Invitation aléatoire", description="[{}]({})".format(ig.name, invite),
                                  color=0x004080)
            embed.set_thumbnail(url=ig.icon_url_as(format='jpg'))
            embed.set_footer(text="Cliquez sur le nom pour rejoindre !")
            await ctx.send(embed=embed)
        else:
            await ctx.send(invite)

    @commands.command()
    @commands.cooldown(3, 10 * 60, type=commands.BucketType.user)
    async def randomguild(self, ctx):
        public_guilds = [x for x in self.bot.guilds if not x.id in self.bot.cogs['Staff'].locked_guilds]

        i = random.randint(0, len(public_guilds) - 1)
        target = public_guilds[i]
        color = 0x004080
        if target.id == self.bot.config["supportGuild"]["ID"]:
            color = 0xca6c17
        embed = discord.Embed(title="Serveur aléatoire", description="{}".format(target.name), color=color)
        embed.set_thumbnail(url=target.icon_url_as(format='jpg'))
        if target.id == self.bot.config["supportGuild"]["ID"]:
            p = round(100 / len(self.bot.guilds), 3)
            embed.add_field(name="Waouh !",
                            value="Vous êtes tombé sur le serveur de support ! Cela avait {}% de chances d'arriver.".format(
                                str(p)))
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(3, 10 * 60, type=commands.BucketType.user)
    async def randomuser(self, ctx):
        allusers = []
        for u in self.bot.get_all_members():
            allusers.append(u)
        i = random.randint(0, len(allusers) - 1)
        user = allusers[i]
        color = 0x004080
        if user.id == 303191513372950529 or user.id == self.bot.user.id:
            color = 0xca6c17
        embed = discord.Embed(title="Utilisateur aléatoire",
                              description="<@{}> ({}#{})".format(str(user.id), user.name, str(user.discriminator)),
                              color=color)
        if user.id == 303191513372950529 or user.id == self.bot.user.id:
            p = round(100 / len(allusers), 3)
            embed.add_field(name="Waouh !",
                            value="Vous êtes tombé sur le bot ou son owner ! Cela avait {}% de chances d'arriver.".format(
                                str(p)))
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 8 * 60, type=commands.BucketType.user)
    async def createguild(self, ctx, *, name):
        names = ["empty", "personnal", "public", "gaming", "pub", "community"]
        if not name in names:
            await ctx.message.delete()
            strlist = ""
            for n in names:
                strlist += n + ", "
            strlist = strlist[:-2]
            embed = discord.Embed(title="❌ Erreur",
                                  description="Veuillez spécifier un type de serveur : `{}`".format(strlist),
                                  color=0xff8000)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(10)
            await response.delete()
            return

        iconLink = None
        guildName = None
        if name == "empty":
            guildName = "..."
            iconLink = "https://image.flaticon.com/icons/png/512/43/43533.png"
        elif name == "personnal":
            guildName = "{}'s guild".format(ctx.author.name if '"' not in ctx.author.name else ctx.author.name.replace('"', '\"'))
            iconLink = ctx.author.avatar_url_as(format='jpg')
        elif name == "public":
            index = random.randint(0, len(self.public_names) - 1)
            guildName = self.public_names[index]
            iconLink = self.public_icons[index]
        elif name == "gaming":
            guildName = self.gaming_names[random.randint(0, len(self.gaming_names) - 1)]
            iconLink = self.gaming_icons[random.randint(0, len(self.gaming_icons) - 1)]
        elif name == "pub":
            guildName = "La taverne à pub de {}".format(ctx.author.name if '"' not in ctx.author.name else ctx.author.name.replace('"', '\"'))
            iconLink = self.pub_icons[random.randint(0, len(self.pub_icons) - 1)]
        elif name == "community":
            guildName = "Communauté de {}".format(ctx.author.name if '"' not in ctx.author.name else ctx.author.name.replace('"', '\"'))
            iconLink = ctx.author.avatar_url_as(format='jpg')

        linkC = self.bot.get_channel(self.bot.config["linkChannel"])
        gCreator = linkC.guild.get_member(self.bot.config["GuildCreator"])

        await linkC.send("/createguild|{}|{}".format(guildName, iconLink))

        def check(m):
            return m.author == gCreator and m.channel == linkC

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(":x: Erreur : pas de réponse du bot créant les serveurs.")
            return
        else:
            try:
                await ctx.author.send(msg.content)
                await ctx.message.add_reaction(emoji="📩")
            except Exception as e:
                await ctx.send(
                    ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))
                await ctx.send(msg.content)

        embed2 = discord.Embed(title="Création de serveur", description="Le serveur {} a été créé".format(guildName),
                               color=0x8000ff)
        embed2.set_thumbnail(url=iconLink)
        embed2.add_field(name="Utilisateur",
                         value=ctx.author.name + "#" + str(ctx.author.discriminator) + " (" + str(ctx.author.id) + ")",
                         inline=False)
        lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
        await lChan.send(embed=embed2)

    @commands.command()
    @commands.cooldown(3, 10 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def health(self, ctx):
        bot_info = ""

        bRole = discord.utils.get(ctx.message.guild.roles, name=self.bot.user.name)
        if bRole is None:
            bot_info += "❌ Le rôle du bot n'a pas été trouvé, veuillez le renommer en `{}`.\n".format(
                self.bot.user.name)
        else:
            bot_info += "✅ Le rôle du bot a bien été trouvé\n"

        if not ctx.message.guild.me.guild_permissions.administrator:
            bot_info += "❌ Le bot ne possède pas la permission administrateur. Veuillez lui accorder, ou toutes les permissions.\n"
        else:
            bot_info += "✅ Permission `Administrateur` accordée au bot\n"

        pob = "unknown"
        if bRole is not None:
            pob = "✅ Le rôle du bot est le plus haut"
            if bRole.position != len(ctx.message.guild.roles) - 1:
                pob = ":negative_squared_cross_mark: Le rôle du bot n'est pas le plus haut"
            for r in ctx.message.guild.roles:
                if r.position > bRole.position and r.managed:
                    pob = "⚠️ Le rôle du bot est en-dessous du rôle d'un autre bot, si un bot malveillant à un rôle au dessus de GuildEdit ce dernier ne pourra rien faire..."
                    break
        bot_info += pob + "\n"

        if len([x for x in ctx.guild.text_channels if x.name == "ge-logs"]) != 0:
            bot_info += "✅ Salon de logs trouvé"
        else:
            bot_info += ":negative_squared_cross_mark: Salon de logs non trouvé. Pour activer les logs : créez un salon `ge-logs`."

        guild_info = ""

        roles_m = ""
        for r in ctx.guild.roles:
            if r.mentionable:
                roles_m += r.mention + " "
        if len(roles_m) == 0:
            guild_info = "✅ Aucun rôle mentionnable\n"
        else:
            guild_info = "⚠️ Rôles mentionnables : {}\n".format(roles_m)

        roles_a = ""
        for r in ctx.guild.roles:
            if r.permissions.administrator and r.name != self.bot.user.name:
                roles_a += r.mention + " "
        if len(roles_a) == 0:
            guild_info += "✅ Aucun rôle ne possédant la permission administrateur\n"
        else:
            guild_info += "❓ Rôles possédant la permission administrateur : {}\n".format(roles_a)

        roles_me = ""
        for r in ctx.guild.roles:
            if r.permissions.mention_everyone:
                roles_me += r.mention + " "
        if len(roles_me) == 0:
            guild_info += "✅ Aucun rôle ne possédant la permission de mentionner everyone\n"
        else:
            guild_info += "❓ Rôles possédant la permission de mentionner everyone : {}\n".format(roles_me)

        roles_stm = ""
        for r in ctx.guild.roles:
            if r.permissions.send_tts_messages:
                roles_stm += r.mention + " "
        if len(roles_stm) == 0:
            guild_info += "✅ Aucun rôle ne possédant la permission d'envoyer des messages tts\n"
        else:
            guild_info += "❓ Rôles possédant la permission d'envoyer des messages tts : {}\n".format(roles_stm)

        if str(ctx.guild.verification_level) in ["medium", "high", "extreme"]:
            guild_info += "✅ Niveau de vérification du serveur correct"
        elif str(ctx.guild.verification_level) == "low":
            guild_info += ":negative_squared_cross_mark: Niveau de vérification du serveur légèrement faible, il est conseillé de l'augmenter d'un niveau"
        else:
            guild_info += "⚠️ Niveau de vérification du serveur trop faible."

        embed = discord.Embed(title="💊 Diagnostic", description="Informations quant aux problèmes éventuels.",
                              color=0x36393f)
        embed.add_field(name="Problèmes liés au bot", value=bot_info, inline=False)
        embed.add_field(name="Problèmes de sécurité du serveur", value=guild_info, inline=False)
        embed.set_footer(
            text="✅ : Aucun problème détecté\n⚠️ Avertissement\n❎ Problème mineur (ne gêne pas une utilisation normale du bot)\n❌ Erreur critique")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
