import traceback
import sys
import discord
from discord.ext import commands


class Error_manager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bypassed_commands = ["changepsw", "hsguild", "likesys", "banraidbots", "hmode", "lockperms"]

    def missing_perms_list(self, missing_perms: list):
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

        strmissing = ""
        for p in missing_perms:
            strmissing += translate_dict[p] + ", "
        return strmissing[:-2]

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isinstance(error, (commands.CommandNotFound, commands.DisabledCommand, commands.NotOwner)):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(title=":warning: **Cette commande ne peut pas être effectuée en mp.**",
                                  color=0xfac801)
            return await ctx.send(embed=embed)
        elif isinstance(error, commands.CommandOnCooldown):
            if str(ctx.author.id) in self.bot.config["Staff"]:
                ctx.command.reset_cooldown(ctx)
                await self.bot.process_commands(ctx.message)
            else:
                await ctx.message.add_reaction("⏰")
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title=":x: **Il manque le paramètre `{}`.**".format(error.param.name), color=0xff0000)
            return await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(title=":x: **Les paramètres n'ont pas été entrés correctement.**", color=0xff0000)
            return await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            if str(ctx.author.id) in self.bot.config["Staff"] and ctx.command.name in self.bypassed_commands:
                await ctx.reinvoke()
                return

            embed = discord.Embed(
                title=":x: **Vous devez avoir les permissions suivantes pour effectuer cette commande : `{}`.**".format(
                    self.missing_perms_list(error.missing_perms)), color=0xff0000)
            return await ctx.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(title=":x: **Le bot a besoin des permissions suivantes : `{}`.**".format(
                self.missing_perms_list(error.missing_perms)), color=0xff0000)
            return await ctx.send(embed=embed)
        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            embed = discord.Embed(title=":x: Une erreur inconnue s'est produite.", color=0xff0000)
            return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Error_manager(bot))
