# !/usr/bin/python3
# -*- coding: utf-8 -*

import datetime
import time
import logging
import re
import ssl
import sys
import telegram
from telegram import Update
from telegram.ext import Filters, CallbackQueryHandler, CallbackContext
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
updater = Updater(token=TOKEN, use_context=True)
# , request_kwargs={'proxy_url': 'socks5://51.15.83.215:1080'}, workers=0) #proxy
dispatcher = updater.dispatcher


# обработчик /start
def start(update: Update, context: CallbackContext):
    job = context.job
    # указываем отправленную пользователем команду для записи в лог
    command = "/start"
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    Helpers.logger(user_id, command)

    user = User('users', user_id, chat_id, command)
    # refresh field report
    # user.users_property('report', 'insert', ' ')
    # user.set_last_msg()
    user.users_property('last_msg', 'insert')
    text, reply_markup = user.menu()

    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')


# ф-ия-обработчик сообщений от пользователя
def echo(update: Update, context: CallbackContext):
    # print(update.message)
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    msg = Helpers.emoji_remove(update.message.text)

    Helpers.logger(user_id, msg)

    user = User('users', user_id, chat_id, msg)
    # refresh field report
    # user.users_property('report', 'insert', ' ')
    user.prev_msg = user.users_property('last_msg')
    user.users_property('last_msg', 'insert')
    # print(user.user_state())

    # print(user.msg)
    if user.msg == 'Тест кабеля' and user_id in user.user_crm_info:
        text = '<code>Пожалуйста, подождите. \nВыполняется тестирование кабеля...</code>'
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

    text, reply_markup = user.menu()

    if not user.users_property('report') or user.users_property('report').find("unplug_") == -1:
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    # print(user.prev_msg)
    crm_number = user.users_property('crm_number')
    if user.crm_number and ((user.msg not in config.exclude_crm_action and user.msg in config.menu_items)
                            or user.prev_msg in config.ch_host_list.keys()) \
            and user.user_crm_info[user_id]['clean_data'] != '':
        # print(user.user_crm_info[user_id]['clean_data']['description'])
        abon_phones = Helpers.get_abon_phones(user.user_crm_info[user_id]['clean_data'])
        Helpers.crm_main_actions(context.bot, chat_id, crm_number, abon_phones)

        if 'type' in user.user_crm_info[user_id]['clean_data'] \
                and user.user_crm_info[user_id]['clean_data']['type'] in config.custom_processing_type\
                and user.user_crm_info[user_id]['clean_data']['subject'] == 'test'\
                and (Helpers.is_int(user.msg) and user.prev_msg in config.ch_host_list.keys()):
            func_name = config.custom_processing_type[user.user_crm_info[user_id]['clean_data']['type']]
            getattr(Helpers, func_name)(context.bot, chat_id, reply_markup, crm_number)

    if user.msg == 'Активация' and user_id in user.user_crm_info:
        Helpers.yes_no_menu(context.bot, chat_id, '<code>Подтвердите выбор</code>')

    elif re.search(r'add_work_(\d)*_(\d)', user.prev_msg) and Helpers.is_int(user.msg):
        work_id = user.prev_msg.split('_')[2]
        crm_num = user.prev_msg.split('_')[3]
        count = user.msg
        res = BG.add_work(crm_num, work_id, count, [str(user.users_property('bg_id'))], user.users_property('bg_id'),
                          user_id)
        if res['code'] == 0:
            text = '<code>Работа по задаче %s успешно добавлена!</code>' % crm_num
        else:
            err_msg = ''
            if 'message' in res:
                err_msg = ':\n' + res['message']
            text = 'Ошибка проставления работы по задаче %s <code>%s</code>!\n<code>Код ошибки=%s. \nОбратитесь к ' \
                   'Администратору</code>' % (crm_num, err_msg, str(res['code']))
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'add_work_(\d)*_(\d)', user.prev_msg) and not Helpers.is_int(user.msg):
        text = '<code>Некорректный ввод кол-ва работ!</code>'
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'func_processing_add_comment', user.prev_msg):
        crm_number = user.users_property('crm_number')
        to_history = user.msg
        res = BG.crm_add_comment(crm_number, to_history, user.users_property('name'), user_id)
        if res['code'] == 0:
            if user_id not in user.user_crm_info.keys():
                user.user_crm_info.update({'crm_number': crm_number})
            text = 'Комментарий добавлен!\n'
            data = {'username': user.users_property('name'), 'responsible': config.tech_department_supervisor, 'user': user}
            text = text + Helpers.func_unplug_processing_finish(crm_number, data)
            user.user_crm_info[user_id] = BG.crm_info(crm_number, user_id)
        else:
            text = '<b>Ошбика добавления комментария!</b> Попробуйте повторить предыдущее действие'
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'save_badge_number#(\d+)', user.prev_msg):
        contract_id = user.user_crm_info[user_id]['clean_data']['contract']['id']
        badge_number = user.msg
        text = 'Вы точно хотите сохранить номер <b>%s</b> в качестве номера бирки для договора <b>%s</b>?' % \
               (badge_number, contract_id)
        Helpers.yes_no_menu(context.bot, chat_id, text)
        # context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')


# ф-ия, обработчик нажатий inline-кнопок
def callback_button(update: Update, context: CallbackContext):
    # print(update.callback_query)
    # данные, отправленные пользователем по нажатию inline-кнопки
    call = update.callback_query
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    Helpers.logger(user_id, call.data)

    user = User('users', user_id, chat_id, call.data)
    # refresh field report
    # user.users_property('report', 'insert', ' ')
    user.prev_msg = user.users_property('last_msg')

    user.users_property('last_msg', 'insert')

    # text, reply_markup = user.menu()
    # text = 'Выполните требуемое действие'
    # context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

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
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'add_work_(\d)*_(\d)', user.msg):
        text = '<code>Для проставления выбранной работы по задаче</code> <b>%s</b> <code>введите кол-во работ (' \
               'число).</code>' % (user.msg.split('_')[3])
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'multi_phones_(\d)*', user.msg):
        phones_list = user.msg.replace('multi_phones_', '').split(';')
        # print(phones_list)
        txt = '<code>У абонента более 1 номера!</code> \nВыберите один из номеров, по которому хотите совершить вызов:'
        call_data = {}
        num = 0
        for phone in phones_list:
            num = num + 1
            data_key = '📞 Номер_' + str(num)  # button text
            call_data[data_key] = 'infinity_call_' + phone
        # print(call_data)
        text, reply_markup = Helpers.gen_inline_kb(call_data, txt)
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'infinity_call_(\d)*', user.msg):
        text = 'Вы точно хотите позвонить абоненту?'
        Helpers.yes_no_menu(context.bot, chat_id, text)

    elif re.search(r'infinity_call_(\d)*', user.prev_msg) and user.msg == 'Да':
        abon_number = re.search(r'\d+', user.prev_msg)[0]
        text = user.infinity_call(abon_number)
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

    elif re.search(r'to_history_crm(\d)*', user.msg):
        # получаем номер задачи из текста inline callback
        crm_number = re.search(r'\d+', user.msg).group(0)
        text = 'Вы точно добавить эту информацию в историю задачи <b>%s</b>?' % crm_number
        Helpers.yes_no_menu(context.bot, chat_id, text)

    elif re.search(r'to_history_crm(\d)*', user.prev_msg) and user.msg == 'Да':
        crm_number = re.search(r'\d+', user.prev_msg).group(0)

        text = '<code>Подождите. Добавляю информацию...</code>'
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
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
        context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

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
        Helpers.yes_no_menu(context.bot, chat_id, text)

    # elif re.search(r'crm_(\d)*_report_photo_(\d)', user.msg):
    #     text = 'Вы точно хотите добавить фото к задаче ' + '<b>' + user.users_property('crm_number') + '</b> '
    #     Helpers.yes_no_menu(context.bot, chat_id, text)

    elif re.search(r'crm_(\d)*_report_photo_(\d)', user.msg):  # and user.msg == 'Да'
        crm_type = user.msg.split('_')[5]
        photo_name = str(config.report_points[crm_type]['send_photo'][int(user.msg.split('_')[4])])
        text = "Отправьте боту фото:\n\"" + photo_name + "\""
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'crm_(\d)*_task_done', user.msg):
        text = 'Вы точно хотите поставить статус "выполнена" для задачи ' + \
               '<b>' + user.users_property('crm_number') + '</b>'
        Helpers.yes_no_menu(context.bot, chat_id, text)

    elif user.prev_msg == 'Изменить статус' and user.msg:
        if re.search(r'crm_(\d)*_task_(open|done|close|suspend)', user.msg):
            status = 'не определен!'
            if re.search(r'open', user.msg):
                status = 'открыта'
            elif re.search(r'done', user.msg):
                status = 'выполнена'
            elif re.search(r'close', user.msg):
                status = 'закрыта'
            elif re.search(r'suspend', user.msg):
                status = 'отложена'
            text = 'Вы точно хотите поставить статус "' + status + '" для задачи ' + \
                   '<b>' + user.users_property('crm_number') + '</b>'
            Helpers.yes_no_menu(context.bot, chat_id, text)

    elif user.prev_msg == 'CRM' and user.msg in config.ch_host_list.keys():
        # bg_config['server'] = config.bg_config['server'].replace(config.default_host, config.ch_host_list[user.msg])
        # print(bg_config)
        user.bg_servername = config.ch_host_list[user.msg]
        user.users_property('bg_servername', 'insert', user.bg_servername)
        text = 'Введите номер задачи:'
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif user.msg == 'Нет':
        text = '<code>Вы отменили предыдущее действие!</code>'
        if user.users_property('report') == 'unplug_badge':
            user.users_property('report', 'insert', ' ')
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif re.search(r'send_photo|send_document', user.prev_msg) and user.msg == 'Да':
        msg_type = user.prev_msg
        db = DB(db_config)
        query = """SELECT teleg_file_id from reports WHERE user_id=%d""" % user.user_id
        file_id = db.sql_execute(query)[0]

        query = """SELECT filesize from reports WHERE user_id=%d""" % user.user_id
        filesize = db.sql_execute(query)[0]

        file = context.bot.getFile(file_id)

        # if user.msg == 'send_photo' and user.prev_msg == 'Да':
        if filesize > 20971520:
            text = '<code>Размер файла более 20Мб. \nМожно загружать файлы не более 20Мб.</code>'
            context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
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
                    key = next((k for k in config.processing_photo_list if config.processing_photo_list[k]['name'] == description), None)
                    if key is None:
                        context.bot.send_message(chat_id=user.chat_id, text='<code>ДОБАВЛЕНО</code>', parse_mode='HTML')
                    else:
                        txt = '<code>Данные сохранены</code>'
                        context.bot.send_message(chat_id=chat_id, text=txt, parse_mode='HTML')

                        if 'unplug_' not in user.users_property('report'):
                            Helpers.unplug_processing(context.bot, chat_id, reply_markup, crm_number)
                        if user.users_property('report') in ['unplug_not_connected', 'unplug_closed_object']:
                            data = {'username': user.name, 'responsible': config.tech_department_supervisor, 'user': user}
                            txt = Helpers.func_unplug_processing_finish(crm_number, data)
                            user.user_crm_info[user_id] = BG.crm_info(crm_number, user_id)
                            context.bot.send_message(chat_id=chat_id, text=txt, parse_mode='HTML')
                else:
                    text = '<b>Ошибка:</b> %s! Попробуйте повторить предыдущее действие заново.' % res['message']
                    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
            else:
                text = '<code>Не выбрана задача для работы! Пожалуйста, сначала выберите пункт "CRM".</code>'
                context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
    elif re.search(r'processing_tree#(\d)*#(\d)', user.msg):
        proc_list = user.msg.split('#')  # 'debt_processing_tree#%s#1.1'
        processing_tree = proc_list[0]
        crm_number = proc_list[1]
        tree_queue = proc_list[2]
        call_data = Helpers.tree_handler(processing_tree, tree_queue, crm_number)
        if isinstance(call_data, str):
            # if re.search(r'func_', call_data) and re.search('#CRM#', call_data, re.IGNORECASE):
            #     call_data.replace('#CRM#', crm_number)
            #     user.users_property('last_msg', 'insert', call_data)

            if re.search(r'func_', call_data):
                data_list = call_data.split('#')
                func_name = data_list[0]
                additional_param = ''
                if len(data_list) > 1:
                    additional_param = data_list[1]
                # user.users_property('last_msg', 'insert', func_name)
                # print(func_name)
                # print(additional_param)
                text = getattr(Helpers, func_name)(processing_tree, tree_queue, additional_param)
                # print(tree_queue)
                if func_name == 'func_processing_debt_paid':
                    pay_method = re.search(r'Метод оплаты:\s*<b>(.+)</b>', text, re.IGNORECASE)[1]
                    user.users_property('last_msg', 'insert', '%s#%s' % (func_name, pay_method))
                else:
                    user.users_property('last_msg', 'insert', call_data)
            else:
                text = 'действие не задано!'

            context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            # print(call_data)
            menu_col_count = 1 if len(call_data) >= 3 else len(call_data)
            separator = '------------------'
            text, reply_keyboard = Helpers.gen_inline_kb(call_data, '<code>%s\nВыберите действие:</code>' % separator,
                                                         menu_col_count)
            context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_keyboard, parse_mode='HTML')
    # elif re.search(r'debt_processing_tree#(\d)*#(\d)', user.prev_msg):
    #     pass
    elif re.search(r'save_badge_number#(\d+)', user.msg):
        text = 'Введите номер бирки'
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

    elif user.msg == 'Да' and user.users_property('report') == 'unplug_badge':
        # print("from user.users_property('report') == 'unplug_badge'" + user.prev_msg)
        crm_num = user.users_property('crm_number')
        bg_id = user.users_property('bg_id')
        badge_number = user.msg
        try:
            contract_id = user.user_crm_info[user_id]['clean_data']['contract']['id']
        except Exception:
            contract_id = BG.crm_info(crm_num, user_id)['data']['contract']['id']

        text = Helpers.func_processing_save_badge_number(crm_num, user, bg_id, contract_id, badge_number)
        text = text + Helpers.func_processing_change_task_status(crm_num, user, user_id)  # status='выполнена'
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')

        # TODO: do autorefresh crm history data after add comment
        user.user_crm_info[user_id] = BG.crm_info(crm_num, user_id)
    else:
        context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')


def photo(update: Update, context: CallbackContext):
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

        text = 'Вы хотите добавить данное фото в фотоотчет по задаче <b>%s</b>?' % user.users_property('crm_number')
        Helpers.yes_no_menu(context.bot, chat_id, text)

    elif re.search(r'func_processing_add_photo#\w+', user.prev_msg):
        try:
            processing_type = re.search(r'func_processing_add_photo#(\w+)', user.prev_msg)[1]
        except Exception:
            processing_type = 'not found'
        photo_name = config.processing_photo_list[processing_type]['name']
        db = DB(db_config)
        f_id = update.message.photo[len(update.message.photo) - 1].file_id
        f_size = update.message.photo[len(update.message.photo) - 1].file_size
        query = """REPLACE INTO reports (user_id, teleg_file_id, filesize, url, description) \
                VALUES (%d, '%s', %d, '%s', '%s')""" % (user_id, f_id, f_size, None, photo_name)
        db.sql_execute(query)

        text = 'Вы точно хотите добавить фото: <b>"%s"</b> в фотоотчет по задаче <b>%s</b>?' % \
               (photo_name, user.users_property('crm_number'))
        Helpers.yes_no_menu(context.bot, chat_id, text)

        if processing_type in ['unplug_badge', 'unplug_not_connected', 'unplug_closed_object']:
            user.users_property('report', 'insert', processing_type)
        if processing_type == 'unplug_badge':
            text = 'после подтверждения предыдущего действия выберите <b>"Указать номер бирки"</b>:'
            call_data = {'Указать номер бирки': 'save_badge_number#%s' % user.users_property('crm_number')}
            text, reply_keyboard = Helpers.gen_inline_kb(call_data, text)
            context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_keyboard, parse_mode='HTML')


def document(update: Update, context: CallbackContext):
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
    Helpers.yes_no_menu(context.bot, chat_id, text)
