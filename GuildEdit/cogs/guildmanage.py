import aiohttp
import asyncio
import random
from datetime import datetime
import discord
from discord.ext import commands


class GuildManage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_date(self):
        return datetime.now().strftime("%d/%m/%Y, %Hh%M")

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

    def has_higher_permissions(self, user1: discord.Member, user2: discord.Member):
        if user1 == user2:
            return False
        if user1 == user1.guild.owner:
            return True
        if user2 == user1.guild.owner:
            return False
        if user1.top_role > user2.top_role:
            return True
        return False

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    async def setperms(self, ctx, mentions_roles: commands.Greedy[discord.Role], permissions_value):
        bRole = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
        if bRole is None:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'a pas été trouvé !",
                                  description="Merci de le renommer en `GuildEdit`.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if len(mentions_roles) == 0:
            await ctx.send(":warning: **Veuillez mentionner au moins un rôle !**")
            return

        if len(mentions_roles) > 10:
            await ctx.send(":x: **Impossible de changer les permissions de plus de 10 rôles à la fois.**")
            return

        perms = discord.Permissions(permissions=0)
        try:
            perms = discord.Permissions(permissions=int(permissions_value))
        except Exception:
            await ctx.send(":x: **Valeur de permissions incorrecte.**")
            return

        embedC = discord.Embed(title=":triangular_flag_on_post::pencil2: Modifier les permissions des rôles ?",
                               color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        await confirm.delete()

        message_content = ""
        for mention_role in mentions_roles:
            if mention_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
                line = ":x: **Impossible de changer les permissions de `{}` : le rôle est dessus de votre rôle le plus haut.**\n".format(
                    mention_role.name)
                if len(message_content + line) > 1950:
                    await ctx.send(message_content)
                    message_content = line
                else:
                    message_content += line
                continue

            if mention_role.position >= bRole.position:
                line = ":x: **Impossible de changer les permissions de `{}` : le rôle est dessus de mon rôle.**\n".format(
                    mention_role.name)
                if len(message_content + line) > 1950:
                    await ctx.send(message_content)
                    message_content = line
                else:
                    message_content += line
                continue

            try:
                await mention_role.edit(permissions=perms, reason="Permissions changées (valeur : {}) par {}#{}".format(
                    str(permissions_value), ctx.author.name, str(ctx.author.discriminator)))
                line = ":white_check_mark: **Permissions de `{}` mises à jour !**\n".format(mention_role.name)
                if len(message_content + line) > 1950:
                    await ctx.send(message_content)
                    message_content = line
                else:
                    message_content += line
            except Exception as e:
                line = ":x: **Erreur inconnue lors de l'édition de `{}` :** `{}`\n".format(mention_role.name, str(e))
                if len(message_content + line) > 1950:
                    await ctx.send(message_content)
                    message_content = line
                else:
                    message_content += line

        if len(message_content) > 0:
            await ctx.send(message_content)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    async def addeveryone(self, ctx, mention_role: discord.Role):
        if mention_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            embed = discord.Embed(title=":warning: Permissions insuffisantes",
                                  description="Le rôle doit être strictement inférieur au votre.", color=0xffff00)
            await ctx.send(embed=embed)
            return

        bRole = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
        if bRole is None:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'a pas été trouvé !",
                                  description="Merci de le renommer en `GuildEdit`.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if mention_role.position >= bRole.position:
            embed = discord.Embed(title=":warning: Le rôle du bot est en dessous de celui indiqué !",
                                  description="Le rôle doit être strictement inférieur à celui du bot.", color=0xffff00)
            await ctx.send(embed=embed)
            return

        if mention_role == ctx.guild.default_role:
            embed = discord.Embed(title="❌ Erreur !", description="Rôle incorrect.", color=0xff0000)
            await ctx.send(embed=embed)
            return

        embedC = discord.Embed(
            title=":triangular_flag_on_post: Ajouter le rôle {} à tout le monde ?".format(mention_role.name),
            color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        for member in ctx.guild.members:
            if not mention_role in member.roles:
                await member.add_roles(mention_role)

        await confirm.clear_reactions()
        rembed = discord.Embed(title=":triangular_flag_on_post: Voilà !", description="Rôle ajouté à tous les membres.",
                               color=0x008040)
        await confirm.edit(embed=rembed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    async def removeeveryone(self, ctx, mention_role: discord.Role):
        if mention_role.position >= ctx.author.top_role.position and ctx.author != ctx.guild.owner:
            embed = discord.Embed(title=":warning: Permissions insuffisantes",
                                  description="Le rôle doit être strictement inférieur au votre.", color=0xffff00)
            await ctx.send(embed=embed)
            return

        bRole = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
        if bRole is None:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'a pas été trouvé !",
                                  description="Merci de le renommer en `GuildEdit`.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if mention_role.position >= bRole.position:
            embed = discord.Embed(title=":warning: Le rôle du bot est en dessous de celui indiqué !",
                                  description="Le rôle doit être strictement inférieur à celui du bot.", color=0xffff00)
            await ctx.send(embed=embed)
            return

        if mention_role == ctx.guild.default_role:
            embed = discord.Embed(title="❌ Erreur !", description="Rôle incorrect.", color=0xff0000)
            await ctx.send(embed=embed)
            return

        embedC = discord.Embed(
            title=":triangular_flag_on_post: Retirer le rôle {} à tout le monde ?".format(mention_role.name),
            color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        for member in ctx.guild.members:
            if mention_role in member.roles:
                await member.remove_roles(mention_role)

        await confirm.clear_reactions()
        rembed = discord.Embed(title=":triangular_flag_on_post: Voilà !",
                               description="Rôle retiré pour tous les membres.", color=0x008040)
        await confirm.edit(embed=rembed)

    @commands.command()
    @commands.has_permissions(manage_emojis=True)
    @commands.guild_only()
    @commands.cooldown(3, 6 * 60, type=commands.BucketType.guild)
    async def addemoji(self, ctx, emoji_name, emoji_url):
        img = None
        try:
            async with aiohttp.ClientSession() as ses:
                async with ses.get(str(emoji_url)) as r:
                    img = await r.read()
        except Exception:
            embed = discord.Embed(title="❌ Erreur !",
                                  description="Impossible d'obtenir l'image correspondant au lien. Veuillez réessayer.",
                                  color=0xff0000)
            await ctx.send(embed=embed)
            return

        embedC = discord.Embed(title="😄 Ajouter l'emoji `{}` ?".format(emoji_name), color=0xf4970b)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        embedC.set_thumbnail(url=emoji_url)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        await confirm.clear_reactions()

        try:
            await ctx.guild.create_custom_emoji(name=emoji_name, image=img,
                                                reason="Emoji créé par {}#{}".format(ctx.author.name,
                                                                                     str(ctx.author.discriminator)))
        except Exception as e:
            embed = discord.Embed(title="❌ Erreur !", description="Impossible de créer l'emoji : `{}`.".format(str(e)),
                                  color=0xff0000)
            try:
                await confirm.edit(embed=embed)
            except Exception:
                await ctx.send(embed=embed)
            return

        rembed = discord.Embed(title="😄 Voilà !", description="Emoji ajouté.", color=0xf4970b)
        await confirm.edit(embed=rembed)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    async def kick(self, ctx, members: commands.Greedy[discord.Member], *, reason="aucune raison fournie"):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if len(members) == 0:
            await ctx.send(":warning: **Veuillez mentionner au moins un utilisateur !**")
            return

        if len(members) > 30:
            await ctx.send(":x: **Impossible d'expulser plus de 30 utilisateurs à la fois.**")
            return

        kick_count = 0
        bRole = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
        message_content = ""

        for member in members:
            line = "unknown"
            if member == self.bot.user or not self.has_higher_permissions(ctx.author, member):
                line = ":x: **Impossible d'expulser *{}#{}* : permissions insuffisantes.**\n".format(member.name, str(
                    member.discriminator))
                if len(message_content + line) > 1950:
                    await ctx.send(message_content)
                    message_content = line
                else:
                    message_content += line
                continue
            if member.top_role >= bRole:
                line = ":x: **Impossible d'expulser *{}#{}* : __mes__ permissions sont insuffisantes.**\n".format(
                    member.name, str(member.discriminator))
                if len(message_content + line) > 1950:
                    await ctx.send(message_content)
                    message_content = line
                else:
                    message_content += line
                continue

            embed = discord.Embed(title=":warning: Expulsion",
                                  description="Vous avez été expulsé de **{}**.".format(ctx.guild.name), color=0xff8000)
            embed.add_field(name="Raison", value=reason, inline=True)
            embed.add_field(name="Modérateur", value="{}#{}".format(ctx.author.name, str(ctx.author.discriminator)),
                            inline=True)
            try:
                await member.send(embed=embed)
            except Exception:
                pass

            try:
                await member.kick(
                    reason="Expulsé par {}#{} : {}".format(ctx.author.name, str(ctx.author.discriminator), reason))
                line = ":white_check_mark:** *{}#{}* a bien été expulsé !**\n".format(member.name,
                                                                                      str(member.discriminator))
                kick_count += 1
            except Exception as e:
                line = ":x: **Erreur inattendue :** `{}`\n".format(e)

            if len(message_content + line) > 1950:
                await ctx.send(message_content)
                message_content = line
            else:
                message_content += line

        if len(message_content) > 0:
            await ctx.send(message_content)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    async def ban(self, ctx, members: commands.Greedy[discord.Member], *, reason="Aucune raison fournie."):
        if not ctx.guild.me.guild_permissions.ban_members:
            raise discord.ext.commands.BotMissingPermissions(['ban_members'])

        try:
            await ctx.message.delete()
        except Exception:
            pass

        if len(members) == 0:
            await ctx.send(":warning: **Veuillez mentionner au moins un utilisateur !**")
            return

        if len(members) > 30:
            await ctx.send(":x: **Impossible de bannir plus de 30 utilisateurs à la fois.**")
            return

        bRole = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
        message_content = ""
        ban_count = 0

        for member in members:
            line = "unknown"
            if member == self.bot.user or not self.has_higher_permissions(ctx.author, member):
                line = ":x: **Impossible de bannir *{}#{}* : permissions insuffisantes.**\n".format(member.name, str(
                    member.discriminator))
                if len(message_content + line) > 1950:
                    await ctx.send(message_content)
                    message_content = line
                else:
                    message_content += line
                continue
            if member.top_role >= bRole:
                line = ":x: **Impossible de bannir *{}#{}* : __mes__ permissions sont insuffisantes.**\n".format(
                    member.name, str(member.discriminator))
                if len(message_content + line) > 1950:
                    await ctx.send(message_content)
                    message_content = line
                else:
                    message_content += line
                continue

            embed = discord.Embed(title=":x: Bannissement",
                                  description="Vous avez été banni de **{}**.".format(ctx.guild.name), color=0xff0000)
            embed.add_field(name="Raison", value=reason, inline=True)
            embed.add_field(name="Modérateur", value="{}#{}".format(ctx.author.name, str(ctx.author.discriminator)),
                            inline=True)
            try:
                await member.send(embed=embed)
            except Exception:
                pass

            try:
                await member.ban(reason="date:{}|mod:{}|reason:{}".format(self.get_date(), str(ctx.author.id), reason),
                                 delete_message_days=0)
                line = ":white_check_mark:** *{}#{}* a bien été banni !**\n".format(member.name,
                                                                                    str(member.discriminator))
                ban_count += 1
            except Exception as e:
                line = ":x: **Erreur inattendue :** `{}`\n".format(e)

            if len(message_content + line) > 1950:
                await ctx.send(message_content)
                message_content = line
            else:
                message_content += line

        if len(message_content) > 0:
            await ctx.send(message_content)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    async def banid(self, ctx, ids: commands.Greedy[int], *, reason="Aucune raison fournie."):
        if not ctx.guild.me.guild_permissions.ban_members:
            raise discord.ext.commands.BotMissingPermissions(['ban_members'])

        try:
            await ctx.message.delete()
        except Exception:
            pass

        if len(ids) == 0:
            await ctx.send(":x: Veuillez entrer au moins un id !")
            return

        if len(ids) > 30:
            await ctx.send(":x: **Impossible de bannir plus de 30 utilisateurs à la fois.**")
            return

        ban_count = 0
        banned = ""
        notfound = ""
        notbanned = ""
        guild_members = [member.id for member in ctx.guild.members]

        for id in ids:
            userToBan = None
            try:
                userToBan = await self.bot.fetch_user(id)
            except Exception:
                notfound += "{}, ".format(str(id))
                continue

            if id in guild_members:
                notbanned += "{}#{}, ".format(userToBan.name, str(userToBan.discriminator))
                continue

            try:
                await ctx.guild.ban(user=userToBan,
                                    reason="date:{}|mod:{}|reason:{}".format(self.get_date(), str(ctx.author.id),
                                                                             reason))
                banned += "{}#{}, ".format(userToBan.name, str(userToBan.discriminator))
                ban_count += 1
            except Exception as e:
                notbanned += "{}#{}, ".format(userToBan.name, str(userToBan.discriminator))
                pass

        embed = discord.Embed(title="Rapport de bannissement de **{}**".format(ctx.guild.name),
                              description="✅ Utilisateurs bannis : {}".format(
                                  banned[:-2] if len(banned) > 0 else "aucun"), color=0xff0000)
        embed.set_thumbnail(url="https://discordemoji.com/assets/emoji/BlurpleBanHammer.png")
        if len(notbanned) > 0:
            embed.add_field(name="❌ Utilisateurs non-bannis :", value=notbanned[:-2], inline=False)
        if len(notfound) > 0:
            embed.add_field(name="❓ Utilisateurs introuvables :", value=notfound[:-2], inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    @commands.cooldown(3, 3 * 60, type=commands.BucketType.guild)
    async def unban(self, ctx, id):
        try:
            id = int(id)
        except Exception as e:
            await ctx.send(":x: Veuillez entrer un id valide !")
            return

        if not ctx.guild.me.guild_permissions.ban_members:
            raise discord.ext.commands.BotMissingPermissions(['ban_members'])

        bans = await ctx.guild.bans()
        result = [x for x in bans if x[1].id == id]
        if len(result) > 0:
            un_user = result[0][1]

            await ctx.message.delete()
            embedC = discord.Embed(title="🛑 Confirmation",
                                   description="Révoquer le bannissement de {}#{} ?".format(un_user.name,
                                                                                            str(un_user.discriminator)),
                                   color=0xff0000)
            embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
            embedC.set_thumbnail(url=un_user.avatar_url_as(format='gif' if un_user.is_avatar_animated() else 'jpg'))
            confirm = await ctx.send(embed=embedC)
            await confirm.add_reaction(emoji='✅')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) == '✅'

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            else:

                try:
                    await confirm.clear_reactions()
                except Exception:
                    pass

                try:
                    await ctx.guild.unban(user=un_user, reason="Révoqué par {}#{} ({})".format(ctx.author.name, str(
                        ctx.author.discriminator), str(ctx.author.id)))
                    await confirm.edit(embed=discord.Embed(title="✅ Succès !", color=0xff8000))
                except Exception:
                    await confirm.edit(
                        embed=discord.Embed(title=":x: Impossible de révoquer ce bannissement. Veuillez réessayer.",
                                            color=0xff0000))
                    pass
        else:
            embed = discord.Embed(title=":x: L'utilisateur d'id **{}** n'est pas banni de ce serveur.".format(str(id)),
                                  color=0xff8000)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    @commands.cooldown(3, 3 * 60, type=commands.BucketType.guild)
    async def isbanned(self, ctx, id):
        try:
            id = int(id)
        except Exception as e:
            await ctx.send(":x: Veuillez entrer un id valide !")
            return

        if not ctx.guild.me.guild_permissions.ban_members:
            raise discord.ext.commands.BotMissingPermissions(['ban_members'])

        bans = await ctx.guild.bans()
        result = [x for x in bans if x[1].id == id]
        embed = discord.Embed()
        if len(result) > 0:
            embed = discord.Embed(
                title=":x: **L'utilisateur {}#{} ({}) est banni du serveur !**".format(result[0][1].name,
                                                                                       str(result[0][1].discriminator),
                                                                                       str(id)), color=0xff0000)

            data = result[0][0]
            for x in ['date:', 'mod:', 'reason:']:
                data = data.replace(x, '')
            data = data.split('|')
            if len(data) > 1:
                e = data[0].split('/')
                e += e[len(e) - 1].split(', ')
                del e[len(e) - 3]
                e += e[len(e) - 1].split('h')
                del e[len(e) - 3]
                e = [int(x) for x in e]

                embed.add_field(name="Date",
                                value=data[0] + '\n' + self.get_time_spent(datetime(e[2], e[1], e[0], e[3], e[4])),
                                inline=True)
                try:
                    mod = await self.bot.fetch_user(int(data[1]))
                    embed.add_field(name="Modérateur",
                                    value="{}#{} ({})".format(mod.name, str(mod.discriminator), data[1]), inline=True)
                except Exception:
                    embed.add_field(name="Modérateur", value=data[1], inline=True)
                embed.add_field(name="Raison", value=data[2], inline=False)
            else:
                embed.add_field(name="Raison", value=result[0][0], inline=False)
        else:
            embed = discord.Embed(
                title=":white_check_mark: L'utilisateur d'id **{}** n'est pas banni de ce serveur.".format(str(id)),
                color=0x008000)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.cooldown(1, 10 * 60, type=commands.BucketType.guild)
    async def rainbow(self, ctx):
        bRole = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
        if bRole is None:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'a pas été trouvé !",
                                  description="Merci de le renommer en `GuildEdit`.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if bRole.position != len(ctx.guild.roles) - 1:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'est pas le plus haut !",
                                  description="Merci de le déplacer tout en haut.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        embedC = discord.Embed(title="🌈 Un serveur multicolore",
                               description="Attention, cela va restaurer la couleur par défaut pour tous vos rôles.\nConfirmer ?",
                               color=0x8000ff)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        for r in ctx.guild.roles:
            if r.name.find("rainbow") > -1:
                embed = discord.Embed(title="❌ Erreur", description="Il ya déjà des rôles rainbow !", color=0xff8000)
                await ctx.message.delete()
                response = await ctx.send(embed=embed)
                await asyncio.sleep(3)
                await response.delete()
                return

        for r in ctx.guild.roles:
            if r.name != self.bot.user.name and r != ctx.guild.default_role:
                await r.edit(color=discord.Colour.default())

        colours = [0xff6666, 0xff8c66, 0xffb366, 0xffd966, 0xffff66, 0xd9ff66, 0xb3ff66, 0x8cff66, 0x66ff66, 0x66ff8c,
                   0x66ffb3, 0x66ffd9, 0x66ffff, 0x66d9ff, 0x66ccff, 0x66b3ff, 0x668cff, 0x6666ff, 0x8c66ff, 0xb366ff,
                   0xd966ff, 0xff66ff]
        for c in colours:
            await ctx.guild.create_role(name="rainbow", colour=discord.Colour(c), reason="RAINBOWWW")

        for m in ctx.guild.members:
            i = random.randint(0, len(colours) - 1)
            role = discord.utils.get(ctx.guild.roles, name="rainbow", colour=discord.Colour(colours[i]))
            await m.add_roles(role)

        await confirm.clear_reactions()
        rembed = discord.Embed(title="🌈 Voilà !", description="Vos salons textuels seront plus coloriés.",
                               color=0x8080ff)
        await confirm.edit(embed=rembed)

        embed2 = discord.Embed(title="Rainbow", description="Le serveur " + ctx.guild.name + " (" + str(
            ctx.guild.id) + ") est désormais coloré", color=0x8000ff)
        embed2.add_field(name="Utilisateur",
                         value=ctx.author.name + "#" + str(ctx.author.discriminator) + " (" + str(ctx.author.id) + ")",
                         inline=False)
        lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
        await lChan.send(embed=embed2)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    async def clearchannel(self, ctx, *, name):
        cCount = 0
        for channel in ctx.message.guild.channels:
            if channel.name == name:
                cCount += 1

        if cCount == 0:
            embed = discord.Embed(title="❌ Erreur", description="Aucun salon détecté !", color=0xff8000)
            await ctx.message.delete()
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        await ctx.message.delete()
        embedC = discord.Embed(title="🛑 Confirmation", description="Êtes-vous sûr de vouloir supprimer les " + str(
            cCount) + " salons " + name + " ?", color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
        else:
            deleted_channels = 0
            for channel in ctx.message.guild.channels:
                if channel.name == name:
                    await channel.delete()
                    deleted_channels += 1

            await confirm.clear_reactions()
            embedE = discord.Embed(title="✅ Terminé !",
                                   description="Les {} salons ont bien été supprimés !".format(str(deleted_channels)),
                                   color=0x008000)
            await confirm.edit(embed=embedE)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    async def clearrole(self, ctx, *, name):
        bRole = discord.utils.get(ctx.message.guild.roles, name=self.bot.user.name)
        if bRole is None:
            embed = discord.Embed(title="❌ Le rôle du bot n'a pas été trouvé, veuillez le renommer en `GuildEdit`.",
                                  color=0xff8000)
            await ctx.message.delete()
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        rCount = 0
        for role in ctx.message.guild.roles:
            if role.name == name and role != ctx.message.guild.default_role and not role.managed and role < bRole:
                rCount += 1

        if rCount == 0:
            embed = discord.Embed(title="❌ Erreur",
                                  description="Aucun rôle détecté ! Veuiller vérifier la position de mon rôle.\n*Note : les rôles intégrés ne peuvent pas être supprimés avec cette commande.*",
                                  color=0xff8000)
            await ctx.message.delete()
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        await ctx.message.delete()
        embedC = discord.Embed(title="🛑 Confirmation", description="Êtes-vous sûr de vouloir supprimer les " + str(
            rCount) + " roles " + name + " ?", color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
        else:
            deleted_roles = 0
            for i in range(round(rCount / 2)):
                for role in ctx.message.guild.roles:
                    if role.name == name and role != ctx.message.guild.default_role and not role.managed and role < bRole:
                        try:
                            await role.delete()
                            deleted_roles += 1
                        except Exception:
                            pass

            await confirm.clear_reactions()
            embedE = discord.Embed(title="✅ Terminé !",
                                   description="Les {} roles ont bien été supprimés !".format(str(deleted_roles)),
                                   color=0x008000)
            await confirm.edit(embed=embedE)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    async def masskick(self, ctx, *, name):
        bRole = discord.utils.get(ctx.message.guild.roles, name=self.bot.user.name)
        if bRole is None:
            embed = discord.Embed(title="❌ Le rôle du bot n'a pas été trouvé, veuillez le renommer en `GuildEdit`.",
                                  color=0xff8000)
            await ctx.message.delete()
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        mCount = 0
        for member in ctx.message.guild.members:
            if member.name == name and member != self.bot.user and self.has_higher_permissions(ctx.author,
                                                                                               member) and member.top_role < bRole:
                mCount += 1

        if mCount == 0:
            embed = discord.Embed(title="❌ Erreur",
                                  description="Aucun membre détecté ! Les membres possédant ce pseudo ne sont pas pris en compte s'ils sont plus haut gradés que vous.\nMon rôle doit également être au dessus de ceux des utilisateurs concernés.",
                                  color=0xff8000)
            await ctx.message.delete()
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        await ctx.message.delete()
        embedC = discord.Embed(title="🛑 Confirmation",
                               description="Êtes-vous sûr de vouloir expulser les " + str(mCount) + " membres " + chr(
                                   34) + name + chr(34) + " ?", color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
        else:
            kicked_members = 0
            for member in ctx.message.guild.members:
                if member.name == name and member != self.bot.user and self.has_higher_permissions(ctx.author,
                                                                                                   member) and member.top_role < bRole:
                    try:
                        await ctx.message.guild.kick(user=member, reason=">masskick par {}#{}".format(ctx.author.name,
                                                                                                      str(
                                                                                                          ctx.author.discriminator)))
                        kicked_members += 1
                    except Exception:
                        pass

            await confirm.clear_reactions()
            embedE = discord.Embed(title="✅ Terminé !",
                                   description="Les {} membres ont bien été expulsés !".format(str(kicked_members)),
                                   color=0x008000)
            await confirm.edit(embed=embedE)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.guild)
    async def massban(self, ctx, *, name):
        bRole = discord.utils.get(ctx.message.guild.roles, name=self.bot.user.name)
        if bRole is None:
            embed = discord.Embed(title="❌ Le rôle du bot n'a pas été trouvé, veuillez le renommer en `GuildEdit`.",
                                  color=0xff8000)
            await ctx.message.delete()
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        mCount = 0
        for member in ctx.message.guild.members:
            if member.name == name and member != self.bot.user and self.has_higher_permissions(ctx.author,
                                                                                               member) and member.top_role < bRole:
                mCount += 1

        if mCount == 0:
            embed = discord.Embed(title="❌ Erreur",
                                  description="Aucun membre détecté ! Les membres possédant ce pseudo ne sont pas pris en compte s'ils sont plus haut gradés que vous.\nMon rôle doit également être au dessus de ceux des utilisateurs concernés.",
                                  color=0xff8000)
            await ctx.message.delete()
            response = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await response.delete()
            return

        await ctx.message.delete()
        embedC = discord.Embed(title="🛑 Confirmation",
                               description="Êtes-vous sûr de vouloir bannir les " + str(mCount) + " membres " + chr(
                                   34) + name + chr(34) + " ?", color=0xff0000)
        embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 1min.", inline=False)
        confirm = await ctx.send(embed=embedC)

        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
        else:
            banned_members = 0
            for member in ctx.message.guild.members:
                if member.name == name and member != bot.user and self.has_higher_permissions(ctx.author,
                                                                                              member) and member.top_role < bRole:
                    try:
                        await ctx.message.guild.ban(user=member, reason=">massban par {}#{}".format(ctx.author.name,
                                                                                                    str(
                                                                                                        ctx.author.discriminator)),
                                                    delete_message_days=0)
                        banned_members += 1
                    except Exception:
                        pass

            await confirm.clear_reactions()
            embedE = discord.Embed(title="✅ Terminé !",
                                   description="Les {} membres ont bien été bannis !".format(str(banned_members)),
                                   color=0x008000)
            await confirm.edit(embed=embedE)


def setup(bot):
    bot.add_cog(GuildManage(bot))
