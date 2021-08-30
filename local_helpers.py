# !/usr/bin/python3
# -*- coding: utf-8 -*
import datetime
import re
import telegram
import requests
from requests.auth import HTTPBasicAuth

import config
from local_db import DB, DBPsql

db_config = config.db_config


class Helpers(object):
    """class for helpers"""

    @staticmethod
    def get_abon_phones(data):
        abonent_phones = data['phone']
        for delimiter in config.phone_delimiters:
            if data['phone'].find(delimiter) != -1:
                abonent_phones = data['phone'].split(delimiter)
                break
        if not isinstance(abonent_phones, list):
            try:
                abonent_phones = data['phone'].split(',')
            except AttributeError:
                abonent_phones = ['']

        abonent_phones = [str(phone) for phone in abonent_phones]
        abonent_phones = [re.sub(r'\D', '', phone) for phone in abonent_phones]

        return abonent_phones

    @staticmethod
    # главное меню
    def main_menu():
        return [
            [telegram.KeyboardButton('🛠CRM'), telegram.KeyboardButton('🔍Мои задачи')],
            # , telegram.KeyboardButton('✏Изменить статус')
            [telegram.KeyboardButton('✔Чек-поинты'), telegram.KeyboardButton('🚀Активация')],
            [telegram.KeyboardButton('📜История задачи'), telegram.KeyboardButton('📷Фотоотчет')],
            [telegram.KeyboardButton('⬅Последняя в работе'), telegram.KeyboardButton('📏Тест кабеля')],
        ]

    @staticmethod
    # выполнение запроса
    def send_request(server_cfg, endpoint, user_id, send_data=None):
        if send_data is None:
            send_data = {'method': 'get', 'body': {}}
        try:
            server = server_cfg['server']
            db = DB(db_config)
            query = "SELECT bg_servername FROM users WHERE id = '%s';" % user_id
            bg_servername = db.sql_execute(query)
            if len(bg_servername) > 0:
                server = server_cfg['server'].replace(config.default_host, bg_servername[0])
            url = server + endpoint
            # print(url)
            if send_data['method'] == 'post':
                auth = HTTPBasicAuth(server_cfg['user'], server_cfg['pass'])
                # print(send_data['body'])
                r = requests.post(url, auth=auth, json=send_data['body'], verify=server_cfg['verify'])
                # print(r.json())
            else:
                r = requests.get(url, auth=(server_cfg['user'], server_cfg['pass']),
                                 verify=server_cfg['verify'])
            if r.status_code == 200:
                try:
                    response = r.json()
                except Exception:
                    response = {"code": 100, "message": "Не могу получить информацию по указанной задаче! "}
            else:
                response = {"code": 100, "message": "Не могу связаться с сервером BG! "}
            return response
        except requests.exceptions.HTTPError as errh:
            Helpers.logger("BG_ERROR", "ERROR_DESCR: " + "Http Error: " + str(errh))
        except requests.exceptions.ConnectionError as errc:
            Helpers.logger("BG_ERROR", "ERROR_DESCR: " + "Error Connecting: " + str(errc))
        except requests.exceptions.Timeout as errt:
            Helpers.logger("BG_ERROR", "ERROR_DESCR: " + "Timeout Error: " + str(errt))
        except requests.exceptions.RequestException as err:
            Helpers.logger("BG_ERROR", "ERROR_DESCR: " + "OOps: Something Else  " + str(err))

    @staticmethod
    # генерация inline-клавиатуры
    def gen_inline_kb(call_data, text='<code>Выберите из списка ниже:</code>', columns=1):  # bot, chat_id,
        # text = '<code>Выберите из списка ниже:</code>'
        tmp_kb = btn_list = []
        i = 0
        for key in call_data:
            i = i + 1
            if not tmp_kb:
                tmp_kb = [telegram.InlineKeyboardButton(text=key, callback_data=call_data[key])]
            else:
                tmp_kb.append(telegram.InlineKeyboardButton(text=key, callback_data=call_data[key]))
            if i % columns == 0:
                btn_list.append(tmp_kb)
                tmp_kb = []
        reply_keyboard = telegram.InlineKeyboardMarkup(btn_list)
        return text, reply_keyboard

    @staticmethod
    # вывод клавиатуры с ответами "Да", "Нет"
    def yes_no_menu(bot, chat_id, text):
        btn_list = [telegram.InlineKeyboardButton(text="Нет", callback_data="Нет"),
                    telegram.InlineKeyboardButton(text="Да", callback_data="Да")]
        custom_keyboard = [btn_list]
        reply_keyboard = telegram.InlineKeyboardMarkup(custom_keyboard)
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_keyboard, parse_mode='HTML')

    @staticmethod
    # клавиатура с основными действиями по задаче
    def crm_main_actions(bot, chat_id, crm_num, abon_phones=['']):
        crm_num = str(crm_num)
        text = 'Действия по задаче 👇' \
               '\n[Изменение истории], [Изменение ответств.], [Выполнить]'  # , [Фотоотчет]

        btn_list = [
            telegram.InlineKeyboardButton(text="📝", callback_data="crm_" + crm_num + "_history_change"),
            telegram.InlineKeyboardButton(text="📣", callback_data="crm_" + crm_num + "_task_delegate"),
            # telegram.InlineKeyboardButton(text="📷", callback_data="crm_" + crm_num + "_task_photo"),
            telegram.InlineKeyboardButton(text="✅", callback_data="crm_" + crm_num + "_task_done"),
        ]

        # abon_phone = '89269423682' - тестовый номер "абонента" Иванов А.С.
        if abon_phones != ['']:
            if len(abon_phones) == 1:
                abon_phone = abon_phones[0]
                phones_call_data = "infinity_call_" + abon_phone
            else:
                phones_call_data = 'multi_phones_' + ';'.join(abon_phones[4:])
            text = text + ', [Позвонить]'
            # TODO: добавить номер задачи в кнопку позвонить
            btn_list.append(telegram.InlineKeyboardButton(text="📞", callback_data=phones_call_data))

        custom_keyboard = [btn_list]
        reply_keyboard = telegram.InlineKeyboardMarkup(custom_keyboard)
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_keyboard, parse_mode='HTML')

    @staticmethod
    # запись лога
    def logger(user_id, command):
        date = datetime.datetime.now()
        f = open('/home/bot/service_bot/logs', 'a')
        f.write(str(date) + "	ID:" + str(user_id) + "	command:" + str(command) + '\n')
        f.close()

    @staticmethod
    # удаление emoji из текста
    def emoji_remove(text):
        text = ''.join(c for c in text if c <= '\uFFFF')
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   u"\U00002702-\U000027B0"
                                   u"\U000024C2-\U0001F251"
                                   "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        return text

    @staticmethod
    # вычисление времени суток
    def time_of_day():
        # время сообщения
        date_time = datetime.datetime.now()
        hour = date_time.hour
        times_of_day = "Добрый день, "
        # определение времени суток
        if 0 <= hour < 6:
            times_of_day = "Доброй ночи, "

        if 6 <= hour < 12:
            times_of_day = "Доброе утро, "

        if 12 <= hour < 18:
            times_of_day = "Добрый день, "

        if 18 <= hour <= 23:
            times_of_day = "Добрый вечер, "

        return times_of_day
