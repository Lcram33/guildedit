from datetime import datetime
from os import listdir, makedirs, remove, rename
from os.path import isfile, join, exists
import discord
import json
import aiohttp
import asyncio
from discord.ext import commands


# Note : cette fonctionnalitée est fortement inspirée du code qui suit :
# https://github.com/LyricLy/Lyric-Selfbot-Cogs/blob/master/serversave.py
# Merci à son auteur, tout crédit lui revient.
# Il a été notament mis à jour, avec certains paramètres qui n'existaient pas encore, comme le cooldown sur les salons par exemple.


class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = bot.cogs["Settings"]

        self.max_count = 3
        self.staff_count = 10
        self.admin_count = 100

    def get_max_count(self, author_id: int):
        if str(author_id) in self.bot.config["Admin"]:
            return self.admin_count
        if str(author_id) in self.bot.config["Staff"]:
            return self.staff_count
        return self.max_count

    def format_datetime(self, date: datetime):
        week = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]
        day = week[int(date.strftime("%w"))]
        return date.strftime("Le %d/%m/%Y ({}) à %Hh%M".format(day))

    def get_filename(self, guild_id: int):
        return datetime.now().strftime("{}-%d-%m-%Y-%H-%M".format(str(guild_id)))

    def embed_error(self, error: str, warn: bool = False):
        return discord.Embed(title=":x: **{}**".format(error), color=0xff0000) if not warn else discord.Embed(
            title=":warning: **{}**".format(error), color=0xffff00)

    def format_name(self, input_name: str):
        forbidden_terms = ["AUTO"]
        for term in forbidden_terms:
            input_name = input_name.replace(term, "")

        e_chars = "éèêë"
        for e in e_chars:
            input_name = input_name.replace(e, "e")

        a_chars = "àâãä"
        for a in a_chars:
            input_name = input_name.replace(a, "a")

        i_chars = "îìï"
        for i in i_chars:
            input_name = input_name.replace(i, "i")

        u_chars = "ùûü"
        for u in u_chars:
            input_name = input_name.replace(u, "u")

        input_name = input_name.replace(" ", "-")
        input_name = input_name.replace("ç", "c")

        char_list = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-0123456789"
        output_name = ""
        for char in input_name:
            if char in char_list:
                output_name += char

        return output_name if len(output_name) > 0 else "nom-incorrect"

    def get_backup_name(self, path: str):
        g = None
        try:
            with open(path, "r", encoding='utf8') as f:
                g = json.load(f)
        except Exception:
            pass
        return g["name"]

    def set_roles_position(self, roles: list):
        new_list = []
        positions = [x["position"] for x in roles]
        while len(positions) > 0:
            new_list.append([x for x in roles if x["position"] == max(positions)][0])
            positions.remove(max(positions))
        return new_list

    async def clean_guild(self, guild: discord.guild):
        for channel in guild.channels:
            await channel.delete()

        for i in range(round(len(guild.roles) / 2)):
            for role in guild.roles:
                try:
                    await role.delete()
                except Exception:
                    pass

    async def load_backup(self, file_path: str, guild: discord.guild, action_reason: str = None):

        with open(file_path, "r", encoding='utf8') as f:
            g = json.load(f)

            backup_roles = []
            if g["backup_date"].startswith("Le"):
                backup_roles = g["roles"][::-1]
            else:
                backup_roles = self.set_roles_position(g["roles"])

            for role in backup_roles:
                permissions = discord.Permissions()
                if type(role["permissions"]) == list:
                    permissions.update(**dict(role["permissions"]))
                else:
                    permissions = discord.Permissions(permissions=role["permissions"])

                if role["name"] != "@everyone":
                    await guild.create_role(name=role["name"], colour=discord.Colour.from_rgb(*role["colour"]) if type(
                        role["colour"]) == list else discord.Colour(role["colour"]), hoist=role["hoist"],
                                            mentionable=role["mentionable"], permissions=permissions,
                                            reason=action_reason)
                else:
                    await guild.default_role.edit(permissions=permissions, reason=action_reason)

            for category in g["categories"]:
                overwrites = []
                for overwrite in category["overwrites"]:
                    if overwrite["type"] == "role":
                        if overwrite["name"] not in [x.name for x in guild.roles]:
                            pass
                        else:
                            role = [x for x in guild.roles if x.name == overwrite["name"]][0]
                            permissions = discord.PermissionOverwrite()
                            if type(overwrite["permissions"]) == list:
                                permissions.update(**dict(overwrite["permissions"]))
                            else:
                                permissions.update(**dict(discord.Permissions(permissions=overwrite["permissions"])))
                            overwrites.append((role, permissions))
                    else:
                        if "name" in overwrite:
                            if overwrite["name"] not in [x.name for x in guild.members]:
                                pass
                            else:
                                member = [x for x in guild.members if x.name == overwrite["name"]][0]
                                permissions = discord.PermissionOverwrite()
                                if type(overwrite["permissions"]) == list:
                                    permissions.update(**dict(overwrite["permissions"]))
                                else:
                                    permissions.update(
                                        **dict(discord.Permissions(permissions=overwrite["permissions"])))
                                overwrites.append((member, permissions))
                        else:
                            if overwrite["id"] not in [str(x.id) for x in guild.members]:
                                pass
                            else:
                                member = [x for x in guild.members if str(x.id) == overwrite["id"]][0]
                                permissions = discord.PermissionOverwrite()
                                if type(overwrite["permissions"]) == list:
                                    permissions.update(**dict(overwrite["permissions"]))
                                else:
                                    permissions.update(
                                        **dict(discord.Permissions(permissions=overwrite["permissions"])))
                                overwrites.append((member, permissions))

                await guild.create_category(category["name"], overwrites=dict(overwrites), reason=action_reason)

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
                            if type(overwrite["permissions"]) == list:
                                permissions.update(**dict(overwrite["permissions"]))
                            else:
                                permissions.update(**dict(discord.Permissions(permissions=overwrite["permissions"])))
                            overwrites.append((role, permissions))
                    else:
                        if "name" in overwrite:
                            if overwrite["name"] not in [x.name for x in guild.members]:
                                pass
                            else:
                                member = [x for x in guild.members if x.name == overwrite["name"]][0]
                                permissions = discord.PermissionOverwrite()
                                if type(overwrite["permissions"]) == list:
                                    permissions.update(**dict(overwrite["permissions"]))
                                else:
                                    permissions.update(
                                        **dict(discord.Permissions(permissions=overwrite["permissions"])))
                                overwrites.append((member, permissions))
                        else:
                            if overwrite["id"] not in [str(x.id) for x in guild.members]:
                                pass
                            else:
                                member = [x for x in guild.members if str(x.id) == overwrite["id"]][0]
                                permissions = discord.PermissionOverwrite()
                                if type(overwrite["permissions"]) == list:
                                    permissions.update(**dict(overwrite["permissions"]))
                                else:
                                    permissions.update(
                                        **dict(discord.Permissions(permissions=overwrite["permissions"])))
                                overwrites.append((member, permissions))

                new_chan = await guild.create_text_channel(channel["name"], overwrites=dict(overwrites),
                                                           reason=action_reason)
                await new_chan.edit(topic=channel["topic"], nsfw=channel["nsfw"], category=category,
                                    slowmode_delay=channel["slowmode_delay"], reason=action_reason)

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
                            if type(overwrite["permissions"]) == list:
                                permissions.update(**dict(overwrite["permissions"]))
                            else:
                                permissions.update(**dict(discord.Permissions(permissions=overwrite["permissions"])))
                            overwrites.append((role, permissions))
                    else:
                        if "name" in overwrite:
                            if overwrite["name"] not in [x.name for x in guild.members]:
                                pass
                            else:
                                member = [x for x in guild.members if x.name == overwrite["name"]][0]
                                permissions = discord.PermissionOverwrite()
                                if type(overwrite["permissions"]) == list:
                                    permissions.update(**dict(overwrite["permissions"]))
                                else:
                                    permissions.update(
                                        **dict(discord.Permissions(permissions=overwrite["permissions"])))
                                overwrites.append((member, permissions))
                        else:
                            if overwrite["id"] not in [str(x.id) for x in guild.members]:
                                pass
                            else:
                                member = [x for x in guild.members if str(x.id) == overwrite["id"]][0]
                                permissions = discord.PermissionOverwrite()
                                if type(overwrite["permissions"]) == list:
                                    permissions.update(**dict(overwrite["permissions"]))
                                else:
                                    permissions.update(
                                        **dict(discord.Permissions(permissions=overwrite["permissions"])))
                                overwrites.append((member, permissions))

                new_chan = await guild.create_voice_channel(channel["name"], overwrites=dict(overwrites),
                                                            reason=action_reason)
                await new_chan.edit(
                    bitrate=channel["bitrate"] if channel["bitrate"] <= 96000 and channel["bitrate"] >= 8000 else 64000,
                    user_limit=channel["user_limit"], category=category, reason=action_reason)

            for channel in g["text_channels"]:
                await [x for x in guild.text_channels if x.name == channel["name"]][0].edit(
                    position=channel["position"] if channel["position"] < len(guild.text_channels) else len(
                        guild.text_channels) - 1, reason=action_reason)

            for channel in g["voice_channels"]:
                await [x for x in guild.voice_channels if x.name == channel["name"]][0].edit(
                    position=channel["position"] if channel["position"] < len(guild.voice_channels) else len(
                        guild.voice_channels) - 1, reason=action_reason)

            for category in g["categories"]:
                await [x for x in guild.categories if x.name == category["name"]][0].edit(
                    position=category["position"] if category["position"] < len(guild.categories) else len(
                        guild.categories) - 1, reason=action_reason)

            guild_bans = [ban_entry[1] for ban_entry in await guild.bans()]
            backup_bans = []
            backup_reasons = []
            for ban_entry in g["bans"]:
                try:
                    user = await self.bot.fetch_user(ban_entry["id"])
                    backup_bans.append(user)
                    backup_reasons.append(ban_entry["reason"])
                except Exception:
                    pass

            for user in guild_bans:
                if not user in backup_bans:
                    try:
                        await guild.unban(user, reason=action_reason)
                    except Exception:
                        pass

            for user in backup_bans:
                if not user in guild_bans:
                    try:
                        await guild.ban(user=user, reason=backup_reasons[backup_bans.index(user)])
                    except Exception:
                        pass

            for member in g["members"]:
                guild_member = guild.get_member(int(member["id"]))
                if guild_member is not None and guild_member != guild.me:
                    member_roles = [discord.utils.get(guild.roles, name=role_name) for role_name in member["roles"]]
                    member_roles = [m_r for m_r in member_roles if m_r is not None and not m_r.managed]
                    for role in member_roles:
                        await guild_member.add_roles(role, reason=action_reason)

                    if "nick" in member and guild_member != guild.owner and guild_member.nick != member["nick"]:
                        await guild_member.edit(nick=member["nick"], reason=action_reason)

            guild_icon = None
            try:
                async with aiohttp.ClientSession() as ses:
                    async with ses.get(g["icon"]) as r:
                        guild_icon = await r.read()
            except Exception:
                pass

            await guild.edit(name=g["name"], region=discord.VoiceRegion(g["region"]),
                             afk_channel=[x for x in guild.voice_channels if x.name == g["afk_channel"]][0] if g[
                                 "afk_channel"] else None, afk_timeout=g["afk_timeout"],
                             verification_level=discord.VerificationLevel(g["verification_level"]),
                             default_notifications=discord.NotificationLevel.only_mentions if g[
                                                                                                  "default_notifications"] == "only_mentions" else discord.NotificationLevel.all_messages,
                             explicit_content_filter=discord.ContentFilter(g["explicit_content_filter"]),
                             system_channel=[x for x in guild.text_channels if x.name == g["system_channel"]][0] if g[
                                 "system_channel"] else None, reason=action_reason)

            try:
                await guild.edit(icon=guild_icon, reason=action_reason)
            except Exception:
                pass

            embed = discord.Embed(title="✅ Voilà !",
                                  description="Votre sauvegarde a été chargée, à l'exception des emojis qui vont être prochainement importés.\nCette opération peut être longue et incomplète.\nDésolé si cela est le cas.",
                                  color=0x008040)
            await guild.text_channels[0].send(content="@here", embed=embed)

            backup_emojis = [emoji["name"] for emoji in g["emojis"]]
            for emoji in guild.emojis:
                if not emoji.name in backup_emojis:
                    await emoji.delete(reason=action_reason)

            guild_emojis = [emoji.name for emoji in guild.emojis]
            for emoji in g["emojis"]:
                if emoji["name"] in guild_emojis:
                    continue

                try:
                    img = None
                    async with aiohttp.ClientSession() as ses:
                        async with ses.get(emoji["url"]) as r:
                            img = await r.read()
                    await guild.create_custom_emoji(name=emoji["name"], image=img, reason=action_reason)
                except Exception:
                    pass

    async def create_backup(self, file_path: str, guild: discord.Guild):
        saved_guild = {
            "name": guild.name,
            "region": str(guild.region),
            "afk_timeout": guild.afk_timeout,
            "afk_channel": guild.afk_channel.name if guild.afk_channel else None,
            "system_channel": guild.system_channel.name if guild.system_channel else None,
            "icon": str(guild.icon_url),
            "verification_level": ["none", "low", "medium", "high", "extreme"].index(
                str(guild.verification_level)),
            "default_notifications": "only_mentions" if guild.default_notifications == discord.NotificationLevel.only_mentions else "all_messages",
            "explicit_content_filter": ["disabled", "no_role", "all_members"].index(str(guild.explicit_content_filter)),
            "roles": [],
            "categories": [],
            "text_channels": [],
            "voice_channels": [],
            "emojis": [],
            "bans": [],
            "members": [],
            "backup_date": self.format_datetime(datetime.now())
        }

        for role in guild.roles:
            if role.managed:
                continue

            role_dict = {
                "name": role.name,
                "permissions": list(role.permissions),
                "colour": role.colour.to_rgb(),
                "hoist": role.hoist,
                "position": role.position,
                "mentionable": role.mentionable
            }

            saved_guild["roles"].append(role_dict)

        for category in guild.categories:
            category_dict = {
                "name": category.name,
                "position": category.position,
                "channels": [],
                "overwrites": []
            }

            for channel in category.channels:
                category_dict["channels"].append(channel.name)

            for overwrite in category.overwrites:
                overwrite_dict = {
                    "name": overwrite.name,
                    "permissions": list(category.overwrites_for(overwrite)),
                    "type": "member" if type(overwrite) == discord.Member else "role"
                }

                category_dict["overwrites"].append(overwrite_dict)

            saved_guild["categories"].append(category_dict)

        for channel in guild.text_channels:
            channel_dict = {
                "name": channel.name,
                "topic": channel.topic,
                "position": channel.position,
                "sync_permissions": channel.permissions_synced,
                "slowmode_delay": channel.slowmode_delay,
                "nsfw": channel.is_nsfw(),
                "overwrites": [],
                "category": channel.category.name if channel.category else None
            }

            for overwrite in channel.overwrites:
                overwrite_dict = {
                    "name": overwrite.name,
                    "permissions": list(channel.overwrites_for(overwrite)),
                    "type": "member" if type(overwrite) == discord.Member else "role"
                }

                channel_dict["overwrites"].append(overwrite_dict)

            saved_guild["text_channels"].append(channel_dict)

        for channel in guild.voice_channels:
            channel_dict = {
                "name": channel.name,
                "position": channel.position,
                "sync_permissions": channel.permissions_synced,
                "user_limit": channel.user_limit,
                "bitrate": channel.bitrate,
                "overwrites": [],
                "category": channel.category.name if channel.category else None
            }

            for overwrite in channel.overwrites:
                overwrite_dict = {
                    "name": overwrite.name,
                    "permissions": list(channel.overwrites_for(overwrite)),
                    "type": "member" if type(overwrite) == discord.Member else "role"
                }

                channel_dict["overwrites"].append(overwrite_dict)

            saved_guild["voice_channels"].append(channel_dict)

        for emoji in guild.emojis:
            emoji_dict = {
                "name": emoji.name,
                "url": str(emoji.url)
            }

            saved_guild["emojis"].append(emoji_dict)

        for ban in await guild.bans():
            ban_dict = {
                "id": ban[1].id,
                "reason": ban[0]
            }

            saved_guild["bans"].append(ban_dict)

        for member in guild.members:
            if member == guild.me:
                continue

            if len(member.roles) == 0 and member.nick is None:
                continue

            member_dict = {
                "id": member.id,
                "nick": member.nick,
                "roles": [role.name for role in member.roles if role != guild.default_role]
            }

            saved_guild["members"].append(member_dict)

        with open(file_path, "w+") as f:
            json.dump(saved_guild, f)

    def get_backup_dict(self, path: str):
        g = None
        try:
            with open(path, "r", encoding='utf8') as f:
                g = json.load(f)
        except Exception:
            pass
        return g

    @commands.command()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.user)
    async def roleslist(self, ctx, backup_name):
        path = "./backups/{}/".format(str(ctx.author.id))

        g = self.get_backup_dict(join(path, backup_name + ".json"))
        if g is None:
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        strroles = ""
        for role in g["roles"][::-1]:
            if role["name"] != "@everyone":
                strroles += role["name"] + "\n"

        embed = discord.Embed(title=g["name"],
                              description="Fichier : `{}`\nCréation : **{}**".format(backup_name, g["backup_date"]),
                              color=0x008080)
        embed.set_thumbnail(url=g["icon"])
        embed.add_field(name="Rôles", value=strroles)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.user)
    async def roleinfo(self, ctx, backup_name, role_name):
        path = "./backups/{}/".format(str(ctx.author.id))

        g = self.get_backup_dict(join(path, backup_name + ".json"))
        if g is None:
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        role = [role for role in g["roles"] if role["name"].find(role_name) > -1]
        if len(role) == 0:
            await ctx.send(embed=self.embed_error("Rôle introuvable.", True))
            return

        role = role[0]
        translate_dict = {
            "create_instant_invite": "Créer une invitation",
            "kick_members": "Expulser des membres",
            "ban_members": "Bannir des membres",
            "administrator": "Administrateur",
            "manage_channels": "Gérer les salons",
            "manage_guild": "Gérer le serveur",
            "add_reactions": "Ajouter des réactions",
            "view_audit_log": "Voir les logs du serveur",
            "priority_speaker": "Priority Speaker",
            "read_messages": "Lire les salons textuels",
            "send_messages": "Envoyer des messages",
            "send_tts_messages": "Envoyer des messages TTS",
            "manage_messages": "Gérer les messages",
            "embed_links": "Intégrer des liens",
            "attach_files": "Attacher des fichiers",
            "read_message_history": "Voir les anciens messages",
            "mention_everyone": "Mentionner @everyone",
            "external_emojis": "Utiliser des émojis externes",
            "connect": "Se connecter",
            "speak": "Parler",
            "mute_members": "Rendre des membres muets",
            "deafen_members": "Rendre des membres sourds",
            "move_members": "Déplacer les membres",
            "use_voice_activation": "Utiliser la détection de voix",
            "change_nickname": "Changer de pseudo",
            "manage_nicknames": "Gérer les pseudos",
            "manage_roles": "Gérer les rôles",
            "manage_webhooks": "Gérer les webhooks",
            "manage_emojis": "Gérer les emojis"
        }

        strperms = ""
        role_perms = role["permissions"]
        if type(role["permissions"]) == int:
            role_perms = dict(discord.Permissions(permissions=role["permissions"]))
        for p in role_perms:
            if p[0] in translate_dict and p[1]:
                strperms += translate_dict[p[0]] + "\n"

        role_colour = None
        if type(role["colour"]) == int:
            role_colour = discord.Color(value=role["colour"])
        else:
            role_colour = discord.Color.from_rgb(role["colour"][0], role["colour"][1], role["colour"][2])

        embed = discord.Embed(title=role["name"],
                              description="Fichier : `{}`\nServeur : `{}`\nCréation : **{}**".format(backup_name, g["name"], g["backup_date"]), color=role_colour)
        embed.set_thumbnail(url=g["icon"])
        embed.add_field(name="Mentionable", value="Oui" if role["mentionable"] else "Non", inline=True)
        embed.add_field(name="Affiché séparément", value="Oui" if role["hoist"] else "Non", inline=True)
        embed.add_field(name="Permissions", value="Pas de permissions" if len(strperms) == 0 else strperms, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.user)
    async def channelslist(self, ctx, backup_name):
        path = "./backups/{}/".format(str(ctx.author.id))

        g = self.get_backup_dict(join(path, backup_name + ".json"))
        if g is None:
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        strtext = ""
        for text_channel in g["text_channels"]:
            channel = text_channel["name"]
            if text_channel["category"] is not None:
                channel += " (dans {})".format(text_channel["category"])
            strtext += channel + "\n"

        strvoice = ""
        for voice_channel in g["voice_channels"]:
            channel = voice_channel["name"]
            if voice_channel["category"] is not None:
                channel += " (dans {})".format(voice_channel["category"])
            strvoice += channel + "\n"

        embed = discord.Embed(title=g["name"],
                              description="Fichier : `{}`\nCréation : **{}**".format(backup_name, g["backup_date"]),
                              color=0x008080)
        embed.set_thumbnail(url=g["icon"])
        embed.add_field(name="Salons textuels", value=strtext, inline=False)
        embed.add_field(name="Salons vocaux", value=strvoice, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.user)
    async def backupinfos(self, ctx, backup_name):
        path = "./backups/{}/".format(str(ctx.author.id))

        g = self.get_backup_dict(join(path, backup_name + ".json"))
        if g is None:
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        my_emoji = self.bot.get_emoji(self.bot.config["emojis"]["banhammer"])

        verification_level = ["Aucun", "Faible", "Moyen", "(╯°□°）╯︵ ┻━┻", "┻━┻ ﾐヽ(ಠ益ಠ)ノ彡┻━┻"]
        explicit_content_filter = ["Aucun", "Sans rôles", "Tous les membres"]

        embed = discord.Embed(title=g["name"],
                              description="Fichier : `{}`\nCréation : **{}**".format(backup_name, g["backup_date"]),
                              color=0x008080)
        embed.set_thumbnail(url=g["icon"])
        embed.add_field(name="Caractéristiques",
                        value="💬 {} | 🔊 {} | 🚩 {} | :slight_smile: {} | {} {}".format(str(len(g["text_channels"])),
                                                                                         str(len(g["voice_channels"])),
                                                                                         str(len(g["roles"])),
                                                                                         str(len(g["emojis"])),
                                                                                         str(my_emoji),
                                                                                         str(len(g["bans"]))),
                        inline=True)
        embed.add_field(name="Paramètres", value="""
    Région : `{}`
    AFK : `{} ({})`
    System channel : `{}`
    Niveau de vérification : `{}`
    Notifications : `{}`
    Filtre de contenu explicit : `{}`
        """.format(g["region"], g["afk_channel"],
                   str(int(g["afk_timeout"] / 60)) + "min" if g["afk_timeout"] != 3600 else "1h", g["system_channel"],
                   verification_level[g["verification_level"]],
                   "Tous les messages" if g["default_notifications"] == "all_messages" else "@mentions seulement",
                   explicit_content_filter[g["explicit_content_filter"]]), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 15 * 60, type=commands.BucketType.user)
    @commands.guild_only()
    async def newguild(self, ctx, backup_name):
        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        g = self.get_backup_dict(join(path, backup_name + ".json"))

        embedc = discord.Embed(title=":heavy_plus_sign::package: Recréer ce serveur ?",
                               description="Vous êtes sur le point de recréer le serveur de cette sauvegarde, **{}**.\nÊtes vous sûr ?".format(
                                   g["name"]), color=0xff0000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        linkC = self.bot.get_channel(self.bot.config["linkChannel"])
        gCreator = linkC.guild.get_member(self.bot.config["GuildCreator"])

        await linkC.send("/createguild|{}|{}".format(backup_name, g["icon"]))

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
                await confirm.delete()
                await ctx.message.add_reaction(emoji="📩")
            except Exception as e:
                await ctx.send(
                    ":x: **Impossible de vous envoyer un mp. Les avez-vous activés ?**\n{}".format(ctx.author.mention))
                await ctx.send(msg.content)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def loadbackup(self, ctx, backup_name):
        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if not ctx.guild.me.guild_permissions.administrator:
            raise commands.BotMissingPermissions(['administrator'])
            return

        bRole = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
        if bRole is None:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'a pas été trouvé !",
                                  description="Merci de le renommer en `GuildEdit PRO`.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if bRole.position != len(ctx.guild.roles) - 1:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'est pas le plus !",
                                  description="Merci de le déplacer tout en haut.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        g = self.get_backup_dict(join(path, backup_name + ".json"))

        embedc = discord.Embed(title=":cd::package: Charger cette sauvegarde ?",
                               description="Vous êtes sur le point de recréer le serveur de cette sauvegarde, **{}**, sur celui-ci.\nLe serveur actuel sera écrasé. Cette action définitive.\nÊtes vous sûr ?".format(
                                   g["name"]), color=0xff0000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        try:
            await self.clean_guild(ctx.guild)
            await self.load_backup(join(path, backup_name + ".json"), ctx.guild, "Chargement d'une sauvegarde")
        except Exception as e:
            await ctx.author.send(embed=self.embed_error(str(e)))
            return

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def loadsettings(self, ctx, backup_name):
        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if not ctx.guild.me.guild_permissions.administrator:
            raise commands.BotMissingPermissions(['administrator'])
            return

        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        g = self.get_backup_dict(join(path, backup_name + ".json"))

        embedc = discord.Embed(title=":tools::package: Charger les paramètres ?",
                               description="Vous êtes sur le point de charger les paramètres de cette sauvegarde (serveur : **{}**) sur ce serveur.\nLes paramètres du serveur actuel seront écrasé. Cette action est définitive.\nÊtes vous sûr ?".format(
                                   g["name"]), color=0xff0000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        action_reason = "Chargement des paramètres de la sauvegarde"
        try:
            guild_icon = None
            try:
                async with aiohttp.ClientSession() as ses:
                    async with ses.get(g["icon"]) as r:
                        guild_icon = await r.read()
            except Exception:
                pass

            await ctx.guild.edit(name=g["name"], icon=guild_icon, region=discord.VoiceRegion(g["region"]),
                                 afk_channel=[x for x in ctx.guild.voice_channels if x.name == g["afk_channel"]][0] if
                                 g["afk_channel"] else None, afk_timeout=g["afk_timeout"],
                                 verification_level=discord.VerificationLevel(g["verification_level"]),
                                 default_notifications=discord.NotificationLevel.only_mentions if g[
                                                                                                      "default_notifications"] == "only_mentions" else discord.NotificationLevel.all_messages,
                                 explicit_content_filter=discord.ContentFilter(g["explicit_content_filter"]),
                                 system_channel=[x for x in ctx.guild.text_channels if x.name == g["system_channel"]][
                                     0] if g["system_channel"] else None, reason=action_reason)
        except Exception as e:
            await ctx.send(embed=self.embed_error(str(e)))
            return

        embed = discord.Embed(title="✅ Voilà !", description="Les paramètres ont été importés avec succès.",
                              color=0x008040)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def loadroles(self, ctx, backup_name):
        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if not ctx.guild.me.guild_permissions.administrator:
            raise commands.BotMissingPermissions(['administrator'])
            return

        bRole = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
        if bRole is None:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'a pas été trouvé !",
                                  description="Merci de le renommer en `GuildEdit PRO`.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if bRole.position != len(ctx.guild.roles) - 1:
            await ctx.message.delete()
            embed = discord.Embed(title="⚠️ Le rôle du bot n'est pas le plus !",
                                  description="Merci de le déplacer tout en haut.", color=0xe0db01)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        g = self.get_backup_dict(join(path, backup_name + ".json"))

        embedc = discord.Embed(title=":triangular_flag_on_post::package: Charger les rôles ?",
                               description="Vous êtes sur le point de charger les rôles de cette sauvegarde (serveur : **{}**) sur ce serveur.\nLes rôles du serveur actuel seront écrasé. Cette action est définitive.\nÊtes vous sûr ?".format(
                                   g["name"]), color=0xff0000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        action_reason = "Chargement des rôles de la sauvegarde"
        try:
            for i in range(round(len(ctx.guild.roles) / 2)):
                for role in ctx.guild.roles:
                    try:
                        await role.delete(reason=action_reason)
                    except Exception:
                        pass

            for role in g["roles"][::-1]:
                permissions = discord.Permissions()
                permissions.update(**dict(role["permissions"]))
                if role["name"] != "@everyone":
                    await ctx.guild.create_role(name=role["name"], colour=discord.Colour.from_rgb(*role["colour"]),
                                                hoist=role["hoist"], mentionable=role["mentionable"],
                                                permissions=permissions, reason=action_reason)
                else:
                    await ctx.guild.default_role.edit(permissions=permissions, reason=action_reason)
        except Exception as e:
            await ctx.send(embed=self.embed_error(str(e)))
            return

        embed = discord.Embed(title="✅ Voilà !", description="Les rôles ont été importés avec succès.", color=0x008040)
        await confirm.clear_reactions()
        await confirm.edit(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def loadchannels(self, ctx, backup_name):
        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if not ctx.guild.me.guild_permissions.administrator:
            raise commands.BotMissingPermissions(['administrator'])
            return

        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        g = self.get_backup_dict(join(path, backup_name + ".json"))

        embedc = discord.Embed(title=":speech_balloon::speaker::package: Charger les salons ?",
                               description="Vous êtes sur le point de charger les salons de cette sauvegarde (serveur : **{}**) sur ce serveur.\nLes salons du serveur actuel seront écrasé. Cette action est définitive.\nÊtes vous sûr ?".format(
                                   g["name"]), color=0xff0000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        action_reason = "Chargement des salons de la sauvegarde"
        try:
            for channel in ctx.guild.channels:
                await channel.delete(reason=action_reason)

            for category in g["categories"]:
                new_cat = await ctx.guild.create_category(category["name"], reason=action_reason)

            for channel in g["text_channels"]:
                category = None
                try:
                    category = [x for x in ctx.guild.categories if x.name == channel["category"]][0]
                except:
                    pass
                new_chan = await ctx.guild.create_text_channel(channel["name"], reason=action_reason)
                await new_chan.edit(topic=channel["topic"], nsfw=channel["nsfw"], category=category,
                                    slowmode_delay=channel["slowmode_delay"], reason=action_reason)

            for channel in g["voice_channels"]:
                category = None
                try:
                    category = [x for x in ctx.guild.categories if x.name == channel["category"]][0]
                except:
                    pass
                new_chan = await ctx.guild.create_voice_channel(channel["name"], reason=action_reason)
                await new_chan.edit(
                    channel["bitrate"] if channel["bitrate"] <= 96000 and channel["bitrate"] >= 8000 else 64000,
                    user_limit=channel["user_limit"], category=category, reason=action_reason)

            for channel in g["text_channels"]:
                await [x for x in ctx.guild.text_channels if x.name == channel["name"]][0].edit(
                    position=channel["position"] if channel["position"] < len(ctx.guild.text_channels) else len(
                        ctx.guild.text_channels) - 1, reason=action_reason)

            for channel in g["voice_channels"]:
                await [x for x in ctx.guild.voice_channels if x.name == channel["name"]][0].edit(
                    position=channel["position"] if channel["position"] < len(ctx.guild.voice_channels) else len(
                        ctx.guild.voice_channels) - 1, reason=action_reason)

            for category in g["categories"]:
                await [x for x in ctx.guild.categories if x.name == category["name"]][0].edit(
                    position=category["position"] if category["position"] < len(ctx.guild.categories) else len(
                        ctx.guild.categories) - 1, reason=action_reason)
        except Exception as e:
            await ctx.message.author.send(embed=self.embed_error(str(e)))
            return

        embed = discord.Embed(title="✅ Voilà !", description="Les salons ont été importés avec succès.", color=0x008040)
        await ctx.guild.text_channels[0].send(content=ctx.message.author.mention, embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def loadbans(self, ctx, backup_name):
        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if not ctx.guild.me.guild_permissions.administrator:
            raise commands.BotMissingPermissions(['administrator'])
            return

        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        g = self.get_backup_dict(join(path, backup_name + ".json"))

        my_emoji = self.bot.get_emoji(self.bot.config["emojis"]["banhammer"])
        embedc = discord.Embed(title="{}:package: Charger les bannissements ?".format(str(my_emoji)),
                               description="Vous êtes sur le point de charger les bannissements de cette sauvegarde (serveur : **{}**) sur ce serveur.\nLes bannissements du serveur actuel seront écrasé. Cette action est définitive.\nÊtes vous sûr ?".format(
                                   g["name"]), color=0xff0000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        action_reason = "Chargement des bannissements de la sauvegarde"
        try:
            guild_bans = [ban_entry[1] for ban_entry in await ctx.guild.bans()]
            backup_bans = []
            backup_reasons = []
            for ban_entry in g["bans"]:
                try:
                    user = await self.bot.fetch_user(ban_entry["id"])
                    backup_bans.append(user)
                    backup_reasons.append(ban_entry["reason"])
                except Exception:
                    pass

            for user in guild_bans:
                if not user in backup_bans:
                    try:
                        await ctx.guild.unban(user, reason=action_reason)
                    except Exception:
                        pass

            for user in backup_bans:
                if not user in guild_bans:
                    try:
                        await ctx.guild.ban(user=user, reason=backup_reasons[backup_bans.index(user)])
                    except Exception:
                        pass
        except Exception as e:
            await ctx.send(embed=self.embed_error(str(e)))
            return

        embed = discord.Embed(title="✅ Voilà !", description="Les bannissements ont été importés avec succès.",
                              color=0x008040)
        await confirm.clear_reactions()
        await confirm.edit(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def loademojis(self, ctx, backup_name):
        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if not ctx.guild.me.guild_permissions.administrator:
            raise commands.BotMissingPermissions(['administrator'])
            return

        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        g = self.get_backup_dict(join(path, backup_name + ".json"))

        embedc = discord.Embed(title=":smile::package: Charger les emojis ?",
                               description="Vous êtes sur le point de charger les emojis de cette sauvegarde (serveur : **{}**) sur ce serveur.\nLes emojis du serveur actuel seront écrasé. Cette action est définitive.\nÊtes vous sûr ?".format(
                                   g["name"]), color=0xff0000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        action_reason = "Chargement des emojis de la sauvegarde"
        try:
            backup_emojis = [emoji["name"] for emoji in g["emojis"]]
            for emoji in ctx.guild.emojis:
                if not emoji.name in backup_emojis:
                    await emoji.delete(reason=action_reason)

            guild_emojis = [emoji.name for emoji in ctx.guild.emojis]
            for emoji in g["emojis"]:
                if emoji["name"] in guild_emojis:
                    continue

                try:
                    img = None
                    async with aiohttp.ClientSession() as ses:
                        async with ses.get(emoji["url"]) as r:
                            img = await r.read()
                    await ctx.guild.create_custom_emoji(name=emoji["name"], image=img, reason=action_reason)
                except Exception:
                    pass
        except Exception as e:
            await ctx.send(embed=self.embed_error(str(e)))
            return

        embed = discord.Embed(title="✅ Voilà !", description="Les emojis ont été importés avec succès.", color=0x008040)
        await confirm.clear_reactions()
        await confirm.edit(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def createbackup(self, ctx):
        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if not ctx.guild.me.guild_permissions.administrator:
            raise commands.BotMissingPermissions(['administrator'])
            return

        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            makedirs(path)
        fcount = len([f for f in listdir(path) if isfile(join(path, f))])

        if fcount >= self.get_max_count(ctx.author.id):
            await ctx.send(embed=self.embed_error(
                "Vous ne pouvez pas conserver plus de {} sauvegardes. Veuillez en supprimer une !".format(
                    str(self.get_max_count(ctx.author.id)))))
            return

        embedc = discord.Embed(title=":inbox_tray::package: Créer une sauvegarde ?",
                               description="Il vous reste {} places disponibles.".format(
                                   str(self.get_max_count(ctx.author.id) - fcount)),
                               color=0xff8000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        # try:
        await self.create_backup("{}{}.json".format(path, self.get_filename(ctx.guild.id)), ctx.guild)
        # except Exception as e:
        #    await ctx.send(embed=self.embed_error(str(e)))
        #    return

        await confirm.clear_reactions()
        embed = discord.Embed(title="✅ Voilà !", description="Votre sauvegarde a été créée avec succès.",
                              color=0x008040)
        await confirm.edit(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3 * 60, type=commands.BucketType.guild)
    @commands.guild_only()
    async def updatebackup(self, ctx, backup_name):
        if self.settings.perms_lock(ctx.guild.id) and ctx.author != ctx.guild.owner:
            await ctx.message.delete()
            embed = discord.Embed(title=":warning: Accès refusé",
                                  description="Le propriétaire du serveur a choisi de verrouiller les commandes sensibles telles que celle-ci",
                                  color=0xffff00)
            response = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await response.delete()
            return

        if not ctx.guild.me.guild_permissions.administrator:
            raise commands.BotMissingPermissions(['administrator'])
            return

        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        if ctx.guild.name != self.get_backup_name(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error(
                "Les noms du serveur et du serveur de la sauvegarde ne correspondent pas.\nVeuillez supprimer cette sauvegarde et en créer une autre."))
            return

        embedc = discord.Embed(title=":inbox_tray::package: Mettre à jour `{}` ?".format(backup_name),
                               description="Attention, cette sauvegarde sera écrasée. Une nouvelle sauvegarde va remplacer celle-ci.\nÊtes-vous sûr ?",
                               color=0xff8000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        try:
            await self.create_backup(join(path, backup_name + ".json"), ctx.guild)
        except Exception as e:
            await ctx.send(embed=self.embed_error(str(e)))
            return

        await confirm.clear_reactions()
        embed = discord.Embed(title="✅ Voilà !", description="Votre sauvegarde a été mise à jour avec succès.",
                              color=0x008040)
        await confirm.edit(embed=embed)

    @commands.command()
    @commands.cooldown(1, 2 * 60, type=commands.BucketType.user)
    async def backuplist(self, ctx):
        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Aucune sauvegarde disponible.", True))
            return

        file_list = [f for f in listdir(path) if isfile(join(path, f))]
        if len(file_list) == 0:
            await ctx.send(embed=self.embed_error("Aucune sauvegarde disponible.", True))
            return

        strf_list = "**Utilisation : {}/{}**\n```\n".format(str(len(file_list)), str(self.get_max_count(ctx.author.id)))
        for f in file_list:
            strf_list += f.replace(".json", "") + "\n"
        strf_list += "```"

        embed = discord.Embed(title=":package: Liste des sauvegardes", description=strf_list, color=0x008080)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(2, 3 * 60, type=commands.BucketType.user)
    async def renamebackup(self, ctx, backup_name, new_name):
        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        new_name = self.format_name(new_name)
        if len(new_name) < 1 or len(new_name) > 50:
            await ctx.send(
                embed=self.embed_error("Nom invalide. Il doit comporter entre 1 et 50 caractères, non spéciaux.", True))
            return

        embedc = discord.Embed(title=":pen_ballpoint::package: Renommer cette sauvegarde ?",
                               description="`{}` sera renommée en `{}`.\nÊtes vous sûr ?".format(backup_name, new_name),
                               color=0xff8000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        rename(join(path, backup_name + ".json"), join(path, new_name + ".json"))

        try:
            await confirm.clear_reactions()
        except Exception:
            pass

        embed = discord.Embed(title="✅ Succès.", description="Votre sauvegarde a bien été renommée.", color=0x008040)
        await confirm.edit(embed=embed)

    @commands.command()
    @commands.cooldown(2, 3 * 60, type=commands.BucketType.user)
    async def deletebackup(self, ctx, backup_name):
        path = "./backups/{}/".format(str(ctx.author.id))
        if not exists(path):
            await ctx.send(embed=self.embed_error("Fichier introuvable.", True))
            return

        if not isfile(join(path, backup_name + ".json")):
            await ctx.send(embed=self.embed_error("Fichier introuvable."))
            return

        embedc = discord.Embed(title=":outbox_tray::package: Supprimer cette sauvegarde ?",
                               description="`{}` sera supprimée définitivement.\nÊtes vous sûr ?".format(backup_name),
                               color=0xff0000)
        confirm = await ctx.send(embed=embedc)
        await confirm.add_reaction(emoji='✅')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '✅'

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
            return

        remove(join(path, backup_name + ".json"))

        try:
            await confirm.clear_reactions()
        except Exception:
            pass

        embed = discord.Embed(title="✅ Succès.", description="Votre sauvegarde a bien été supprimée.", color=0x008040)
        await confirm.edit(embed=embed)


def setup(bot):
    bot.add_cog(Backup(bot))
