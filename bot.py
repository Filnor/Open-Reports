#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import getpass
import logging
import logging.handlers
import os
import OpenReports
import time
import traceback
from subprocess import call
from threading import Thread

import chatexchange.client
import chatexchange.events

rooms = [
    {
        'hostID' : 'stackoverflow.com',
        'roomID' : '111347',
    },
    {
        'hostID' : 'stackexchange.com',
        'roomID' : '54445',
    }
]

commands = {'o':'normal', 'open':'normal', 'ir':'ignore_rest', 'ignore rest':'ignore_rest',
        'fa':'fetch_amount', 'fetch amount':'fetch_amount'}

helpmessage = \
        '    o, open:                    Open all reports not on ignore list\n' + \
        '    `number` [b[back]]:         Open up to `number` reports, fetch from the back of the list if b or back is present\n' + \
        '    ir, ignore rest:            Put all unhandled reports from you last querry on your ignore list\n' + \
        '    fa, fetch amount:           Display the number of unhandled reports\n' + \
        '    dil, delete ignorelist:     Delete your ignorelist\n' + \
        '    reboot open:                Restart the open reports bot'

def _parseMessage(msg):
    temp = msg.split()
    return ' '.join(v for v in temp if not v[0] == '@').lower()

def onMessage(message, client):
    if isinstance(message, chatexchange.events.MessagePosted) and \
            str(message.room.id) not in ['111347', '54445']:
        return
    if isinstance(message, chatexchange.events.MessagePosted) and \
            message.content in ['🚂', '🚆', '🚄']:
        message.room.send_message('[🚃](https://github.com/SOBotics/Open-Reports)')
        return

    amount = None
    fromTheBack = False
    try:
        if message.target_user_id != client.get_me().id:
            return
        userID = message.user.id
        command = _parseMessage(message.content)
        words = command.split()
        if not words:
            return
        if command == 'reboot open':
            os._exit(1)
        if command == 'update open':
            call(['git', 'pull'])
            os._exit(1)
        if command in ['a', 'alive']:
            message.room.send_message('[open] Yes.')
            return
        if command in ['dil', 'delete ignorelist']:
            os.remove(str(userID) + client.host + '.ignorelist.db')
            message.room.send_message('Ignorelist deleted.')
            return
        if command in ['commands open', 'commands openreports']:
            message.room.send_message(helpmessage)
            return
        if command == 'commands':
            message.room.send_message('[open] Try `commands open`')
            return
        if words[0].isdigit():
            mode = 'normal'
            amount = int(words[0])
            if len(words) > 1 and words[1] in ['b', 'back']:
                fromTheBack = True
        else:
            mode = commands[words[0]]
        where = None
        if 'sentinel' in command:
            where  = 'sentinel'
        if 'guttenberg' in command:
            if where is not None:
                return
            where = 'gutty'
    except:
        return
    
    try:
        message.room.send_message(OpenReports.OpenReports(mode, message.user, 
            client, amount=amount, back=fromTheBack, where=where))
    except Exception as e:
        message.room.send_message('Error occurred: ' + str(e) + ' (cc @Baum)')
        traceback.print_exc()

def WatchRoom(mail, password, room):
    client = chatexchange.client.Client(room['hostID'])
    client.login(email, password)

    room = client.get_room(room['roomID'])
    room.join()
    room.send_message('[open] Hi o/')

    watcher = room.watch_socket(onMessage)

    return client, room, watcher

if 'ChatExchangeU' in os.environ:
    email = os.environ['ChatExchangeU']
else:
    email = input("Email: ")
if 'ChatExchangeP' in os.environ:
    password = os.environ['ChatExchangeP']
else:
    password = input("Password: ")


while True:
    watchers = [WatchRoom(email, password, r) for r in rooms]
    for w in watchers:
        w[2].thread.join()


