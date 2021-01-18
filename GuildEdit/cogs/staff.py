import ast
import json
import random
from datetime import datetime
import discord
import psutil
from discord.ext import commands


class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = bot.cogs["Settings"]
        self.database = bot.cogs["Database"]

        self.embed = discord.Embed()

    def is_staff():
        def predicate(ctx):
            if str(ctx.author.id) in ctx.cog.bot.config["Staff"]:
                return True
            raise commands.DisabledCommand()

        return commands.check(predicate)

    def is_admin():
        def predicate(ctx):
            if str(ctx.author.id) in ctx.cog.bot.config["Admin"]:
                return True
            raise commands.DisabledCommand()

        return commands.check(predicate)

    def convert_size(self, size: int):
        unit = "o"
        if size > 1024 ** 3:
            unit = "Go"
            size = round(size / 1024 ** 3, 1)
        elif size > 1024 ** 2:
            unit = "Mo"
            size = round(size / 1024 ** 2, 1)
        elif size > 1024:
            unit = "Ko"
            size = round(size / 1024, 1)
        return str(size) + unit

    def hide_sensitive_content(self, text: str):
        sensitive_data = [self.bot.config["Token"], self.bot.config["Database"]["host"],
                          self.bot.config["Database"]["user"], self.bot.config["Database"]["password"]]
        for data in sensitive_data:
            random_int = random.randint(1, 10)
            text = text.replace(data, "█" * (len(data) + random_int))
        return text

    def log_console(self, s_input: str, member: discord.Member):
        print("\033[93m" + datetime.now().strftime("[%d/%m/%Y, %Hh%M] : ") + "{}#{} ({}) ".format(member.name, str(
            member.discriminator), str(member.id)) + s_input + "\033[0m")

    @commands.command()
    @commands.is_owner()
    async def savejson(self, ctx, *, fName):
        if ctx.author.id == 303191513372950529:
            saved_guild = {
                "name": ctx.guild.name,
                "region": str(ctx.guild.region),
                "afk_timeout": ctx.guild.afk_timeout,
                "afk_channel": ctx.guild.afk_channel.name if ctx.guild.afk_channel else None,
                "system_channel": ctx.guild.system_channel.name if ctx.guild.system_channel else None,
                "icon": str(ctx.guild.icon_url),
                "mfa_level": ctx.guild.mfa_level,
                "verification_level": ["none", "low", "medium", "high", "extreme"].index(
                    str(ctx.guild.verification_level)),
                "default_notifications": "only_mentions" if ctx.guild.default_notifications == discord.NotificationLevel.only_mentions else "all_messages",
                "explicit_content_filter": ["disabled", "no_role", "all_members"].index(
                    str(ctx.guild.explicit_content_filter)),
                "roles": [],
                "categories": [],
                "text_channels": [],
                "voice_channels": [],
                "emojis": []
            }

            for role in ctx.guild.roles:
                if role.managed:
                    continue

                role_position = role.position - 1 if role.position - 1 > 0 else role.position
                role_dict = {
                    "name": role.name,
                    "permissions": list(role.permissions),
                    "colour": role.colour.to_rgb(),
                    "hoist": role.hoist,
                    "position": role_position,
                    "mentionable": role.mentionable
                }

                saved_guild["roles"].append(role_dict)

            for category in ctx.guild.categories:
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

            for channel in ctx.guild.text_channels:
                channel_dict = {
                    "name": channel.name,
                    "topic": channel.topic,
                    "position": channel.position,
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

            for channel in ctx.guild.voice_channels:
                channel_dict = {
                    "name": channel.name,
                    "position": channel.position,
                    "user_limit": channel.user_limit,
                    "bitrate": channel.bitrate,
                    "overwrites": [],
                    "category": channel.category.name if channel.category else None
                }
                try:
                    channel_dict["category"] = channel.category.name
                except Exception:
                    pass
                for overwrite in channel.overwrites:
                    overwrite_dict = {
                        "name": overwrite.name,
                        "permissions": list(channel.overwrites_for(overwrite)),
                        "type": "member" if type(overwrite) == discord.Member else "role"
                    }

                    channel_dict["overwrites"].append(overwrite_dict)

                saved_guild["voice_channels"].append(channel_dict)

            for emoji in ctx.guild.emojis:
                emoji_dict = {
                    "name": emoji.name,
                    "url": str(emoji.url)
                }

                saved_guild["emojis"].append(emoji_dict)

            with open(fName + ".json", "w+") as f:
                json.dump(saved_guild, f)

            await ctx.author.send(":white_check_mark: Le modèle a bien été créé !")

    def insert_returns(self, body):
        # insert return stmt if the last expression is a expression statement
        if isinstance(body[-1], ast.Expr):
            body[-1] = ast.Return(body[-1].value)
            ast.fix_missing_locations(body[-1])

        # for if statements, we insert returns into the body and the orelse
        if isinstance(body[-1], ast.If):
            self.insert_returns(body[-1].body)
            self.insert_returns(body[-1].orelse)

        # for with blocks, again we insert returns into the body
        if isinstance(body[-1], ast.With):
            self.insert_returns(body[-1].body)
    
    def prepare_eval(self, data: str):
        data = data.replace("```py", "```")

        return data

    def format_code(self, code: str):
        lines = code.split("\n")
        new_code = "```"

        for i in range(len(lines)):
            new_code += "{}  {} \n".format(str(i+1), lines[i])
        
        return new_code + "```"


    @commands.command()
    @commands.is_owner()
    async def lockguild(self, ctx, *, id):
        found_guild = None
        try:
            found_guild = self.bot.get_guild(int(id))
        except Exception:
            pass

        if found_guild is None:
            await ctx.send(":x: Serveur introuvable.")
            return

        request = self.database.select_request("guildedit", "locked_guilds", '*', ("guild_id",), (id,))
        if type(request) == str:
            await ctx.send(":x: **L'erreur suivante s'est produite :** `{}`".format(request))
        else:
            if request is None:
                request = self.database.insert_request("guildedit", "locked_guilds", ("guild_id",), (id,))
                if type(request) == str:
                    await ctx.send(":x: **L'erreur suivante s'est produite :** `{}`".format(request))
                else:
                    await ctx.send(":warning: Ce serveur est désormais privé.")
            else:
                request = self.database.delete_request("guildedit", "locked_guilds", ("guild_id",), (id,))
                if type(request) == str:
                    await ctx.send(":x: **L'erreur suivante s'est produite :** `{}`".format(request))
                else:
                    await ctx.send(":white_check_mark: Ce serveur n'est plus privé !")

    # commande eval récupérée d'ici :
    # https://gist.github.com/nitros12/2c3c265813121492655bc95aa54da6b9
    # Il ne s'agit pas de mon travail et tout le crédit revient à son auteur.

    @commands.command()
    @commands.is_owner()
    async def eval(self, ctx):
        """Evaluates input.
        Input is interpreted as newline seperated statements.
        If the last statement is an expression, that is the return value.
        Usable globals:
          - `bot`: the bot instance
          - `discord`: the discord module
          - `commands`: the discord.ext.commands module
          - `ctx`: the invokation context
          - `__import__`: the builtin `__import__` function
        Such that `>eval 1 + 1` gives `2` as the result.
        The following invokation will cause the bot to send the text '9'
        to the channel of invokation and return '3' as the result of evaluating
        >eval ```
        a = 1 + 2
        b = a * 2
        await ctx.send(a + b)
        a
        ```
        """

        result = ""
        try:
            fn_name = "_eval_expr"
            cmd = self.prepare_eval(ctx.message.content.replace(">eval ", ""))
            cmd = cmd.strip("` ")

            # add a layer of indentation
            cmd = "\n".join("    {}".format(i) for i in cmd.splitlines())

            # wrap in async def body
            body = "async def {}():\n{}".format(fn_name, cmd)
            old_body = body

            parsed = ast.parse(body)
            body = parsed.body[0].body

            self.insert_returns(body)

            env = {
                'bot': ctx.bot,
                'discord': discord,
                'commands': commands,
                'ctx': ctx,
                '__import__': __import__
            }

            exec(compile(parsed, filename="<ast>", mode="exec"), env)
            result = (await eval("{}()".format(fn_name), env))
            result = ":white_check_mark: Résultat :\n```" + str(result) + "```"
        except Exception as e:
            result = ":warning: L'erreur suivante s'est produite :\n```" + str(e) + "``` \n :arrow_right: Code : {}".format(self.format_code(old_body))

        await ctx.send(self.hide_sensitive_content(result))

    @commands.command()
    @commands.is_owner()
    async def rank(self, ctx, user_id, level):
        levels = ["Staff", "Admin", "Smod"]
        if level not in levels:
            await ctx.send(":x: **Veuillez entrer un niveau existant !**")
            return

        user_data = None
        try:
            user = await self.bot.fetch_user(str(user_id))
            user_data = "{}#{}".format(user.name, str(user.discriminator))
        except Exception:
            await ctx.send(":x: **Veuillez entrer un id valide !**")
            return

        if user_id in self.bot.config[level]:
            del self.bot.config[level][user_id]
            await ctx.send(":white_check_mark: ** *{}* n'est désormais plus *{}*.**".format(user_data, level))
        else:
            self.bot.config[level][user_id] = user_data
            await ctx.send(":white_check_mark: ** *{}* est désormais *{}* !**".format(user_data, level))

        with open('config.json', 'w') as f:
            json.dump(self.bot.config, f)

    @commands.command()
    @is_staff()
    async def ignbot(self, ctx, *, id):
        found_user = None
        try:
            found_user = await self.bot.fetch_user(int(id))
        except Exception:
            pass

        if found_user is None:
            await ctx.send(":x: Utilisateur introuvable.")
            return

        if not found_user.bot:
            await ctx.send(":x: Cet utilisateur n'est pas un bot.")
            return

        request = self.database.select_request("guildedit", "ignored_bots", '*', ("bot_id",), (id,))
        if type(request) == str:
            await ctx.send(":x: **L'erreur suivante s'est produite :** `{}`".format(request))
        else:
            revoked = None
            if request is None:
                request = self.database.insert_request("guildedit", "ignored_bots", ("bot_id",), (id,))
                if type(request) == str:
                    await ctx.send(":x: **L'erreur suivante s'est produite :** `{}`".format(request))
                else:
                    await ctx.send(":negative_squared_cross_mark: Ce bot est désormais exclu de la détection !")
                revoked = False
            else:
                request = self.database.delete_request("guildedit", "ignored_bots", ("bot_id",), (id,))
                if type(request) == str:
                    await ctx.send(":x: **L'erreur suivante s'est produite :** `{}`".format(request))
                else:
                    await ctx.send(":white_check_mark: Ce bot n'est plus exclu de la détection !")
                revoked = True

        self.log_console("a ignore {}".format(str(id) + " (revocation)" if revoked else str(id)), ctx.author)

    @commands.command()
    @is_staff()
    async def getinvite(self, ctx, *, guild_id):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        try:
            guild_id = int(guild_id)
        except Exception:
            await ctx.send(":x: Veuillez entrer un id valide.")
            return

        if guild_id in self.settings.locked_guilds():
            await ctx.author.send(":x: **Accès refusé.**")
            return

        try:
            target = self.bot.get_guild(guild_id)
            target_invites = await target.invites()

            self.log_console("a utilise >getinvite sur {}".format(str(guild_id)), ctx.author)
            if len(target_invites) > 0:
                infinite_invite = None
                infinite_invites = [i for i in target_invites if not i.temporary and i.max_age == 0]
                if len(infinite_invites) > 0:
                    infinite_invite = infinite_invites[0]

                if infinite_invite is not None:
                    await ctx.author.send("Infinie\n" + str(infinite_invite))
                    return

                invite = target_invites[0]
                for i in target_invites:
                    if i.max_age > invite.max_age and not i.temporary:
                        invite = i
                await ctx.author.send("Temporaire\n" + str(invite))
            else:
                invite = await target.text_channels[0].create_invite(destination=target.text_channels[0], xkcd=True,
                                                                     max_uses=5, max_age=900)
                await ctx.author.send("Générée : expire dans 15min, 5 utilisations\n" + str(invite))
        except Exception as e:
            await ctx.author.send(":x: **Impossible d'obtenir une invitation :** " + str(e))

    @commands.command()
    @is_admin()
    @commands.guild_only()
    async def say(self, ctx):
        content = str(ctx.message.content.replace(">say ", ""))
        await ctx.send(content.replace("`everyone`", "@everyone"))
        await ctx.message.delete()

    @commands.command()
    @is_staff()
    async def sban(self, ctx, ids: commands.Greedy[int], *, reason="aucune raison fournie"):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        if len(ids) == 0:
            await ctx.send(":x: Veuillez entrer au moins un id !")
            return

        supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])
        banned = ""
        notfound = ""
        notbanned = ""
        for id in ids:
            userToBan = None
            try:
                userToBan = await self.bot.fetch_user(id)
            except Exception:
                notfound += "{}, ".format(str(id))
                continue

            try:
                await supguild.ban(user=userToBan, reason=">banid par {}#{} : {}".format(ctx.author.name, str(
                    ctx.author.discriminator), reason))
                banned += "{}#{}, ".format(userToBan.name, str(userToBan.discriminator))
            except Exception as e:
                notbanned += "{}#{}, ".format(userToBan.name, str(userToBan.discriminator))
                pass

        embed = discord.Embed(title="Rapport de bannissement de **{}**".format(supguild.name),
                              description="✅ Utilisateurs bannis : {}".format(
                                  banned[:-2] if len(banned) > 0 else "aucun"), color=0xff0000)
        embed.set_thumbnail(url="https://discordemoji.com/assets/emoji/BlurpleBanHammer.png")
        if len(notbanned) > 0:
            embed.add_field(name="❌ Utilisateurs non-bannis :", value=notbanned[:-2], inline=False)
        if len(notfound) > 0:
            embed.add_field(name="❓ Utilisateurs introuvables :", value=notfound[:-2], inline=False)
        await ctx.author.send(embed=embed)

    @commands.command()
    @is_staff()
    async def leaveguild(self, ctx, *, guild_id):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        try:
            target = self.bot.get_guild(int(guild_id))
            await target.leave()
            await ctx.author.send(":white_check_mark: Le serveur **{}** a été quitté !".format(target.name))
            self.log_console("a utilise >leaveguild sur {}".format(guild_id), ctx.author)
        except Exception as e:
            await ctx.author.send(":x: Impossible de quitter le serveur : {}".format(str(e)))
            pass

    @commands.command()
    @is_staff()
    async def searchguild(self, ctx, *, guildName):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        mcount = 0
        result = ""
        pack = ""
        for i in self.bot.guilds:
            if i.name.lower().find(guildName.lower()) > -1:
                result += str(i.id) + "\n"
                ginfo = "{} ({})\n".format(i.name, str(i.id))
                if len(pack) + len(ginfo) > 2000:
                    await ctx.author.send(pack)
                    pack = ginfo
                else:
                    pack += ginfo
                mcount += 1

        if mcount > 0:
            pack += "\n{} résultat(s).".format(str(mcount))
        else:
            await ctx.author.send(":x: Aucun résultat de recherche.")

        if len(pack) > 0:
            await ctx.author.send(pack)

        self.log_console("a utilise >searchguild {}".format(guildName), ctx.author)

    @commands.command()
    @is_staff()
    async def searchuser(self, ctx, *, memberName):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        rcount = 0
        result = ""
        pack = ""
        for i in self.bot.guilds:
            for m in i.members:
                if m.name.lower().find(memberName.lower()) > -1:
                    if result.find(str(m.id)) == -1:
                        result += str(m.id) + "\n"
                        minfo = "{}#{} ({})\n".format(m.name, str(m.discriminator), str(m.id))
                        if len(pack) + len(minfo) > 2000:
                            await ctx.author.send(pack)
                            pack = minfo
                        else:
                            pack += minfo
                        rcount += 1

        if rcount > 0:
            pack += "\n{} résultat(s).".format(str(rcount))
        else:
            await ctx.author.send(":x: Aucun résultat de recherche.")

        if len(pack) > 0:
            await ctx.author.send(pack)

        self.log_console("a utilise >searchuser {}".format(memberName), ctx.author)

    @commands.command()
    @is_staff()
    async def commonguilds(self, ctx, *, id):
        try:
            id = int(id)
        except Exception:
            await ctx.author.send(":x: Veuillez entrer un id valide.")
            return

        if id == self.bot.user.id:
            await ctx.author.send(":x: Trop de serveurs à afficher.")
            return

        gcount = 0
        pack = ""

        for g in self.bot.guilds:
            if g.get_member(id) is not None:
                ginfo = "**{}** ({})\n".format(g.name, str(g.id))
                if len(pack) + len(ginfo) > 2000:
                    await ctx.author.send(pack)
                    pack = ginfo
                else:
                    pack += ginfo
                gcount += 1

        if gcount > 0:
            pack += "\n{} serveur(s).".format(str(gcount))
        else:
            await ctx.author.send(":x: Utilisateur non trouvé.")

        if len(pack) > 0:
            await ctx.author.send(pack)

        self.log_console("a utilise >commonguilds {}".format(str(id)), ctx.author)

    @commands.command()
    @is_staff()
    async def checkguilds(self, ctx):
        supguild = self.bot.get_guild(self.bot.config["supportGuild"]["ID"])

        try:
            await ctx.message.delete()
        except Exception:
            pass

        pack = ""
        for g in self.bot.guilds:
            m_list = ""
            for m in g.members:
                if m.guild_permissions.administrator or m == g.owner and not m.bot:
                    try:
                        banned = await supguild.fetch_ban(m)
                        m_list += "   {}#{} ({}), {}\n".format(m.name, str(m.discriminator), str(m.id),
                                                               "owner" if m == g.owner else "admin")
                    except Exception:
                        pass

            if len(m_list) == 0:
                continue

            g_text = "**{}** ({})\n{}\n".format(g.name, str(g.id), m_list)
            if len(g_text) + len(pack) > 1950:
                await ctx.author.send(pack)
                pack = g_text
            else:
                pack += g_text

        if len(pack) > 0:
            await ctx.author.send(pack)

        self.log_console("a utilise >checkguilds", ctx.author)

    @commands.command()
    @is_staff()
    async def helpstaff(self, ctx):
        embed3 = discord.Embed(title="Commandes", description="""
__Catégorie : Outils du bot 1/2__

**>leaveguild (id)** : Fait partir le bot du serveur d'id donné.
**>getinvite (id)** : Retourne ou crée une invitation pour le serveur dont l'id est donné.

**>searchguild (mot clé)** : Recherche le mot clé dans tous les noms des serveurs sur lequel le bot est présent, et retourne le nom et l'id du ou des serveurs trouvés.
**>searchuser (mot clé)** : Recherche le mot clé dans tous les noms des utilisateurs sur tous les serveurs sur lequel le bot est présent, et retourne le nom et l'id du ou des membres trouvés.
**>commonguilds (id)** : Retourne les serveurs en commun du bot avec l'utilisateur d'id donné.
**>checkguilds** : Donne les serveurs où les admins/l'owner est banni.

**>sban (id1, id2, ..., idn, raison)** : Banni les membres sur le serveur de support grâce à leur id.

**>mmode** : Active ou désactive le mode maintenance (seul le staff peut utiliser les commandes du bot).
**>rmode** : Active ou désactive le mode raid (logging de toutes les commandes).
**>updatestatus** : Restaure le status du bot.

**>guildpsw (id)** : Donne le mot de passe d'entrée d'un serveur. Ne fonctionne qu'en mp.

**>ignbot (id)** : Exclut (ou révoque l'exclusion) un bot de la détection des bots de raid.
        """, color=0x36393f)
        await ctx.author.send(embed=embed3)

        embed4 = discord.Embed(title="Commandes", description="""
__Catégorie : Outils du bot 2/2__

**>setembed (code json)** : Crée un embed avec le code json donné (voir modèle ci-dessous).

__Modèle :__ (les "fields" sont optionnels)

{
    "title": "Titre",
    "description": "Description",
    "color": "couleur en hex, ex : 0xff0000",
    "url": "url de l'icône souhaitée",
    "field1": {
        "name": "Nom champ",
        "value": "Description champ"
    },

    "field2": {
        "name": "Nom champ",
        "value": "Description champ"
    },

    "field3": {
        "name": "Nom champ",
        "value": "Description champ"
    },
}
        """, color=0x36393f)
        await ctx.author.send(embed=embed4)

    @commands.command()
    @is_admin()
    async def helpadmin(self, ctx):
        embed3 = discord.Embed(title="Commandes", description="""
__Catégorie : Gestion du bot__

**>serverstatus** : Informations sur le VPS.

**>say (message)** : Pour mentionner everyone : `everyone` (évite d'avoir deux mentions).

**>broadcastnews** : Envoie l'embed défini avec `>setembed` dans tous les salons portant le nom `ge-news`.

**>reloadconfig** : Recharge le fichier `config.json`.

**>stop** : /!\ TERMINE LE PROCESSUS DU BOT /!\
        """, color=0x36393f)
        await ctx.author.send(embed=embed3)

    @commands.command()
    @is_admin()
    async def serverstatus(self, ctx):
        total, used, free, usage_percent = psutil.disk_usage("//")

        embed = discord.Embed(title="Statut du VPS", description="""
**CPU :** {}%
**RAM :** {}/{} ({}%)
**Stockage :** {}/{} ({}%)
        """.format(str(psutil.cpu_percent()), self.convert_size(psutil.virtual_memory().used),
                   self.convert_size(psutil.virtual_memory().available), str(psutil.virtual_memory().percent),
                   self.convert_size(used), self.convert_size(total), str(usage_percent)), color=0x36393f)
        embed.set_thumbnail(
            url="http://icons.iconarchive.com/icons/tuziibanez/profesional-red/256/network-drive-connected-icon.png")
        await ctx.send(embed=embed)

    @commands.command()
    @is_staff()
    async def guildpsw(self, ctx, *, id):
        if not isinstance(ctx.message.channel, discord.DMChannel):
            await ctx.message.delete()
            await ctx.author.send(":x: Cette commande ne s'effectue qu'en DM (info privée !)")
            return

        password = ""
        try:
            entry = self.settings.get_entry(int(id))
            if entry is None:
                password = ":x: Pas de données"
            elif entry["password"] == "":
                password = ":white_check_mark: Aucun mot de passe"
            else:
                password = entry["password"]
        except Exception:
            password = ":x: id invalide."

        await ctx.author.send(password)

        self.log_console("a utilise >guildpsw {}".format(id), ctx.author)

    @commands.command()
    @is_staff()
    async def setembed(self, ctx):
        embed_dict = None
        try:
            embed_dict = json.loads(ctx.message.content.replace(">setembed ", ""))
        except Exception as e:
            await ctx.send(":x: **Impossible de décoder le texte json :** `{}`".format(str(e)))
            return

        try:
            self.embed = discord.Embed(title=embed_dict["title"], description=embed_dict["description"],
                                       color=int(embed_dict["color"], 16))
            self.embed.set_author(name="{}#{}".format(ctx.author.name, str(ctx.author.discriminator)),
                                  url=self.bot.config["links"]["support"], icon_url=ctx.author.avatar_url_as(
                    format='gif' if ctx.author.is_avatar_animated() else 'jpg'))
            self.embed.set_thumbnail(url=embed_dict["url"])

            if "field1" in embed_dict:
                self.embed.add_field(name=embed_dict["field1"]["name"], value=embed_dict["field1"]["value"],
                                     inline=False)

            if "field2" in embed_dict:
                self.embed.add_field(name=embed_dict["field2"]["name"], value=embed_dict["field2"]["value"],
                                     inline=False)

            if "field3" in embed_dict:
                self.embed.add_field(name=embed_dict["field3"]["name"], value=embed_dict["field3"]["value"],
                                     inline=False)

            self.embed.set_footer(text="Actualité GuildEdit")

            await ctx.send(content="Résultat :", embed=self.embed)
        except Exception as e:
            await ctx.send(":x: **Impossible de complier l'embed :** `{}`".format(str(e)))

    @commands.command()
    @is_admin()
    async def broadcastnews(self, ctx):
        await ctx.send(embed=self.embed)

        embedC = discord.Embed(title="🛑 Confirmation", description="Confirmer l'envoie dans tous les channels news ?",
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

        news_channels = []
        for guild in self.bot.guilds:
            channels = [x for x in guild.text_channels if x.name == self.bot.config["newsChannel"]]
            if len(channels) > 0:
                news_channels.append(channels[0])

        for news_channel in news_channels:
            await news_channel.send(embed=self.embed)

        await confirm.clear_reactions()
        embedF = discord.Embed(title="✅ Voilà !",
                               description="Actualité envoyée sur **{}** serveurs.".format(str(len(news_channels))),
                               color=0x008040)
        await confirm.edit(embed=embedF)

        self.log_console("a utilise >broadcastnews", ctx.author)


def setup(bot):
    bot.add_cog(Staff(bot))
