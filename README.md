A simple bot for more convenient review of different bot reports. Currently supports Natty and Guttenberg. The main features are convenient opening several reports at the same time, maintaining a personal ignorelist and automatically skipping deleted posts if you are <10k.

The bot currently understands the following commands:

 - 'open' or 'o': Open all pending reports not in the ignore list
 - '`number` [b[ack]]': Open up to `number` reports, fetch from the back of the list if b or back is present
 - 'ignore rest' or 'ir': Put all reports that where in your last report in your personal ignore list. Those reports will not be shown to you in the future.
 - 'dil' or 'delete ignorelist': Delete your ignorelist
 - 'fetch amount' or 'fa': Tells you, how many unhandled reports there are
 - 'reboot': Restarts the bot

If you want more filters or sorting facilities, please raise an issue on Github or ping me.

