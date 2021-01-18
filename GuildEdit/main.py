import discord, sys, asyncio, json
from discord.ext import commands
from datetime import datetime


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


bot = commands.AutoShardedBot(command_prefix=commands.when_mentioned_or('ge>', '>'))
bot.remove_command('help')
bot.version = "v2.3"
bot.mmode = False
bot.rmode = False

print(bcolors.UNDERLINE + "GuildEdit {}".format(bot.version) + bcolors.ENDC)

with open("config.json", 'r') as f:
    bot.config = json.load(f)
print(bcolors.OKBLUE + "Config chargee" + bcolors.ENDC)

print(bcolors.HEADER + "Chargement des cogs :" + bcolors.ENDC)
cogs = ["error_manager", "database", "settings", "events", "antiraid", "heuristic", "staff", "guildmanage", "guildlist",
        "backup", "clone_configguild", "general", "afk"]
for cog in cogs:
    try:
        bot.load_extension("cogs.{}".format(cog))
        print(bcolors.OKBLUE + "    {} : OK".format(cog) + bcolors.ENDC)
    except Exception as e:
        print(bcolors.WARNING + "    /!\ {} : {}".format(cog, str(e)) + bcolors.ENDC)


def is_staff():
    def predicate(ctx):
        if str(ctx.author.id) in bot.config["Staff"]:
            return True
        raise commands.DisabledCommand()

    return commands.check(predicate)


def is_admin():
    def predicate(ctx):
        if str(ctx.author.id) in bot.config["Admin"]:
            return True
        raise commands.DisabledCommand()

    return commands.check(predicate)


def format_datetime(date: datetime, logs: bool = False):
    week = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"]
    day = week[int(date.strftime("%w"))]
    return date.strftime("[%d/%m/%Y, %Hh%M] : ") if logs else date.strftime("Le %d/%m/%Y ({}) à %Hh%M".format(day))


async def clear_vars():
    antiraid = bot.cogs["Antiraid"]
    heuristic = bot.cogs["Heuristic"]
    await bot.wait_until_ready()

    while 1:
        await asyncio.sleep(86400)

        antiraid.raid_warn.clear()
        antiraid.last_created_channel.clear()
        antiraid.last_created_role.clear()
        antiraid.last_bot_message.clear()

        heuristic.raid_warn.clear()
        heuristic.last_created_channel.clear()
        heuristic.last_deleted_channel.clear()
        heuristic.last_created_role.clear()
        heuristic.last_deleted_role.clear()
        heuristic.last_bot_message.clear()


async def update_status():
    if bot.rmode:
        await bot.change_presence(
            activity=discord.Game(name=">help & >infos | {} serveurs".format(str(len(bot.guilds))), type=1),
            status=discord.Status.idle)
    if bot.mmode:
        await bot.change_presence(activity=discord.Game(name="Mode maintenance, bot indisponible.", type=0),
                                  status=discord.Status.do_not_disturb)
    if not bot.rmode and not bot.mmode:
        new_message = ">help & >infos | {} serveurs".format(str(len(bot.guilds)))
        await bot.change_presence(activity=discord.Streaming(name=new_message, url="https://www.twitch.tv/lcram33"),
                                  status=discord.Status.online)


async def get_raidmode_channel():
    supguild = bot.get_guild(bot.config["supportGuild"]["ID"])
    rmchan = None
    for c in supguild.channels:
        if c.name == "raidmode-logs":
            rmchan = c
            break
    if rmchan is None:
        perms = {supguild.default_role: discord.PermissionOverwrite(read_messages=False)}
        rmchan = await supguild.create_text_channel(name="raidmode-logs", overwrites=perms)
    return rmchan


@bot.check
async def check_mmode(ctx):
    if bot.mmode and not str(ctx.author.id) in bot.config["Staff"]:
        raise commands.DisabledCommand()
    else:
        return True


@bot.check
async def check_rmode(ctx):
    if bot.rmode:
        gtext = "Unknown"
        if isinstance(ctx.message.channel, discord.DMChannel):
            gtext = "DM"
        else:
            gtext = "{} ({})".format(ctx.message.guild.name, str(ctx.message.guild.id))
        rmchan = await get_raidmode_channel()
        embed = discord.Embed(title="Commande", description=ctx.message.content, color=0xffff00)
        embed.add_field(name="Utilisateur",
                        value="{}#{} ({})".format(ctx.author.name, str(ctx.author.discriminator), str(ctx.author.id)),
                        inline=True)
        embed.add_field(name="Serveur", value=gtext, inline=True)
        embed.add_field(name="Date", value=format_datetime(datetime.now()), inline=False)
        await rmchan.send(embed=embed)
    return True


@bot.check
async def check_ban(ctx):
    supguild = bot.get_guild(bot.config["supportGuild"]["ID"])
    banned = None
    try:
        banned = await supguild.fetch_ban(ctx.author)
    except Exception:
        pass

    if banned is not None:
        raise commands.DisabledCommand()
    else:
        return True


@bot.event
async def on_ready():
    print(bcolors.HEADER + "Demarre en tant que {}#{}, {} ({} serveurs)".format(bot.user.name,
                                                                                str(bot.user.discriminator),
                                                                                str(bot.user.id),
                                                                                str(len(bot.guilds))) + bcolors.ENDC)
    new_message = ">help & >infos | {} serveurs".format(str(len(bot.guilds)))
    await bot.change_presence(activity=discord.Streaming(name=new_message, url="https://www.twitch.tv/lcram33"),
                              status=discord.Status.online)


@bot.command()
@commands.is_owner()
async def addcog(ctx, cog):
    try:
        bot.load_extension("cogs.{}".format(cog))
        global cogs
        cogs.append(cog)
    except Exception as e:
        await ctx.send("**:warning: Impossible d'ajouter l'extension : `{}`**".format(str(e)))
    else:
        await ctx.send("**:white_check_mark: Extension ajoutée !**")


@bot.command()
@commands.is_owner()
async def removecog(ctx, cog):
    try:
        bot.unload_extension("cogs.{}".format(cog))
        global cogs
        cogs.remove(cog)
    except Exception as e:
        await ctx.send("**:warning: Impossible de retirer l'extension : `{}`**".format(str(e)))
    else:
        await ctx.send("**:white_check_mark: Extension retirée !**")


@bot.command()
@commands.is_owner()
async def reloadcog(ctx, cog):
    try:
        try:
            bot.unload_extension("cogs.{}".format(cog))
        except Exception:
            pass
        bot.load_extension("cogs.{}".format(cog))
    except Exception as e:
        await ctx.send("**:warning: Impossible de recharger l'extension : `{}`**".format(str(e)))
    else:
        await ctx.send("**:white_check_mark: Extension rechargée !**")


@bot.command()
@commands.is_owner()
async def reloadcogs(ctx):
    global cogs
    not_reloaded = ""
    for cog in cogs:
        try:
            bot.reload_extension("cogs.{}".format(cog))
        except Exception:
            not_reloaded += cog + ", "

    if len(not_reloaded) > 0:
        not_reloaded = not_reloaded[:-2]
        await ctx.send("**:warning: Extensions suivantes non-rechargées : `{}`**".format(not_reloaded))
    else:
        await ctx.send("**:white_check_mark: Extensions rechargées !**")


@bot.command()
@is_staff()
async def updatestatus(ctx):
    await update_status()
    await ctx.message.add_reaction(emoji='✅')


@bot.command()
@is_admin()
async def reloadconfig(ctx):
    try:
        with open("config.json", 'r') as f:
            bot.config = json.load(f)
        await ctx.author.send(":white_check_mark: Config chargée")
        print(bcolors.WARNING + format_datetime(datetime.now(), True) + "{}#{} ({}) a recharge config.json".format(
            ctx.author.name, str(ctx.author.discriminator), str(ctx.author.id)) + bcolors.ENDC)
    except Exception as e:
        await ctx.author.send(":x: Config non-chargée : " + str(e))


@bot.command()
@is_staff()
async def rmode(ctx):
    if bot.mmode:
        bot.mmode = False

    if bot.rmode:
        bot.rmode = False
        supguild = bot.get_guild(bot.config["supportGuild"]["ID"])
        for c in supguild.channels:
            if c.name == "raidmode-logs":
                await c.delete()
        print(bcolors.WARNING + format_datetime(datetime.now(), True) + "{}#{} ({}) a desactive le mode raid".format(
            ctx.author.name, str(ctx.author.discriminator), str(ctx.author.id)) + bcolors.ENDC)
    else:
        bot.rmode = True
        await get_raidmode_channel()
        print(bcolors.WARNING + format_datetime(datetime.now(), True) + "{}#{} ({}) a active le mode raid".format(
            ctx.author.name, str(ctx.author.discriminator), str(ctx.author.id)) + bcolors.ENDC)

    await update_status()
    await ctx.message.add_reaction(emoji='✅')


@bot.command()
@is_staff()
async def mmode(ctx):
    if bot.rmode:
        bot.rmode = False

    if bot.mmode:
        bot.mmode = False
        print(bcolors.WARNING + format_datetime(datetime.now(),
                                                True) + "{}#{} ({}) a desactive le mode maintenance".format(
            ctx.author.name, str(ctx.author.discriminator), str(ctx.author.id)) + bcolors.ENDC)
    else:
        bot.mmode = True
        print(
            bcolors.WARNING + format_datetime(datetime.now(), True) + "{}#{} ({}) a active le mode maintenance".format(
                ctx.author.name, str(ctx.author.discriminator), str(ctx.author.id)) + bcolors.ENDC)
    await update_status()
    await ctx.message.add_reaction(emoji='✅')


@bot.command()
@is_admin()
async def stop(ctx):
    embedC = discord.Embed(title="🛑 Confirmation de l'arrêt", description="Stopper le bot ?", color=0xff0000)
    embedC.add_field(name="Annulation", value="Ne faîtes rien, la commande s'annulera dans 30s.", inline=False)
    confirm = await ctx.send(embed=embedC)
    await confirm.add_reaction(emoji='✅')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == '✅'

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send(":x: Délai d'atente dépassé, veuillez retaper la commande.")
        return

    print(bcolors.FAIL + format_datetime(datetime.now(), True) + "{}#{} ({}) a stoppe le bot".format(ctx.author.name,
                                                                                                     str(
                                                                                                         ctx.author.discriminator),
                                                                                                     str(
                                                                                                         ctx.author.id)) + bcolors.ENDC)

    embed = discord.Embed(title="🌙 Sauvegarde réussie, l'arrêt est enclenché.")
    await confirm.edit(embed=embed)
    try:
        await confirm.clear_reactions()
    except Exception:
        pass

    await bot.close()
    sys.exit("Bot down par commande.")


bot.loop.create_task(clear_vars())
bot.run(bot.config["Token"], bot=True, reconnect=True)
