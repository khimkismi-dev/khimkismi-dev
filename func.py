# !/usr/bin/python3
# -*- coding: utf-8 -*

# import email.message
# import xmljson
# import json
# from json import dumps
# from xmljson import badgerfish as bf
# import random
# from random import randint
# import smtplib as smtp
# from email.header import Header
# from email.mime.text import MIMEText
# from functools import wraps
# from lxml.etree import fromstring, tostring
# import urllib.parse
# import requests
# from requests.auth import HTTPBasicAuth
import datetime
import time
import logging
import re
import ssl
import sys
import telegram
from telegram.ext import Filters, CallbackQueryHandler
from telegram.ext import Updater, CommandHandler, MessageHandler

import os
from os import path

import config

# file with classes imports
from local_helpers import Helpers
from local_user import User
from local_bg import BG
from local_db import DB, DBPsql


# bg_config = copy.deepcopy(config.bg_config)
db_config = config.db_config
TOKEN = config.TOKEN
updater = Updater(token=TOKEN)  # , request_kwargs={'proxy_url': 'socks5://51.15.83.215:1080'}, workers=0) #proxy
dispatcher = updater.dispatcher


# обработчик /start
def start(bot, update):
    # указываем отправленную пользователем команду для записи в лог
    command = "/start"
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    Helpers.logger(user_id, command)

    user = User('users', user_id, chat_id, command)
    # user.set_last_msg()
    user.users_property('last_msg', 'insert')
    text, reply_markup = user.menu()

    bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')


# ф-ия-обработчик сообщений от пользователя
def echo(bot, update):
    # print(update.message)
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    msg = Helpers.emoji_remove(update.message.text)

    Helpers.logger(user_id, msg)

    user = User('users', user_id, chat_id, msg)
    user.prev_msg = user.users_property('last_msg')
    user.users_property('last_msg', 'insert')
    # print(user.user_state())

    # print(user.msg)
    if user.msg == 'Тест кабеля' and user_id in user.user_crm_info:
        text = '<code>Пожалуйста, подождите. \nВыполняется тестирование кабеля...</code>'
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

    text, reply_markup = user.menu()

    bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    # print(user.prev_msg)
    crm_number = user.users_property('crm_number')
    if user.crm_number and ((user.msg not in config.exclude_crm_action and user.msg in config.menu_items)
                            or user.prev_msg in config.ch_host_list.keys()) and user.user_crm_info[user_id][
        'clean_data'] != '':
        # print(user.user_crm_info[user_id]['clean_data']['description'])
        abon_phone = Helpers.get_abon_phone(user.user_crm_info[user_id]['clean_data'])
        Helpers.crm_main_actions(bot, chat_id, crm_number, abon_phone)

    if user.msg == 'Активация' and user_id in user.user_crm_info:
        Helpers.yes_no_menu(bot, chat_id, '<code>Подтвердите выбор</code>')


# ф-ия, обработчик нажатий inline-кнопок
def callback_button(bot, update):
    # print(update.callback_query)
    # данные, отправленные пользователем по нажатию inline-кнопки
    call = update.callback_query
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    # print(call.data)

    Helpers.logger(user_id, call.data)

    user = User('users', user_id, chat_id, call.data)
    user.prev_msg = user.users_property('last_msg')
    user.users_property('last_msg', 'insert')

    # text, reply_markup = user.menu()
    # text = 'Выполните требуемое действие'
    # bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    text, reply_markup = user.menu()

    if user.prev_msg == 'Чек-поинты' and user.msg not in config.menu_items:
        crm_number = user.users_property('crm_number')
        user_name = user.users_property('name')
        res = BG.crm_set_checkpoint(crm_number, user.msg, user_name, user_id)
        # print(res)
        if res['code'] == 0:
            text = '<code>Чек-поинт [' + user.msg + '] по задаче ' + str(crm_number) + ' проставлен!</code>'
        else:
            text = 'Ошибка: ' + res['message']
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'infinity_call_(\d)*', user.msg):
        text = 'Вы точно хотите позвонить абоненту?'
        Helpers.yes_no_menu(bot, chat_id, text)

    elif re.search(r'infinity_call_(\d)*', user.prev_msg) and user.msg == 'Да':
        abon_number = re.search(r'\d+', user.prev_msg)[0]
        text = user.infinity_call(abon_number)
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

    elif re.search(r'to_history_crm(\d)*', user.msg):
        # получаем номер задачи из текста inline callback
        crm_number = re.search(r'\d+', user.msg).group(0)
        text = 'Вы точно добавить эту информацию в историю задачи <b>%s</b>?' % crm_number
        Helpers.yes_no_menu(bot, chat_id, text)

    elif re.search(r'to_history_crm(\d)*', user.prev_msg) and user.msg == 'Да':
        crm_number = re.search(r'\d+', user.prev_msg).group(0)

        text = '<code>Подождите. Добавляю информацию...</code>'
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
        res_cable_test = BG.get_cable_test(crm_number, user_id)
        if res_cable_test['code'] == 0:
            to_history = res_cable_test['data']['cable']['log']
            res = BG.crm_add_comment(crm_number, to_history, user.users_property('name'), user_id)
            if res['code'] == 0:
                text = '<code>Комментарий успешно добавлен к задаче %s!</code>' % crm_number
                user.user_crm_info[user_id] = BG.crm_info(crm_number, user_id)
                user.user_crm_info[user_id]['crm_number'] = crm_number
            else:
                text = 'Ошибка добавления комментария к задаче %s!\n<code>Код ошибки=%s. \nОбратитесь к ' \
                       'Администратору</code>' % (crm_number, str(res['code']))
        else:
            text = '<code>Ошибка тестирования кабеля! Информация не добавлена в историю задачи %s!</code>' % crm_number
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

    elif re.search(r'crm_(\d)*_task_delegate', user.prev_msg) and user.msg not in ['Да', 'Нет']:
        group_list = BG.get_group_list(user_id)
        if user.msg in group_list:
            text = 'Вы точно хотите перевести задачу ' + \
                   '<b>' + user.users_property('crm_number') + '</b> ' \
                                                               'на группу ' + '<b>' + user.msg + '</b> '
        else:
            text = 'Вы точно хотите назначить ответственным ' + '<b>' + user.msg + '</b>' \
                                                                                   ' по задаче ' + '<b>' + user.users_property(
                'crm_number') + '</b> '
        Helpers.yes_no_menu(bot, chat_id, text)

    # elif re.search(r'crm_(\d)*_report_photo_(\d)', user.msg):
    #     text = 'Вы точно хотите добавить фото к задаче ' + '<b>' + user.users_property('crm_number') + '</b> '
    #     Helpers.yes_no_menu(bot, chat_id, text)

    elif re.search(r'crm_(\d)*_report_photo_(\d)', user.msg):  # and user.msg == 'Да'
        crm_type = user.msg.split('_')[5]
        photo_name = str(config.report_points[crm_type]['send_photo'][int(user.msg.split('_')[4])])
        text = "Отправьте боту фото:\n\"" + photo_name + "\""
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'crm_(\d)*_task_done', user.msg):
        text = 'Вы точно хотите поставить статус "выполнена" для задачи ' + \
               '<b>' + user.users_property('crm_number') + '</b>'
        Helpers.yes_no_menu(bot, chat_id, text)

    elif user.prev_msg == 'Изменить статус' and user.msg:
        if re.search(r'crm_(\d)*_task_(open|done|close)', user.msg):
            status = 'не определен!'
            if re.search(r'open', user.msg):
                status = 'открыта'
            elif re.search(r'done', user.msg):
                status = 'выполнена'
            elif re.search(r'close', user.msg):
                status = 'закрыта'
            text = 'Вы точно хотите поставить статус "' + status + '" для задачи ' + \
                   '<b>' + user.users_property('crm_number') + '</b>'
            Helpers.yes_no_menu(bot, chat_id, text)

    elif user.prev_msg == 'CRM' and user.msg in config.ch_host_list.keys():
        # bg_config['server'] = config.bg_config['server'].replace(config.default_host, config.ch_host_list[user.msg])
        # print(bg_config)
        user.bg_servername = config.ch_host_list[user.msg]
        user.users_property('bg_servername', 'insert', user.bg_servername)
        text = 'Введите номер задачи:'
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif user.msg == 'Нет':
        text = '<code>Вы отменили предыдущее действие!</code>'
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'send_photo|send_document', user.prev_msg) and user.msg == 'Да':
        msg_type = user.prev_msg
        db = DB(db_config)
        query = """SELECT teleg_file_id from reports WHERE user_id=%d""" % user.user_id
        file_id = db.sql_execute(query)[0]

        query = """SELECT filesize from reports WHERE user_id=%d""" % user.user_id
        filesize = db.sql_execute(query)[0]

        file = bot.getFile(file_id)

        # if user.msg == 'send_photo' and user.prev_msg == 'Да':
        if filesize > 20971520:
            text = '<code>Размер файла более 20Мб. \nМожно загружать файлы не более 20Мб.</code>'
            bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
        else:
            (dirName, file_name) = os.path.split(file.file_path)
            file_name = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S")) + '_' + file_name
            servername = user.users_property('bg_servername')
            crm_number = user.users_property('crm_number')
            folder_path = config.bot_folder + 'reports/' + config.report_provider_folders[servername] + '/' + \
                          str(crm_number) + '/'
            if not path.exists(folder_path):
                try:
                    os.mkdir(folder_path)
                except OSError:
                    Helpers.logger(user.user_id, "Creation of the directory %s failed" % folder_path)
            downloaded_file = file.download(folder_path + file_name)

            url = config.bot_url + config.report_provider_folders[servername] + '/' + str(crm_number) + '/' + file_name
            query = """SELECT description FROM reports WHERE user_id=%d""" % user.user_id
            description = db.sql_execute(query)[0]

            if crm_number:
                res = BG.post_url_to_task(crm_number, user_id, url, description)
                if res['code'] == 0:
                    set_report_tag(bot, user, msg_type)
                else:
                    text = res['message']
                    bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            else:
                text = '<code>Не выбрана задача для работы! Пожалуйста, сначала выберите пункт "CRM".</code>'
                bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')


    else:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')


def set_report_tag(bot, user, report_type):
    text = '<code>ДОБАВЛЕНО</code>'
    bot.send_message(chat_id=user.chat_id, text=text, parse_mode='HTML')


def photo(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    msg_type = 'send_photo'
    msg = msg_type  # + ' ' + str(update.message.photo[len(update.message.photo) - 1].file_id)

    # print(update.message.photo[len(update.message.photo) - 1])

    user = User('users', user_id, chat_id, msg)
    user.prev_msg = user.users_property('last_msg')
    user.users_property('last_msg', 'insert')

    Helpers.logger(user_id, msg)

    if re.search(r'crm_(\d)*_report_photo_(\d)', user.prev_msg):  # and user.msg == 'Да'
        # user.user_crm_info[user.user_id][]
        crm_type = user.prev_msg.split('_')[5]
        photo_name = str(config.report_points[crm_type]['send_photo'][int(user.prev_msg.split('_')[4])])
        db = DB(db_config)
        f_id = update.message.photo[len(update.message.photo) - 1].file_id
        f_size = update.message.photo[len(update.message.photo) - 1].file_size
        query = """REPLACE INTO reports (user_id, teleg_file_id, filesize, url, description) \
        VALUES (%d, '%s', %d, '%s', '%s')""" % (user_id, f_id, f_size, None, photo_name)
        db.sql_execute(query)

        text = 'Вы хотите добавить данное фото в фотоотчет по задаче ' + '<b>' + user.users_property(
            'crm_number') + '</b>?'
        Helpers.yes_no_menu(bot, chat_id, text)


def document(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    msg_type = 'send_document'
    msg = msg_type  # + ' ' + str(update.message.document.file_id)

    # print(update.message)

    user = User('users', user_id, chat_id, msg)
    user.prev_msg = user.users_property('last_msg')
    user.users_property('last_msg', 'insert')

    Helpers.logger(user_id, msg)

    text = 'Вы хотите добавить данный документ в фотоотчет по задаче ' + \
           '<b>' + user.users_property('crm_number') + '</b>?'
    Helpers.yes_no_menu(bot, chat_id, text)
