#!/usr/bin/python3
# -*- coding: utf-8 -*-
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, CallbackQueryHandler
#from functools import wraps
import func
import config


TOKEN = func.TOKEN
BOT_SERVER_IP = config.BOT_SERVER_IP
PORT = config.PORT
updater = func.updater
dispatcher = updater.dispatcher

# обработчик /start
start_handler = CommandHandler('start', func.start)
dispatcher.add_handler(start_handler)

# обработчик сообщений от пользователя
echo_handler = MessageHandler(Filters.text, func.echo)
dispatcher.add_handler(echo_handler)

# обработчик нажатий inline-кнопок
callback_handler = CallbackQueryHandler(func.callback_button)
dispatcher.add_handler(callback_handler)

# обработчик полученных от пользователя фото
photo_handler = MessageHandler(Filters.photo, func.photo)
dispatcher.add_handler(photo_handler)

# обработчик полученных от пользователя документов
document_handler = MessageHandler(Filters.document, func.document)
dispatcher.add_handler(document_handler)


#updater.dispatcher.add_error_handler(error)

updater.start_webhook(listen='0.0.0.0',
                      port=PORT,  # возможны след. порты: 80, 8443, 88, 443 (88 и 443 уже используются)
                      url_path=TOKEN,
                      key=config.bot_folder + 'YOURPRIVATE.key',
                      cert=config.bot_folder + 'YOURPUBLIC.pem',
                      webhook_url="https://%s:%d/%s" % (BOT_SERVER_IP, PORT, TOKEN))

# updater.start_polling()

updater.idle()