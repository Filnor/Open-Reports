import os
import sys
import traceback

import git

import chatexchange
import openreports.se_api as stackexchange_api
from chatexchange.chatexchange.client import Client
from chatexchange.chatexchange.events import MessagePosted, MessageEdited
from openreports.logger import main_logger
from openreports.open_reports import OpenReports
from openreports.locations import Locations
from openreports.utils import utils, Struct

#Import config file with custom error message
try:
    import config as config
except ModuleNotFoundError:
    raise Exception("The config module couldn't be imported. Have you renamed config.example.py to config.py?")

utils = utils()

def main():
    """
    Main thread of the bot
    """
    debug_mode = False

    #Get config for the mode (debug/prod)
    try:
        if sys.argv[1] == "--debug":
            print("Using debug config.")
            utils.config = Struct(**config.debug_config)
            debug_mode = True
        else:
            raise IndexError
    except IndexError:
        print("Using productive config. \nIf you intended to use the debug config, use the '--debug' command line option")
        utils.config = Struct(**config.prod_config)

    #Set version
    utils.config.botVersion = "v2.0 DEV"

    #Initialize SE API class instance
    utils.se_api = stackexchange_api.se_api(utils.config.stackExchangeApiKey)

    try:
        #Login and connection to chat
        print("Logging in and joining chat room...")
        utils.room_number = utils.config.room
        client = Client(utils.config.chatHost)
        client.login(utils.config.email, utils.config.password)
        utils.client = client
        room = client.get_room(utils.config.room)
        try:
            room.join()
        except ValueError as e:
            if str(e).startswith("invalid literal for int() with base 10: 'login?returnurl=http%3a%2f%2fchat.stackoverflow.com%2fchats%2fjoin%2ffavorite"):
                raise chatexchange.chatexchange.browser.LoginError("Too many recent logins. Please wait a bit and try again.")

        room.watch_socket(on_message)
        print(room.get_current_user_names())
        utils.room_owners = room.owners

        main_logger.info(f"Joined room '{room.name}' on {utils.config.chatHost}")

        if debug_mode:
            room.send_message(f"[ [OpenReports](https://git.io/fpszU) ] {utils.config.botVersion} started in debug mode on {utils.config.botOwner}/{utils.config.botMachine}.")
        else:
            room.send_message(f"[ [OpenReports](https://git.io/fpszU) ] {utils.config.botVersion} started on {utils.config.botOwner}/{utils.config.botMachine}.")


        while True:
            message = input()

            if message in ["restart", "reboot"]:
                os._exit(1)
            else:
                room.send_message(message)

    except KeyboardInterrupt:
        os._exit(0)
    except BaseException as e:
        print(e)
        os._exit(1)

def on_message(message, client):
    """
    Handling the event if a message was posted or edited
    """

    if not isinstance(message, MessagePosted) and not isinstance(message, MessageEdited):
        #We ignore events that aren't MessagePosted or MessageEdited events.
        return

    #Check that the message object is defined
    if message is None or message.content is None:
        try:
            if message.user.id is 6294609 or message.user.id is client.get_me().id: #Don't handle self-messages and messages by Queen (Causes bugs from the comment deletion)
                return
        except AttributeError:
            main_logger.warning("ChatExchange message object or content property is None.")
            main_logger.warning(message)
        return

    #Get message as full string and as single words
    words = message.content.split()

    #Check for non-alias-command calls
    if message.content.startswith("🚂") or message.content.startswith("🚆") or message.content.startswith("🚄"):
        utils.log_command("train")
        utils.post_message("[🚃](https://youtu.be/qmhe9bm8SoE)")
    elif message.content.lower().startswith("@bots alive"):
        utils.log_command("@bots alive")
        utils.post_message("[open] Yes.")

    #Check if alias is valid
    if not utils.alias_valid(words[0]):
        return

    #Check if command is not set
    if len(words) <= 1:
        message.reply_to("Huh?")
        return

    #Store command in it's own variable
    command = words[1]
    full_command = ' '.join(words[1:])
    utils.log_command(full_command)

    amount = None
    from_the_back = False

    try:
        #Here are the commands defined
        if command in ["poof"]:
            msg = client.get_message(message.parent_message_id)
            if msg is not None:
                if utils.is_privileged(message):
                    msg.delete()
                else:
                    message.reply_to("This command is restricted to moderators, room owners and maintainers.")
        elif command in ["amiprivileged", "privs"]:
            if utils.is_privileged(message):
                message.reply_to("You are privileged.")
            else:
                message.reply_to(f"You are not privileged. Ping {utils.config.botOwner} if that doesn't makes sense to you.")
        elif command in ["a", "alive"]:
            utils.post_message("[open] Yes.")
        elif command in ["v", "version"]:
            message.reply_to(f"[open] Current version is {utils.config.botVersion}")
        elif command in ["loc", "location"]:
            message.reply_to(f"[open] This instance is running on {utils.config.botOwner}/{utils.config.botMachine}")
        elif command in ["kill open", "stop open"]:
            main_logger.warning(f"Stop requested by {message.user.name}")

            if utils.is_privileged(message):
                try:
                    utils.post_message("Cya! \o")
                    utils.client.get_room(utils.room_number).leave()
                except BaseException:
                    pass
                raise os._exit(0)
            else:
                message.reply_to("This command is restricted to moderators, room owners and maintainers.")
        elif full_command in ["standby open"]:
            main_logger.warning(f"Leave requested by {message.user.name}")

            # Restrict function to (site) moderators, room owners and maintainers
            if utils.is_privileged(message):
                utils.post_message("Cya! \o")
                utils.client.get_room(utils.room_number).leave()
            else:
                message.reply_to("This command is restricted to moderators, room owners and maintainers.")
        elif full_command in ["reboot open"]:
            main_logger.warning(f"Reboot requested by {message.user.name}")

            if utils.is_privileged(message):
                try:
                    utils.post_message("Rebooting now...")
                    utils.client.get_room(utils.room_number).leave()
                except BaseException:
                    pass
                raise os._exit(1)
            else:
                message.reply_to("This command is restricted to moderators, room owners and maintainers.")
        elif full_command in ["commands open", "commands openreports", "help open", "help openreports"]:
            utils.post_message("    ### OpenReports commands ###\n" + \
                               "    o[pen]                   - Open all reports not on ignore list.\n" + \
                               "    <number>                 - Open up to `number` reports.\n" + \
                               "    <number> b[ack]          - Open up to `number` reports, fetch from the back of the list (newest reports first)\n" + \
                               "    ignore rest, ir         - Put all unhandled reports from you last query on your ignore list\n" + \
                               "    fetch amount, fa         - Display the number of unhandled reports.\n" + \
                               "    dil, delete ignorelist   - Delete your ignorelist.\n" + \
                               "    poof                     - Deletes the message replied to, if possible. Requires privileges.\n" + \
                               "    amiprivileged, privs     - Checks if you're allowed to run privileged commands, like restarting or stopping the bot.\n" + \
                               "    a[live]                  - Replies with a message if the bot is running.\n" + \
                               "    v[ersion]                - Returns current version.\n" + \
                               "    loc[ation]               - Returns current location where the bot is running.\n" + \
                               "    kill open, stop open     - Stops the bot. Requires privileges.\n" + \
                               "    standby open             - Tells the bot to go to standby mode. That means it leaves the chat room and a bot maintainer needs to issue a restart manually. Requires privileges.\n" + \
                               "    reboot open              - Restarts the bot. Requires privileges.\n" + \
                               "    commands, help           - This command. Lists all available commands.\n" + \
                               "    status                   - Returns how long the bot is running\n" + \
                               "    update                   - Updates the bot to the latest git commit and restarts it. Requires owner privileges.", log_message=False, length_check=False)
        elif command in ["help", "commands"]:
            message.reply_to("[open] Try `commands open`")
        elif command in ["commands"]:
            message.reply_to(f"[open] Try `commands open`")
        elif command in ["status"]:
            utils.post_message("    ### OpenReports status ###\n" + \
                              f"    uptime         {utils.get_uptime()}\n" + \
                              f"    location       {utils.config.botOwner}/{utils.config.botMachine}\n" + \
                              f"    version        {utils.config.botVersion}", log_message=False, length_check=False)
        elif full_command in ["update open"]:
            if utils.is_privileged(message, owners_only=True):
                try:
                    repo = git.Repo(".")
                    repo.git.reset("--hard", "origin/master")
                    g = git.cmd.Git(".")
                    g.pull()
                    main_logger.info("Update completed, restarting now.")
                    os._exit(1)
                except BaseException as e:
                    main_logger.error(f"Error while updating: {e}")
                    pass
                os._exit(1)
            else:
                message.reply_to("This command is restricted to bot owners.")
        elif full_command in ["dil", "delete ignorelist"]:
            try:
                os.remove(f"{message.user.id}{client.host}.ignorelist.db")
                message.reply_to("Your ignorelist is deleted.")
            except OSError:
                message.reply_to("You don't seem to have a ignorelist currently.")
        elif command.isdigit():
            mode = 'normal'
            amount = int(command)
            if len(words) > 3 and words[2] in ['b', 'back']:
                from_the_back = True
                #Class method call
        elif full_command.startswith(("o", "open", "ir", "ignore rest", "fa", "fetch amount")):
            location = Locations.Natty
            if 'sentinel' in words or 's' in words:
                location = Locations.Sentinel
            if 'guttenberg' in words or 'g' in words:
                if location is Locations.Natty:
                    location = Locations.Guttenberg

            reports = OpenReports(utils.client.get_me(), utils, 0, False, utils.client.host, location)

            if full_command.startswith(("o", "open")):
                pass
            elif full_command.startswith(("ir", "ignore rest")):
                pass
            elif full_command.startswith(("fa", "fetch amount")):
                message.reply_to(reports.fetch_amount())

    except BaseException as e:
        main_logger.error(f"CRITICAL ERROR: {e}")
        if message is not None:
            try:
                if message.îd is not None:
                    main_logger.error(f"Caused by message id {message.id}")
            except AttributeError:
                pass
            main_logger.error(traceback.format_exc())
        try:
            utils.post_message(f"Error on processing the last command ({e}); rebooting instance... (cc @{utils.config.botOwner})")
            os._exit(1)

        except AttributeError:
            os._exit(1)
            pass


if __name__ == '__main__':
    main()
