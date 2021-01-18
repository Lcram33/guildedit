import discord
from discord.ext import commands
from datetime import datetime
from datetime import timedelta


class Heuristic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = bot.cogs["Settings"]

        self.delay = 3
        self.raid_warn = []
        self.last_created_channel = []
        self.last_deleted_channel = []
        self.last_created_role = []
        self.last_deleted_role = []
        self.last_bot_message = []

    def check_message_content(self, message: str):
        terms = ["discord.gg/", "discordapp.com/invite/", "@here", "@everyone"]
        for t in terms:
            if message.find(t) > -1:
                return True
        return False

    def check_last_created_channel(self, guildID: int, name: str, cID: int):
        for e in self.last_created_channel:
            if e["gID"] == guildID:
                if datetime.now() - e["date"] < timedelta(days=0, hours=0, minutes=0, seconds=self.delay) or e[
                    "name"] == name:
                    return e["cID"]
                self.last_created_channel.remove(e)
        entry = {
            "gID": guildID,
            "name": name,
            "date": datetime.now(),
            "cID": cID
        }
        self.last_created_channel.append(entry)
        return None

    def check_last_created_role(self, guildID: int, name: str, rID: int):
        for e in self.last_created_role:
            if e["gID"] == guildID:
                if datetime.now() - e["date"] < timedelta(days=0, hours=0, minutes=0, seconds=self.delay) or e[
                    "name"] == name:
                    return e["rID"]
                self.last_created_role.remove(e)
        entry = {
            "gID": guildID,
            "name": name,
            "date": datetime.now(),
            "rID": rID
        }
        self.last_created_role.append(entry)
        return None

    def check_last_deleted_role(self, guildID: int):
        for e in self.last_deleted_role:
            if e["gID"] == guildID:
                if datetime.now() - e["date"] < timedelta(days=0, hours=0, minutes=0, seconds=self.delay):
                    return True
                self.last_deleted_role.remove(e)
        entry = {
            "gID": guildID,
            "date": datetime.now()
        }
        self.last_deleted_role.append(entry)
        return False

    def check_last_deleted_channel(self, guildID: int):
        for e in self.last_deleted_channel:
            if e["gID"] == guildID:
                if datetime.now() - e["date"] < timedelta(days=0, hours=0, minutes=0, seconds=self.delay):
                    return True
                self.last_deleted_channel.remove(e)
        entry = {
            "gID": guildID,
            "date": datetime.now()
        }
        self.last_deleted_channel.append(entry)
        return False

    def check_last_bot_message(self, guildID: int):
        for e in self.last_bot_message:
            if e["gID"] == guildID:
                if datetime.now() - e["date"] < timedelta(days=0, hours=0, minutes=0, seconds=self.delay):
                    return True
                self.last_bot_message.remove(e)
        entry = {
            "gID": guildID,
            "date": datetime.now()
        }
        self.last_bot_message.append(entry)
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if not isinstance(message.channel, discord.DMChannel) and message.author.bot:
            if not self.settings.heuristic(message.guild.id):
                return

            if message.author.id in self.settings.ignored_bots():
                return

            if not self.check_message_content(message.content):
                return

            if not self.check_last_bot_message(message.guild.id):
                return

            banned = None
            try:
                await message.guild.ban(user=message.author, reason="Spam mentions et invitations.")
                banned = "✅ Le bot a été automatiquement banni."
            except Exception:
                pass

            if banned is not None:
                try:
                    await message.delete()
                except Exception:
                    pass
            else:
                banned = "❌ Le bot n'a pas put être banni : permissions insuffisantes."

            try:
                if message.guild.id in self.raid_warn:
                    return
                self.raid_warn.append(message.guild.id)

                for m in message.guild.members:
                    if m.guild_permissions.administrator and not m.bot:
                        try:
                            await m.send(
                                ":warning: Le bot __{}#{}__ ({}) a été détecté (détection heuristique) comme bot de raid sur le serveur **{}** où vous êtes administrateur pour la cause suivante : `Spam mentions et invitations`.\nPour désactiver cette fonctionnalité : `>hmode`\n{}".format(
                                    message.author.name, str(message.author.discriminator), str(message.author.id),
                                    message.guild.name, banned))
                        except Exception:
                            pass

                embed = discord.Embed(title="Détection d'un raid (heuristique)",
                                      description="Spam mentions et invitations", color=0xff0000)
                embed.set_thumbnail(
                    url="https://images.vexels.com/media/users/3/136844/isolated/preview/11a79246e95fb4ad3b097b5e0dbf0328-skull-bones-circle-icon-by-vexels.png")
                embed.add_field(name="Serveur", value="{} ({})".format(message.guild.name, str(message.guild.id)),
                                inline=False)
                embed.add_field(name="Bot",
                                value="{}#{} ({})".format(message.author.name, str(message.author.discriminator),
                                                          str(message.author.id)), inline=False)
                embed.add_field(name="Résultat", value=banned, inline=False)

                lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
                supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])
                botNotif = [x for x in supguild.roles if x.name == "botNotif"][0]

                await lChan.send(content=botNotif.mention, embed=embed)
                self.bot.stats["blocked_raids"] += 1
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if not self.settings.heuristic(role.guild.id):
            return

        if role.managed:
            return

        member = None
        try:
            async for a in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                member = a.user
        except Exception:
            return

        if not member.bot:
            return

        if member == self.bot.user:
            return

        if member.id in self.settings.ignored_bots():
            return

        result = self.check_last_deleted_role(role.guild.id)
        if result == True:
            banned = None

            try:
                await role.guild.ban(user=member, reason="Suppression de masse de rôles.")
                banned = "✅ Le bot a été automatiquement banni."
            except Exception:
                banned = "❌ Le bot n'a pas put être banni : permissions insuffisantes."
                pass

            try:
                if role.guild.id in self.raid_warn:
                    return
                self.raid_warn.append(role.guild.id)

                for m in role.guild.members:
                    if m.guild_permissions.administrator and not m.bot:
                        try:
                            await m.send(
                                ":warning: Le bot __{}#{}__ ({}) a été détecté (détection heuristique) comme bot de raid sur le serveur **{}** où vous êtes administrateur pour la cause suivante : `Suppression de masse de rôles`.\nPour désactiver cette fonctionnalité : `>hmode`\n{}".format(
                                    member.name, str(member.discriminator), str(member.id), role.guild.name, banned))
                        except Exception:
                            pass

                embed = discord.Embed(title="Détection d'un raid (heuristique)", description="Suppression de rôles",
                                      color=0xff0000)
                embed.set_thumbnail(
                    url="https://images.vexels.com/media/users/3/136844/isolated/preview/11a79246e95fb4ad3b097b5e0dbf0328-skull-bones-circle-icon-by-vexels.png")
                embed.add_field(name="Serveur", value="{} ({})".format(role.guild.name, str(role.guild.id)),
                                inline=False)
                embed.add_field(name="Bot",
                                value="{}#{} ({})".format(member.name, str(member.discriminator), str(member.id)),
                                inline=False)
                embed.add_field(name="Résultat", value=banned, inline=False)

                lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
                supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])
                botNotif = [x for x in supguild.roles if x.name == "botNotif"][0]

                await lChan.send(content=botNotif.mention, embed=embed)
                self.bot.stats["blocked_raids"] += 1
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if not self.settings.heuristic(role.guild.id):
            return

        if role.managed:
            return

        member = None
        try:
            async for a in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                member = a.user
        except Exception:
            return

        if not member.bot:
            return

        if member == self.bot.user:
            return

        if member.id in self.settings.ignored_bots():
            return

        result = self.check_last_created_role(role.guild.id, role.name, role.id)
        if isinstance(result, int):
            banned = None

            try:
                await role.guild.ban(user=member, reason="Création de masse de rôles.")
                banned = "✅ Le bot a été automatiquement banni."
            except Exception:
                pass

            if banned is not None:
                try:
                    r2 = role.guild.get_role(result)
                    await role.delete()
                    await r2.delete()
                except Exception:
                    pass
            else:
                banned = "❌ Le bot n'a pas put être banni : permissions insuffisantes."
        else:
            return

        try:
            if role.guild.id in self.raid_warn:
                return
            self.raid_warn.append(role.guild.id)

            for m in role.guild.members:
                if m.guild_permissions.administrator and not m.bot:
                    try:
                        await m.send(
                            ":warning: Le bot __{}#{}__ ({}) a été détecté (détection heuristique) comme bot de raid sur le serveur **{}** où vous êtes administrateur pour la cause suivante : `Création de masse de rôles`.\nPour désactiver cette fonctionnalité : `>hmode`\n{}".format(
                                member.name, str(member.discriminator), str(member.id), role.guild.name, banned))
                    except Exception:
                        pass

            embed = discord.Embed(title="Détection d'un raid (heuristique)", description="Création de rôles",
                                  color=0xff0000)
            embed.set_thumbnail(
                url="https://images.vexels.com/media/users/3/136844/isolated/preview/11a79246e95fb4ad3b097b5e0dbf0328-skull-bones-circle-icon-by-vexels.png")
            embed.add_field(name="Serveur", value="{} ({})".format(role.guild.name, str(role.guild.id)), inline=False)
            embed.add_field(name="Bot",
                            value="{}#{} ({})".format(member.name, str(member.discriminator), str(member.id)),
                            inline=False)
            embed.add_field(name="Résultat", value=banned, inline=False)

            lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
            supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])
            botNotif = [x for x in supguild.roles if x.name == "botNotif"][0]

            await lChan.send(content=botNotif.mention, embed=embed)
            self.bot.stats["blocked_raids"] += 1
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not self.settings.heuristic(channel.guild.id):
            return

        member = None
        try:
            async for a in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                member = a.user
        except Exception:
            return

        if not member.bot:
            return

        if member == self.bot.user:
            return

        if member.id in self.settings.ignored_bots():
            return

        result = self.check_last_deleted_channel(channel.guild.id)
        if result == True:
            banned = None

            try:
                await channel.guild.ban(user=member, reason="Suppression de masse de salons.")
                banned = "✅ Le bot a été automatiquement banni."
            except Exception:
                banned = "❌ Le bot n'a pas put être banni : permissions insuffisantes."
                pass

            try:
                if channel.guild.id in self.raid_warn:
                    return
                self.raid_warn.append(channel.guild.id)

                for m in channel.guild.members:
                    if m.guild_permissions.administrator and not m.bot:
                        try:
                            await m.send(
                                ":warning: Le bot __{}#{}__ ({}) a été détecté (détection heuristique) comme bot de raid sur le serveur **{}** où vous êtes administrateur pour la cause suivante : `Suppression de masse de salons`.\nPour désactiver cette fonctionnalité : `>hmode`\n{}".format(
                                    member.name, str(member.discriminator), str(member.id), channel.guild.name, banned))
                        except Exception:
                            pass

                embed = discord.Embed(title="Détection d'un raid (heuristique)", description="Suppression de salons",
                                      color=0xff0000)
                embed.set_thumbnail(
                    url="https://images.vexels.com/media/users/3/136844/isolated/preview/11a79246e95fb4ad3b097b5e0dbf0328-skull-bones-circle-icon-by-vexels.png")
                embed.add_field(name="Serveur", value="{} ({})".format(channel.guild.name, str(channel.guild.id)),
                                inline=False)
                embed.add_field(name="Bot",
                                value="{}#{} ({})".format(member.name, str(member.discriminator), str(member.id)),
                                inline=False)
                embed.add_field(name="Résultat", value=banned, inline=False)

                lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
                supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])
                botNotif = [x for x in supguild.roles if x.name == "botNotif"][0]

                await lChan.send(content=botNotif.mention, embed=embed)
                self.bot.stats["blocked_raids"] += 1
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not self.settings.heuristic(channel.guild.id):
            return

        member = None
        try:
            async for a in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                member = a.user
        except Exception:
            return

        if not member.bot:
            return

        if member == self.bot.user:
            return

        if member.id in self.settings.ignored_bots():
            return

        result = self.check_last_created_channel(channel.guild.id, channel.name, channel.id)
        if isinstance(result, int):
            banned = None

            try:
                await channel.guild.ban(user=member, reason="Création de masse de salons.")
                banned = "✅ Le bot a été automatiquement banni."
            except Exception:
                pass

            if banned is not None:
                try:
                    await channel.delete()
                    ch2 = self.bot.get_channel(result)
                    await ch2.delete()
                except Exception:
                    pass
            else:
                banned = "❌ Le bot n'a pas put être banni : permissions insuffisantes."
        else:
            return

        try:
            if channel.guild.id in self.raid_warn:
                return
            self.raid_warn.append(channel.guild.id)

            for m in channel.guild.members:
                if m.guild_permissions.administrator and not m.bot:
                    try:
                        await m.send(
                            ":warning: Le bot __{}#{}__ ({}) a été détecté (détection heuristique) comme bot de raid sur le serveur **{}** où vous êtes administrateur pour la cause suivante : `Création de masse de salons`.\nPour désactiver cette fonctionnalité : `>hmode`\n{}".format(
                                member.name, str(member.discriminator), str(member.id), channel.guild.name, banned))
                    except Exception:
                        pass

            embed = discord.Embed(title="Détection d'un raid (heuristique)", description="Création de salons",
                                  color=0xff0000)
            embed.set_thumbnail(
                url="https://images.vexels.com/media/users/3/136844/isolated/preview/11a79246e95fb4ad3b097b5e0dbf0328-skull-bones-circle-icon-by-vexels.png")
            embed.add_field(name="Serveur", value="{} ({})".format(channel.guild.name, str(channel.guild.id)),
                            inline=False)
            embed.add_field(name="Bot",
                            value="{}#{} ({})".format(member.name, str(member.discriminator), str(member.id)),
                            inline=False)
            embed.add_field(name="Résultat", value=banned, inline=False)

            lChan = self.bot.get_channel(self.bot.config["supportGuild"]["logsChannel"])
            supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])
            botNotif = [x for x in supguild.roles if x.name == "botNotif"][0]

            await lChan.send(content=botNotif.mention, embed=embed)
            self.bot.stats["blocked_raids"] += 1
        except Exception:
            pass


def setup(bot):
    bot.add_cog(Heuristic(bot))
