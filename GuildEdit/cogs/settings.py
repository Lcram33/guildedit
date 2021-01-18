from discord.ext import commands
import discord


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database = self.bot.cogs["Database"]

    def locked_guilds(self):
        request = self.database.select_request("guildedit", "locked_guilds", "guild_id", (), ())
        if type(request) == list or type(request) == tuple:
            return [int(x["bot_id"]) for x in request]
        if type(request) == dict:
            return [int(request["bot_id"])]
        return list()

    def ignored_bots(self):
        request = self.database.select_request("guildedit", "ignored_bots", "bot_id", (), ())
        if type(request) == list or type(request) == tuple:
            return [int(x["bot_id"]) for x in request]
        if type(request) == dict:
            return [int(request["bot_id"])]
        return list()

    def add_entry(self, id: int, identified: bool = False, password: str = None, lisys: bool = False,
                  banraidbots: bool = True,
                  heuristic: bool = False, perms_lock: bool = True):
        if password is None:
            password = ""

        return self.database.insert_request("guildedit", "guilds_settings",
                                            ("guild_id", "identified", "password", "likesys", "banraidbots",
                                             "heuristic", "perms_lock"), (id, identified, password,
                                                                          lisys, banraidbots, heuristic, perms_lock))

    def remove_entry(self, id: int):
        return self.database.delete_request("guildedit", "guilds_settings", ("guild_id",), (id,))

    def get_entry(self, id: int):
        request = self.database.select_request("guildedit", "guilds_settings", '*', ("guild_id",), (id,))

        result = None
        if type(request) != str and request is not None:
            result = {
                "ID": id,
                "identified": bool(request["identified"]),
                "password": request["password"],
                "likesys": bool(request["likesys"]),
                "banraidbots": bool(request["banraidbots"]),
                "heuristic": bool(request["heuristic"]),
                "perms_lock": bool(request["perms_lock"])
            }
        else:
            result = request

        return result

    def edit_identified(self, id: int):
        entry = self.get_entry(id)
        if entry is None:
            self.add_entry(id, identified=True)
            return ":white_check_mark: Votre serveur est désormais visible !"
        else:
            if type(entry) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(entry)

            request = self.database.update_request("guildedit", "guilds_settings", ("identified",),
                                                   (not entry["identified"],), ("guild_id",), (id,))
            if type(request) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(request)

            return ":white_check_mark: Votre serveur n'est plus visible !" if entry[
                "identified"] else ":white_check_mark: Votre serveur est de nouveau visible !"

    def edit_password(self, id: int, password: str):
        return self.database.update_request("guildedit", "guilds_settings", ("password",), (password,), ("guild_id",),
                                            (id,))

    def like_system_enabled(self, id: int):
        entry = self.get_entry(id)
        if type(entry) == str or entry is None:
            return False
        else:
            return entry["likesys"]

    def edit_likesys(self, id: int):
        entry = self.get_entry(id)
        if entry is None:
            self.add_entry(id)
            return ":white_check_mark: Système de like activé !"
        else:
            if type(entry) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(entry)

            request = self.database.update_request("guildedit", "guilds_settings", ("likesys",),
                                                   (not entry["likesys"],), ("guild_id",), (id,))
            if type(request) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(request)

            return ":white_check_mark: Système de like désactivé !" if entry[
                "likesys"] else ":white_check_mark: Système de like activé !"

    def ban_raidbots(self, id: int):
        entry = self.get_entry(id)
        if type(entry) == str or entry is None:
            return True
        else:
            return entry["banraidbots"]

    def edit_ban_raidbots(self, id: int):
        entry = self.get_entry(id)
        if entry is None:
            self.add_entry(id, banraidbots=False)
            return ":x: **Les bots détectés comme bots de raid ne seront plus bannis !**"
        else:
            if type(entry) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(entry)

            if entry["heuristic"]:
                return ":warning: **Le mode heuristique est activé ! Veuillez d'abord le désactiver avec `>hmode`.**"

            request = self.database.update_request("guildedit", "guilds_settings", ("banraidbots",),
                                                   (not entry["banraidbots"],), ("guild_id",), (id,))
            if type(request) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(request)

            return ":x: **Les bots détectés comme bots de raid ne seront plus bannis.**" if entry[
                "banraidbots"] else ":white_check_mark: Les bots détectés comme bots de raid seront désormais bannis."

    def heuristic(self, id: int):
        entry = self.get_entry(id)
        if type(entry) == str or entry is None:
            return False
        else:
            return entry["heuristic"]

    def edit_heuristic(self, id: int):
        entry = self.get_entry(id)
        if entry is None:
            self.add_entry(id, heuristic=True, banraidbots=False)
            return ":white_check_mark: **Mode heuristique activé !**"
        else:
            if type(entry) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(entry)

            request = self.database.update_request("guildedit", "guilds_settings", ("heuristic", "banraidbots"),
                                                   (not entry["heuristic"], not entry["banraidbots"]), ("guild_id",), (id,))

            if type(request) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(request)

            return ":white_check_mark: **Mode heuristique désactivé !**" if entry[
                "heuristic"] else ":white_check_mark: **Mode heuristique activé !**"

    def perms_lock(self, id: int):
        entry = self.get_entry(id)
        if type(entry) == str or entry is None:
            return True
        else:
            return entry["perms_lock"]

    def edit_perms_lock(self, id: int):
        entry = self.get_entry(id)
        if entry is None:
            self.add_entry(id, perms_lock=False)
            return ":warning: **Les administrateurs ont désormais accès aux commandes sensibles !**"
        else:
            if type(entry) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(entry)

            request = self.database.update_request("guildedit", "guilds_settings", ("perms_lock",),
                                                   (not entry["perms_lock"],), ("guild_id",), (id,))
            if type(request) == str:
                return ":x: **L'erreur suivante s'est produite :** `{}`".format(request)

            return ":warning: **Les administrateurs ont désormais accès aux commandes sensibles !**" if entry[
                "perms_lock"] else ":white_check_mark: Seul le propriétaire du serveur a désormais accès aux commandes sensibles !"

    async def get_like_channel(self, guild: discord.Guild):
        for c in guild.text_channels:
            if c.name == "fil-des-likes":
                return c
        try:
            perms = {guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=False)}
            channel = await guild.create_text_channel(name="fil-des-likes", overwrites=perms)
            await channel.send(
                ":white_check_mark: Les messages avec plus de 15 réactions :heart: s'afficheront ici ! :smile:\nMerci de ne pas changer le nom de ce salon, sinon un autre sera créé avec ce nom.")
            return channel
        except Exception as e:
            return ":x: Impossible de créer le salon : `{}`".format(str(e))


def setup(bot):
    bot.add_cog(Settings(bot))
