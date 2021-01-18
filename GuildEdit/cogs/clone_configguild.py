import aiohttp
import asyncio
import json
import discord
from discord.ext import commands


class CloneConfigguild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = bot.cogs["Settings"]

    async def cleanguild(self, guild: discord.guild):
        for channel in guild.channels:
            await channel.delete()

        for i in range(round(len(guild.roles) / 2)):
            for role in guild.roles:
                try:
                    await role.delete()
                except Exception:
                    pass

    async def loadmodel(self, guild: discord.guild, filename: str):
        with open(filename + ".json", "r") as f:
            g = json.load(f)

            for role in g["roles"][::-1]:
                permissions = discord.Permissions()
                permissions.update(**dict(role["permissions"]))
                if role["name"] != "@everyone":
                    await guild.create_role(name=role["name"], colour=discord.Colour.from_rgb(*role["colour"]),
                                            hoist=role["hoist"], mentionable=role["mentionable"],
                                            permissions=permissions)
                else:
                    await guild.default_role.edit(permissions=permissions)

            for category in g["categories"]:
                overwrites = []
                for overwrite in category["overwrites"]:
                    if overwrite["type"] == "role":
                        if overwrite["name"] not in [x.name for x in guild.roles]:
                            pass
                        else:
                            role = [x for x in guild.roles if x.name == overwrite["name"]][0]
                            permissions = discord.PermissionOverwrite()
                            permissions.update(**dict(overwrite["permissions"]))
                            overwrites.append((role, permissions))

                new_cat = await guild.create_category(category["name"], overwrites=dict(overwrites))
                await new_cat.edit(nsfw=category["nsfw"])

            for channel in g["text_channels"]:
                category = None
                try:
                    category = [x for x in guild.categories if x.name == channel["category"]][0]
                except:
                    pass
                overwrites = []
                for overwrite in channel["overwrites"]:
                    if overwrite["type"] == "role":
                        if overwrite["name"] not in [x.name for x in guild.roles]:
                            pass
                        else:
                            role = [x for x in guild.roles if x.name == overwrite["name"]][0]
                            permissions = discord.PermissionOverwrite()
                            permissions.update(**dict(overwrite["permissions"]))
                            overwrites.append((role, permissions))

                new_chan = await guild.create_text_channel(channel["name"], overwrites=dict(overwrites))
                await new_chan.edit(topic=channel["topic"], nsfw=channel["nsfw"], category=category,
                                    slowmode_delay=channel["slowmode_delay"])

            for channel in g["voice_channels"]:
                overwrites = []
                category = None
                try:
                    category = [x for x in guild.categories if x.name == channel["category"]][0]
                except:
                    pass
                for overwrite in channel["overwrites"]:
                    if overwrite["type"] == "role":
                        if overwrite["name"] not in [x.name for x in guild.roles]:
                            pass
                        else:
                            role = [x for x in guild.roles if x.name == overwrite["name"]][0]
                            permissions = discord.PermissionOverwrite()
                            permissions.update(**dict(overwrite["permissions"]))
                            overwrites.append((role, permissions))

                new_chan = await guild.create_voice_channel(channel["name"], overwrites=dict(overwrites))
                await new_chan.edit(bitrate=channel["bitrate"] if channel["bitrate"] <= guild.bitrate_limit else guild.bitrate_limit,
                                    user_limit=channel["user_limit"], category=category)

            for channel in g["text_channels"]:
                await [x for x in guild.text_channels if x.name == channel["name"]][0].edit(
                    position=channel["position"] if channel["position"] < len(guild.text_channels) else len(
                        guild.text_channels) - 1)

            for channel in g["voice_channels"]:
                await [x for x in guild.voice_channels if x.name == channel["name"]][0].edit(
                    position=channel["position"] if channel["position"] < len(guild.voice_channels) else len(
                        guild.voice_channels) - 1)

            for category in g["categories"]:
                await [x for x in guild.categories if x.name == category["name"]][0].edit(
                    position=category["position"] if category["position"] < len(guild.categories) else len(
                        guild.categories) - 1)

            await guild.edit(region=discord.VoiceRegion(g["region"]),
                             afk_channel=[x for x in guild.voice_channels if x.name == g["afk_channel"]][0] if g[
                                 "afk_channel"] else None, afk_timeout=g["afk_timeout"],
                             verification_level=discord.VerificationLevel(g["verification_level"]),
                             default_notifications=discord.NotificationLevel.only_mentions if g[
                                                                                                  "default_notifications"] == "only_mentions" else discord.NotificationLevel.all_messages,
                             explicit_content_filter=discord.ContentFilter(g["explicit_content_filter"]),
                             system_channel=[x for x in guild.text_channels if x.name == g["system_channel"]][0] if g[
                                 "system_channel"] else None)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10 * 60, type=commands.BucketType.user)
    async def configguild(self, ctx, *, content):
        name = None
        id = None

        try:
            name, id = content.split(" ")
            id = int(id)
        except Exception:
            name = content
            id = ctx.message.guild.id

        names = ["empty", "personnal", "public", "gaming", "pub", "community"]
        if not name in names:
            strlist = ""
            for n in names:
                strlist += n + ", "
            strlist = strlist[:-2]
            embed = discord.Embed(title="❌ Erreur",
                                  description="Veuillez spécifier un type de serveur : `{}`".format(strlist),
                                  color=0xff8000)
            await ctx.send(embed=embed)
            return

        target = None
        try:
            target = self.bot.get_guild(id)
            test = target.name
        except Exception:
            embed = discord.Embed(title="❌ Erreur", description="Impossible de trouver le serveur.", color=0xff8000)
            await ctx.send(embed=embed)
            return

        member = target.get_member(ctx.author.id)
        if member is None:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Vous n'êtes pas sur ce serveur !",
                                  description="Il s'agit du serveur **{}** que vous tentez de configurer.".format(
                                      target.name), color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        if not member.guild_permissions.administrator and member != target.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Vous n'avez pas la permission administrateur sur le serveur indiqué !",
                                  description="Vous n'êtes pas autorisé à configurer ce serveur.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        if self.settings.perms_lock(target.id) and member != target.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        bRole = discord.utils.get(target.roles, name=self.bot.user.name)
        if bRole is None:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Le rôle du bot n'a pas été trouvé sur le serveur cible !",
                                  description="Merci de le renommer en `GuildEdit`.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if bRole.position != len(target.roles) - 1:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Le rôle du bot n'est pas le plus haut sur le serveur cible !",
                                  description="Merci de le déplacer tout en haut.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        confirm = None
        if len(target.members) >= 30:
            embed = discord.Embed(title="☝️ Attention !", description="Il y a 30 membres ou plus sur le serveur cible.",
                                  color=0xe4da05)
            embed.add_field(name="Serveur cible ?",
                            value="Le serveur cible correspond au serveur que vous allez configurer : **{}**. Cela entraînera la suppression de tout son contenu.".format(
                                target.name), inline=False)
            embed.add_field(name="On ne clique pas trop vite !",
                            value="Toute opération est définitive. En cas de doute, ne réagissez pas à ce message, et lisez bien la description de la commande dans >helpguild.\nSi vous êtes sûr de ce que vous faîtes, réagissez avec 🛑",
                            inline=False)
            confirm = await ctx.send(embed=embed)
            await confirm.add_reaction(emoji='🛑')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == '🛑'

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
                return

            await confirm.clear_reactions()

        try:
            await ctx.message.delete()
        except Exception:
            pass

        embedC = discord.Embed(title="🛑 Confirmation",
                               description="Êtes-vous sûr de configurer le serveur **{}** ? Cela supprimera tout son contenu.".format(
                                   target.name), color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        if confirm is None:
            confirm = await ctx.send(content="Loading")
        await confirm.edit(content="", embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        if id != ctx.guild.id:
            embedE = discord.Embed(title="Configuration en cours",
                                   description="Vous serez notifié une fois l'opération terminée. Merci de ne pas modifier le serveur cible en attendant !",
                                   color=0xff0000)
            embedE.set_thumbnail(url="https://cdn3.iconfinder.com/data/icons/databases/512/data_processor-512.png")
            await confirm.edit(embed=embedE)
            await confirm.clear_reactions()

        async with ctx.message.channel.typing():

            try:
                await self.cleanguild(target)
            except Exception as e:
                if id != ctx.guild.id:
                    embed = discord.Embed(title="❌ Erreur",
                                          description="**Le nettoyage du serveur a échoué pour la raison suivante :** " + str(
                                              e), color=0xff8000)
                    await ctx.send(embed=embed)
                return

            try:
                if name != "empty":
                    await self.loadmodel(target, name)
                    if name != "personnal":
                        await target.text_channels[0].create_invite(destination=target.text_channels[0], xkcd=True,
                                                                    max_uses=0, max_age=0)

                    adminrole = [x for x in target.roles[::-1] if x.permissions.administrator and not x.managed][0]
                    member = target.get_member(ctx.author.id)
                    await member.add_roles(adminrole)

                    if target.owner == member:
                        ownerrole = [x for x in target.roles[::-1] if
                                     x.name.find("Propriétaire") > -1 or x.name.find("👑") > -1 or x.name.find(
                                         "Fondateur") > -1 and not x.managed]
                        if len(ownerrole) > 0 and not ownerrole[0] in member.roles:
                            await member.add_roles(ownerrole[0])

                    embed = discord.Embed(title="✅ Voilà !", description="Votre serveur a été configuré avec succès.",
                                          color=0x008040)
                    if id == ctx.guild.id:
                        await target.text_channels[0].send(content=ctx.author.mention, embed=embed)
                    else:
                        await confirm.edit(content=ctx.author.mention, embed=embed)
            except Exception as e:
                embed = discord.Embed(title="❌ Erreur",
                                      description="**La modification du serveur a échouée pour la raison suivante :** " + str(
                                          e), color=0xff8000)
                if id != ctx.guild.id:
                    await ctx.send(embed=embed)
                else:
                    await ctx.guild.text_channels[0].send(content=ctx.author.mention, embed=embed)
                return

        embed2 = discord.Embed(title="Configuration de serveur",
                               description="Le serveur " + target.name + " (" + str(target.id) + ") a été configuré",
                               color=0x8000ff)
        embed2.add_field(name="Utilisateur",
                         value=ctx.author.name + "#" + str(ctx.author.discriminator) + " (" + str(ctx.author.id) + ")",
                         inline=False)
        lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
        await lChan.send(embed=embed2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 15 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def clone(self, ctx, *, targetid):
        try:
            targetid = int(targetid)
        except Exception:
            await ctx.message.delete()
            embed = discord.Embed(title="❌ Veuillez entrer un id valide !", color=0xff0000)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if ctx.message.guild.id == int(targetid):
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Serveurs cible et source sont les mêmes !",
                                  description="Vous ne pouvez pas cloner ce serveur sur ce serveur...", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        guild_copy = None
        try:
            guild_copy = self.bot.get_guild(targetid)
            test = guild_copy.name
        except Exception:
            embed = discord.Embed(title="❌ Erreur", description="Le bot n'est pas sur le serveur cible !",
                                  color=0xff8000)
            await ctx.message.delete()
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        if ctx.author != guild_copy.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Vous n'êtes pas propriétaire du serveur cible !",
                                  description="Impossible de cloner le serveur.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        bRole = discord.utils.get(guild_copy.roles, name=self.bot.user.name)
        if bRole is None:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Le rôle du bot n'a pas été trouvé sur le serveur cible !",
                                  description="Merci de le renommer en `GuildEdit`.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if bRole.position != len(guild_copy.roles) - 1 and ctx.author.id != 303191513372950529:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Le rôle du bot n'est pas le plus haut sur le serveur cible !",
                                  description="Merci de le déplacer tout en haut.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        confirm = None
        if len(guild_copy.members) >= 30:
            embed = discord.Embed(title="☝️ Attention !", description="Il y a 30 membres ou plus sur le serveur cible.",
                                  color=0xe4da05)
            embed.add_field(name="Serveur cible ?",
                            value="Le serveur cible correspond au serveur où le serveur source (ce serveur) sera copié : **{}**. Cela entraînera la suppression de tout son contenu.".format(
                                guild_copy.name), inline=False)
            embed.add_field(name="On ne clique pas trop vite !",
                            value="Toute opération est définitive. En cas de doute, ne réagissez pas à ce message, et lisez bien la description de la commande dans >helpguild.\nSi vous êtes sûr de ce que vous faîtes, réagissez avec 🛑",
                            inline=False)
            confirm = await ctx.send(embed=embed)
            await confirm.add_reaction(emoji='🛑')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == '🛑'

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
                return
            await confirm.clear_reactions()

        embedC = discord.Embed(title="🛑 Confirmation du clonage",
                               description="Le clonage de ce serveur entraînera la suppression de toute la configuration de **{}**. Continuer ?".format(
                                   guild_copy.name), color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        if confirm is None:
            confirm = await ctx.send(content="Loading")
        await confirm.edit(content="", embed=embedC)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        await confirm.clear_reactions()
        embedE = discord.Embed(title="Clonage en cours",
                               description="Vous serez notifié une fois l'opération terminée. Merci de ne pas modifier le serveur cible en attendant !",
                               color=0xff0000)
        embedE.set_thumbnail(url="https://cdn3.iconfinder.com/data/icons/3d-printing-icon-set/512/Clone.png")
        await confirm.edit(embed=embedE)

        async with ctx.message.channel.typing():

            await self.cleanguild(guild_copy)
            await ctx.send(":white_check_mark: Nettoyage du serveur cible OK")

            # roles
            botRole = discord.utils.get(ctx.message.guild.roles, name=self.bot.user.name)
            if botRole is None:
                await ctx.send(
                    ":x: **La copie des rôles a échouée pour la raison suivante :** Impossible de trouver le rôle du bot. Veuillez redonner au rôle son nom d'origine : `GuildEdit`")
                return
            try:
                guild_roles = ctx.message.guild.roles[::-1]
                for role in guild_roles:
                    if role != ctx.message.guild.default_role and role != botRole:
                        newrole = await guild_copy.create_role(name=role.name, permissions=role.permissions,
                                                               colour=role.colour, hoist=role.hoist,
                                                               mentionable=role.mentionable)

                await guild_copy.default_role.edit(permissions=ctx.message.guild.default_role.permissions)
                await ctx.send(":white_check_mark: Copie des rôles OK")
            except Exception as e:
                await ctx.send(":x: **La copie des rôles a échouée pour la raison suivante :** " + str(e))
                return

            afk_channel = None
            system_channel = None

            # channels
            try:
                gcopy_roles = guild_copy.roles

                for category in ctx.message.guild.categories:
                    overwrites = []
                    newOverwrites = []
                    overwrite_dict = {}
                    for overwrite in category.overwrites:
                        overwrite_dict = {
                            "name": overwrite.name,
                            "permissions": list(category.overwrites_for(overwrite)),
                            "type": "member" if type(overwrite) == discord.Member else "role"
                        }
                        overwrites.append(overwrite_dict)

                    for overwriteI in overwrites:
                        if overwriteI["type"] == "role":
                            if overwriteI["name"] not in [x.name for x in gcopy_roles]:
                                pass
                            else:
                                role = [x for x in gcopy_roles if x.name == overwriteI["name"]][0]
                                permissions = discord.PermissionOverwrite()
                                permissions.update(**dict(overwriteI["permissions"]))
                                newOverwrites.append((role, permissions))

                    new_cat = await guild_copy.create_category(name=category.name, overwrites=dict(newOverwrites))
                    await new_cat.edit(nsfw=category.nsfw)

                for textchannel in ctx.message.guild.text_channels:
                    category = None
                    if textchannel.category is not None:
                        category = discord.utils.get(guild_copy.categories, name=textchannel.category.name)

                    overwrites = []
                    newOverwrites = []
                    overwrite_dict = {}
                    for overwrite in textchannel.overwrites:
                        overwrite_dict = {
                            "name": overwrite.name,
                            "permissions": list(textchannel.overwrites_for(overwrite)),
                            "type": "member" if type(overwrite) == discord.Member else "role"
                        }
                        overwrites.append(overwrite_dict)

                    for overwriteI in overwrites:
                        if overwriteI["type"] == "role":
                            if overwriteI["name"] not in [x.name for x in gcopy_roles]:
                                pass
                            else:
                                role = [x for x in gcopy_roles if x.name == overwriteI["name"]][0]
                                permissions = discord.PermissionOverwrite()
                                permissions.update(**dict(overwriteI["permissions"]))
                                newOverwrites.append((role, permissions))

                    new_channel = await guild_copy.create_text_channel(name=textchannel.name,
                                                                       overwrites=dict(newOverwrites),
                                                                       category=category, topic=textchannel.topic,
                                                                       slowmode_delay=textchannel.slowmode_delay,
                                                                       nsfw=textchannel.nsfw)

                    if textchannel == ctx.message.guild.system_channel:
                        system_channel = new_channel

                for voicechannel in ctx.message.guild.voice_channels:
                    category = None
                    if voicechannel.category is not None:
                        category = discord.utils.get(guild_copy.categories, name=voicechannel.category.name)

                    overwrites = []
                    newOverwrites = []
                    overwrite_dict = {}
                    for overwrite in voicechannel.overwrites:
                        overwrite_dict = {
                            "name": overwrite.name,
                            "permissions": list(voicechannel.overwrites_for(overwrite)),
                            "type": "member" if type(overwrite) == discord.Member else "role"
                        }
                        overwrites.append(overwrite_dict)

                    for overwriteI in overwrites:
                        if overwriteI["type"] == "role":
                            if overwriteI["name"] not in [x.name for x in gcopy_roles]:
                                pass
                            else:
                                role = [x for x in gcopy_roles if x.name == overwriteI["name"]][0]
                                permissions = discord.PermissionOverwrite()
                                permissions.update(**dict(overwriteI["permissions"]))
                                newOverwrites.append((role, permissions))

                    new_channel = await guild_copy.create_voice_channel(name=voicechannel.name,
                                                                        overwrites=dict(newOverwrites),
                                                                        category=category,
                                                                        bitrate=voicechannel.bitrate if voicechannel.bitrate <= guild_copy.bitrate_limit else guild_copy.bitrate_limit,
                                                                        user_limit=voicechannel.user_limit)

                    if voicechannel == ctx.message.guild.afk_channel:
                        afk_channel = new_channel
                await ctx.send(":white_check_mark: Copie des salons OK")
            except Exception as e:
                await ctx.send(":x: **La copie des salons a échouée pour la raison suivante : ** " + str(e))
                return

            # settings
            try:
                img = None
                if len(ctx.message.guild.icon_url_as(format='jpg')) > 0:
                    async with aiohttp.ClientSession() as ses:
                        async with ses.get(str(ctx.message.guild.icon_url_as(format='jpg'))) as r:
                            img = await r.read()

                await guild_copy.edit(name=ctx.message.guild.name + " (copie)", icon=img,
                                      region=ctx.message.guild.region, afk_channel=afk_channel,
                                      afk_timeout=ctx.message.guild.afk_timeout,
                                      verification_level=ctx.message.guild.verification_level,
                                      default_notifications=ctx.message.guild.default_notifications,
                                      system_channel=system_channel)
                await ctx.send(":white_check_mark: Importation des paramètres OK")
            except Exception as e:
                await ctx.send(":x: **L'importation des paramètres a échouée pour la raison suivante : ** " + str(e))
                return

            # liste bots
            content = ""
            for m in ctx.message.guild.members:
                if m.bot and m != self.bot.user:
                    line = "[{}]({})".format(m.name,
                                             "https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions={}".format(
                                                 str(m.id), str(m.guild_permissions.value)))
                    if content == "":
                        content += line
                    else:
                        if len(content) + len(line) < 1000:
                            content += line + "\n"
                        else:
                            embedb = discord.Embed(title="Liste des bots présents sur le serveur cloné",
                                                   description="Voici la liste des bots présents sur le serveur cloné :")
                            embedb.set_thumbnail(
                                url="https://pngimage.net/wp-content/uploads/2018/05/bot-icon-png-8.png")
                            embedb.add_field(name="Liste", value=content, inline=False)
                            if len(guild_copy.text_channels) > 0:
                                await guild_copy.text_channels[0].send(embed=embedb)
                            content = ""
                            content += line

            if len(content) > 0:
                embedb = discord.Embed(title="Liste des bots présents sur le serveur cloné",
                                       description="Voici la liste des bots présents sur le serveur cloné :")
                embedb.set_thumbnail(url="https://pngimage.net/wp-content/uploads/2018/05/bot-icon-png-8.png")
                embedb.add_field(name="Liste", value=content, inline=False)
                if len(guild_copy.text_channels) > 0:
                    await guild_copy.text_channels[0].send(content=ctx.author.mention, embed=embedb)

            await ctx.send(ctx.author.mention + " Clonage terminé !")

            embed2 = discord.Embed(title="Serveur cloné",
                                   description="Le serveur " + ctx.message.guild.name + " (" + str(
                                       ctx.message.guild.id) + ") a été cloné", color=0x8000ff)
            embed2.add_field(name="Utilisateur",
                             value=ctx.author.name + "#" + str(ctx.author.discriminator) + " (" + str(
                                 ctx.author.id) + ")", inline=False)
            lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
            await lChan.send(embed=embed2)


def setup(bot):
    bot.add_cog(CloneConfigguild(bot))
