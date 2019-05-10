#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Server Monitor Bot
# by Aliaksandr Zakharenka
#
# ///////////////////////////////// https://al3xable.me/ ////////////////////////////////////
# //                                                                                       //
# //          .__   ________                  ___.    .__                                  //
# //  _____   |  |  \_____  \ ___  ________   \_ |__  |  |    ____        _____    ____    //
# //  \__  \  |  |    _(__  < \  \/  /\__  \   | __ \ |  |  _/ __ \      /     \ _/ __ \   //
# //   / __ \_|  |__ /       \ >    <  / __ \_ | \_\ \|  |__\  ___/     |  Y Y  \\  ___/   //
# //  (____  /|____//______  //__/\_ \(____  / |___  /|____/ \___  > /\ |__|_|  / \___  >  //
# //       \/              \/       \/     \/      \/            \/  \/       \/      \/   //
# //                                                                                       //
# ///////////////////////////////////////////////////////////////////////////////////////////

import json
import logging
import time
import urllib.request
from threading import Thread, Event
from urllib.error import HTTPError, URLError

from telegram import TelegramError
from telegram.ext import Updater, CommandHandler

updater = None
config = None
logger = None


def servers_monitor(bot, run):
    while run.is_set():
        try:
            fail = False
            resp = '```\n'

            for host in config['hosts']:
                r, st = checkHost(host)
                fail = fail or not st
                if not st:
                    resp += r

            resp += '```'

            if fail:
                bot.sendMessage(chat_id=config['chat'], text=resp, parse_mode="Markdown")

            time.sleep(config['monitorSleep'])
        except TelegramError as e:
            logger.error('Monitor exception: {}'.format(e.message))
        except Exception as e:
            logger.error('Monitor exception: {}'.format(e.args))


def chat(bot, update):
    update.message.reply_text(update.message.chat.id)
    # bot.sendPhoto(chat_id=config['master'], photo=open(file, 'rb'))


def checkHost(host):
    resp = ''
    srvip = host[0]

    try:
        code = urllib.request.urlopen("http://" + srvip).getcode()
    except HTTPError as e:
        code = e.code
    except URLError as e:
        code = e.reason

    ok = (code in [200, 401, 402, 403, 404])

    if ok:
        status = "OK (" + str(code) + ")"
    else:
        status = "FAIL (" + str(code) + ")"

    resp += "%10s | %-15s | %s\n" % (host[1], host[0], status)

    return resp, ok


def status(bot, update):
    resp = '```\n'

    for host in config['hosts']:
        r, st = checkHost(host)
        resp += r

    resp += '```'

    update.message.reply_text(resp, parse_mode="Markdown")


def main():
    # INIT #
    global config, logger, updater

    config = json.loads(open('bot.json', 'r').read())
    logger = logging.getLogger(__name__)
    updater = Updater(config['token'])

    logging.basicConfig(format='[%(asctime)s] [%(levelname)s:%(name)s] %(message)s', level=logging.INFO,
                        filename=config['logFileName'])

    updater.dispatcher.add_handler(CommandHandler('chat', chat))
    updater.dispatcher.add_handler(CommandHandler('status', status))

    updater.start_polling(timeout=config['poolTimeout'])

    run = Event()
    run.set()

    th = Thread(target=servers_monitor, args=(updater.bot, run))
    th.start()

    updater.idle()

    # Stopping thread
    run.clear()
    th.join()


if __name__ == '__main__':
    main()
