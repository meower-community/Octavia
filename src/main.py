from dotenv import load_dotenv
import pymongo
import update_check as updater
from MeowerBot import Bot
import requests
import os
import time

# Version tracker
version = "1.0.0"

# Load environment keys
if not load_dotenv():
    print("Failed to load .env keys, exiting.")
    exit()

# Create instance of bot
octavia = Bot()

# Keep track of processing requests
tickets = dict()

# Prepare DB connection
print(f"Connecting to database...")
dbclient = pymongo.MongoClient(os.getenv("SERVER_DB", "mongodb://localhost:27017"))
meowerdb = None
octaviadb = None

# Check DB connection status
try:
    dbclient.server_info()
    print("Connected to database!")
    meowerdb = dbclient.meowerserver
    octaviadb = dbclient.octavia
except pymongo.errors.ServerSelectionTimeoutError as err:
    print(f"Failed to connect to database: \"{err}\"!")
    exit()


# DB methods
def getUserLevel(username):
    return meowerdb.usersv0.find_one({"_id": username})["lvl"]


def modifyUserLevel(username, newlevel):
    return (meowerdb.usersv0.update_one({"_id": username}, {"$set": {"lvl": newlevel}})).matched_count > 0


def isUserValid(username):
    if meowerdb.usersv0.find_one({"_id": username}):
        return True
    return False


# Restart script
def restart():
    print("Shutting down websocket")
    octavia.wss.stop()

    script = os.getenv("RESET_SCRIPT")
    print(f"Running reset script: {script}")
    os.system(script)

    print(f"octavia {version} going away now...")
    exit()


# Shutdown script
def shutdown():
    print("Shutting down websocket")
    octavia.wss.stop()

    print(f"octavia {version} going away now...")
    exit()


''' def registerNewTicket(ctx, username, method):
    # Log the ticket
    ticket_result = octaviadb.tickets.insert_one({
        "_id": str(time.time()),
        "request": method,
        "timestamp": time.time(),
        "origin": ctx.user.username,
        "recipient": username,
        "result": None
    })
    
    ticketID = ticket_result.inserted_id
    
    print(f"Creating ticket: {ticketID}")
    
    tickets[ticketID] = {
        "origin": ctx.user.username,
        "recipient": username
    }
    
    return ticketID


def resolveTicket(ticketID, status):
    if not ticketID in tickets:
        print(f"Invalid ticket ID \"{ticketID}\", exiting resolveTicket method")
    
    print(f"Ticket {ticketID} resolving with status {status}")
    
    octavia.send_msg(
        f"@{tickets[ticketID]['origin']} I have processed the your request with result {status}!")
    
    # Log the ticket result
    ticket_result = octaviadb.tickets.update_one({"_id": ticketID}, {"$set": {"result": status}})
    
    del tickets[ticketID]
'''

# Commands
'''@octavia.command(args=0, aname="meow")
def quack(ctx):
    ctx.send_msg("Meow!")'''


@octavia.command(args=0, aname="help")
def help(ctx):
    ctx.send_msg(
        " - help: this message.\n - meow: another fun message!\n - about: Learn a little about me!\n - setlevel (username) (user level)\n - getlevel (username)\n - kick (username)\n - ban (username)\n - ipban (username)\n - pardon (username)\n - ippardon (username)\n - update\n - shutdown\n - reboot\n - announce \"(message)\"\n - warn (username) \"(message)\"")


@octavia.command(args=0, aname="about")
def about(ctx):
    ctx.send_msg(
        f"octavia v{version} \nCreated by @MikeDEV, built using @ShowierData9978's MeowerBot.py library! \n\nI'm a little orange cat with a squeaky toy hammer, and I'm here to keep Meower a safer place! Better watch out, only Meower Mods, Admins, and Sysadmins can use me!\n\nYou can find my source code here: https://github.com/MeowerBots/octavia")


@octavia.command(args=0, aname="update")
def updateCheck(ctx):
    if getUserLevel(ctx.user.username) == 4:
        # Check for updates, but better(ish)
        versionHistory = requests.get("https://raw.githubusercontent.com/MeowerBots/octavia/main/versionInfo.json").json()
        if version not in versionHistory["latest"] or version in versionHistory["old"]:
            ctx.send_msg(f"Looks like I'm out-of-date! Latest version(s) are {versionHistory['latest']} while I'm on {version}. Downloading updates...")
            time.sleep(1)
            updater.update(f"{os.getcwd()}/main.py", "https://raw.githubusercontent.com/MeowerBots/octavia/main/src/main.py")
            ctx.send_msg("Rebooting to apply updates...")
            time.sleep(1)
            restart()
        else:
            ctx.send_msg(f"Looks like I'm up-to-date! Running v{version} right now.")
    else:
        ctx.send_msg(f"You don't have permissions to do that so I ignored your request, {ctx.user.username}. The command \"update\" requires level 4 access, you only have level {getUserLevel(ctx.user.username)}.")


@octavia.command(args=0, aname="reboot")
def rebootScript(ctx):
    if getUserLevel(ctx.user.username) == 4:
        ctx.send_msg("Oke! I'm rebooting now...")
        restart()
    else:
        ctx.send_msg(f"You don't have permissions to do that so I ignored your request, {ctx.user.username}. The command \"reboot\" requires level 4 access, you only have level {getUserLevel(ctx.user.username)}.")


@octavia.command(args=0, aname="shutdown")
def shutdownScript(ctx):
    if ctx.user.username == "MikeDEV":
        ctx.send_msg("Goodbye! I'm shutting down now...")
        shutdown()
    else:
        ctx.send_msg(f"Sorry, the \"shutdown\" command is only allowed for MikeDEV.")


# Listener management
def listenerEventManager(post, bot):
    # Validate keys
    for key in ["cmd", "val", "listener"]:
        if key not in post:
            return

    # Handle listeners
    if post["cmd"] == "statuscode":
        if post["listener"] in tickets:
            resolveTicket(post["listener"], post["val"])
        elif post["listener"] == "__meowerbot__login" and post["val"] == "I:100 | OK":
            bot.send_msg(f"Octavia v{version} is alive! Use @Octavia help for info!")


# Register event listener for tickets and startup message
octavia.callback(listenerEventManager, cbid="__raw__")

print(f"Octavia {version} starting up now...")

# Run bot
try:
    octavia.run(
        username=os.getenv("BOT_USERNAME"),
        password=os.getenv("BOT_PASSWORD"),
        server=os.getenv("SERVER_CL")
    )
except KeyboardInterrupt:
    print("Detecting interrupt, going away now...")
    shutdown()
