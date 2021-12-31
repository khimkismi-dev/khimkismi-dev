# !/usr/bin/python3
# -*- coding: utf-8 -*
import random
from random import randint
import re
import smtplib as smtp
from email.header import Header
from email.mime.text import MIMEText
import telegram

import config
from local_helpers import Helpers
from local_db import DB, DBPsql
from local_bg import BG

db_config = config.db_config


class User:
    """class for working with Users Table"""
    user_data = {}
    email_code = {}
    user_crm_info = {}

    def __init__(self, user_table, user_id, chat_id, msg):
        """Constructor"""
        self.user_table = user_table
        self.user_id = user_id
        self.chat_id = chat_id
        self.msg = msg
        self.prev_msg = ''
        self.bg_id = ''
        self.email = ''
        self.name = ''
        self.phone = ''
        self.crm_number = False
        self.bg_servername = ''
        self.to_history_msg = ''

    # состояние пользователя
    def user_state(self):
        return {
            'id': self.user_id,
            'bg_id': self.bg_id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'last_msg': self.msg,
            'crm_number': self.crm_number,
        }
        # if self.is_reg():
        #     for key in state:
        #         if not state[key]:
        #             state[key] = self.users_property(key)
        # return state

    def infinity_call(self, abonent_phone):  # '89269423682' - тестовый номер "абонента" Иванов А.С.
        db = DBPsql(config.db_inf_config)
        host = self.users_property('bg_servername')
        target_table = config.inf_call_tables[host]
        get_max_id_query = """SELECT max("ID") FROM "%s";""" % target_table
        max_id = db.sql_execute(get_max_id_query)[0]
        if max_id is None:
            max_id = randint(1000000, 9999999)

        next_id = int(max_id) + 1

        user_phone = self.users_property('phone')
        user_phone = re.sub(r'\D', '', user_phone)
        # print('user_phone=%s' % user_phone)
        abonent_phone = re.sub(r'\D', '', abonent_phone)
        # print('abonent_phone=%s' % abonent_phone)

        if user_phone is None:
            return "Поле с телефоном пользователя не заполнено!"
        elif len(user_phone) < 11:
            return "Некорректный формат номера пользователя!"
        elif len(abonent_phone) < 11:
            return "Некорректный формат номера абонента!"
        else:  # добавляем в кампанию автоинформатор строку для звонка
            db = DBPsql(config.db_inf_config)
            crm_number = self.users_property('crm_number')
            add_call_query = """INSERT INTO "%s" ("ID", abonent_phone, serviceman_phone, crm) VALUES (%d, '%s', '%s', '%s')""" % (
                target_table, next_id, abonent_phone, user_phone, crm_number)
            db.sql_execute(add_call_query)
            return "<code>В течение 1 минуты ожидайте звонка от Инфинити и соединения с абонентом!</code>"

    # получение информации о пользователе
    def get_user_data(self):
        if self.is_reg():
            db = DB(db_config)
            query = "SELECT `id`," \
                    "`bg_id`, " \
                    "`email`, " \
                    "`name`, " \
                    "`phone`, " \
                    "`last_msg`, " \
                    "`bg_servername`, " \
                    "`crm_number`" \
                    "FROM users WHERE id='%s';" % self.user_id
            return db.sql_execute(query)
        else:
            return False

    @staticmethod
    # добавление нового пользователя
    def add_new(user_data):
        query = "INSERT INTO users (`id`," \
                "`bg_id`, " \
                "`email`, " \
                "`name`, " \
                "`phone`, " \
                "`last_msg`, " \
                "`bg_servername`, " \
                "`crm_number`) " \
                "VALUES ('%d','%d','%s','%s','%s','%s','%s','%d');" % \
                (user_data['id'],
                 user_data['bg_id'],
                 user_data['email'],
                 user_data['name'],
                 user_data['phone'],
                 user_data['last_msg'],
                 config.default_host,
                 user_data['crm_number'],
                 )
        db = DB(db_config)
        return db.sql_execute(query)

    # попытка регистрации
    def reg_try(self, email_dst):
        text = '<b>Вы не зарегистрированы!</b> ' \
               '\nПожалуйста, нажмите кнопку [Регистрация]'
        if self.msg and "@" in self.msg:
            resp = BG.check_mail(self.msg.strip(), self.user_id)
            # print(resp)
            if resp['code'] == 0:  # значит запрос успешный!
                email_dst = self.msg  # 'ivanov.andrey.serg@gmail.com' - for test
                User.email_code[self.user_id] = str(random.randint(4001, 9999))
                # print(User.email_code)

                try:
                    self.send_email(email_dst, User.email_code[self.user_id])
                    User.user_data = {
                        'id': self.user_id,
                        'bg_id': resp['data']['id'],
                        'email': email_dst,
                        'name': resp['data']['name'],
                        'phone': None,
                        'last_msg': None,
                        'bg_servername': config.default_host,
                        'crm_number': 0
                    }
                    text = '<b>На указанную почту отправлен код подтверждения.</b>' \
                           '\nВведите его сюда.'
                except Exception as err:
                    text = str(err)
                    text = text + '\nНе удалось отправить код! \nПопробуйте заново'
            else:
                text = '<b>К сожалению, указанный email не зарегистрирован в системе BGBilling!</b>'
        elif self.msg.isdigit():  # get_last_msg()
            if User.email_code[self.user_id] == self.msg:
                try:
                    self.add_new(User.user_data)
                    text = '<b>Поздравляю, Вы зарегистрировались!</b>' \
                           '\nМожете пользоваться сервисами.'
                    self.menu()
                except Exception as err:
                    text = '<b>Неуспешная попытка регистрации!</b>\nПожалуйста, попробуйте заново.\n' + str(err)
            else:
                text = '<b>Введен неверный код!</b> \nНеобходимо повторить процедуру регистрации сначала.'

        elif self.msg == 'Регистрация':
            text = 'Пожалуйста, отправьте боту Ваш корпоративный email' \
                   '\n<code>Например: ivanov@gmail.com</code>'
        # else:
        #     text = '<b>Что-то пошло не так! \nПожалуйста, попробуйте начать сначала</b>'

        return text

    # проверка регистрации
    def is_reg(self):
        query = "SELECT 1 FROM %s WHERE id='%d';" % (self.user_table, self.user_id)
        db = DB(db_config)
        res = db.sql_execute(query)
        # print(res)
        if len(res) > 0:
            return True
        else:
            return False

    # отправка кода через e-mail для регистрации нового пользователя
    @staticmethod
    def send_email(email_dest, email_text, subj='Код подтверждения TelegramBot:'):
        smtp_host = config.mail_host
        login = config.email_address
        password = config.email_pswd

        # Create a secure SSL context
        # context = ssl.create_default_context()

        msg = MIMEText(email_text, 'html', 'utf-8')  # plain
        msg['Subject'] = Header(subj, 'utf-8')
        msg['From'] = login
        msg['To'] = email_dest  # 'ivanov.andrey.serg@gmail.com'#

        s = smtp.SMTP_SSL(host=smtp_host, port=465)  # smtp.SMTP(smtp_host, 587, timeout=10)
        # s.set_debuglevel(1)

        try:
            # s.starttls(context=context)
            s.login(login, password)
            s.sendmail(msg['From'], email_dest, msg.as_string())
        finally:
            # print(msg)
            s.quit()

    # получение таблицы пользователя ('not_reg_users' - для незарег., 'users' - для зарег.)
    def get_user_table(self):
        if self.is_reg():
            user_tbl = self.user_table
        else:
            user_tbl = 'not_reg_users'
        return user_tbl

    # получение или вставка единичного значения поля из таблицы
    def users_property(self, field, action='select', insert_text=''):
        if insert_text == '':
            insert_text = self.msg
        result = False
        db = DB(db_config)

        table = self.get_user_table()

        check_col = "SELECT 1 FROM information_schema.COLUMNS " \
                    "WHERE TABLE_SCHEMA = '%s' " \
                    "AND TABLE_NAME = '%s' " \
                    "AND COLUMN_NAME = '%s';" % (db_config['db_name'], table, field)

        if not db.sql_execute(check_col):
            return result

        elif action == 'select':
            query = "SELECT %s FROM %s WHERE id='%d';" % (field, table, self.user_id)
            res = db.sql_execute(query)
            if res and len(res):
                result = res[0]

        elif action == 'insert':
            q = "SELECT id FROM %s WHERE id=%d;" % (table, self.user_id)
            res = db.sql_execute(q)
            if len(res) > 0:
                query = "UPDATE %s SET %s='%s' WHERE id=%d;" % (table, field, insert_text, self.user_id)
            else:
                query = "INSERT INTO %s (id, %s) VALUES (%d, '%s');" % (table, field, self.user_id, insert_text)
            db.sql_execute(query)

        return result

    # возвращает клавиатуру меню
    def menu(self):
        # список кнопок
        inline_kb = False
        not_reg_kb = [[telegram.KeyboardButton('Регистрация')]]
        custom_keyboard = Helpers.main_menu()
        if self.is_reg():
            # print('prev_msg=' + self.prev_msg)
            # логика меню
            text = 'Выберите интересующий пункт:'

            if self.msg == '/start':
                text = Helpers.time_of_day() + '\n' + text

            elif self.msg == 'Нет':
                text = '<code>Вы отменили предыдущее действие!</code>'

            elif self.msg == 'CRM':
                call_data = {'ХимкиСМИ': 'ch_host_to_himki', 'Гигавайдер': 'ch_host_to_gigavider'}
                text, inline_kb = Helpers.gen_inline_kb(call_data, text, 2)
                text = 'Выберите в какой базе ищем'
                # text = 'Введите номер задачи'

            elif self.prev_msg in config.ch_host_list.keys() and self.msg not in config.menu_items:
                if self.msg.isdigit():
                    self.crm_number = self.msg
                    self.users_property('crm_number', 'insert')
                    self.user_crm_info[self.user_id] = BG.crm_info(self.crm_number, self.user_id)
                    self.user_crm_info[self.user_id]['crm_number'] = self.crm_number
                    host_str = '<code>(Провайдер: %s)</code>\n' % \
                               (config.provider_names[config.ch_host_list[self.prev_msg]])
                    text = host_str + self.user_crm_info[self.user_id]['text']
                else:
                    text = 'Некорректный ввод, попробуйте заново!'

            elif re.search(r'func_processing_debt_paid#\w+', self.prev_msg):
                if Helpers.is_number(self.msg.replace(',', '.')):
                    paid_sum = self.msg.replace(',', '.')
                    # print('paid_sum=%s\n' % paid_sum)
                    # print(self.prev_msg)
                    user_name = self.users_property('name')
                    crm_number = self.users_property('crm_number')
                    
                    try:
                        pay_method = re.search(r'func_processing_debt_paid#(.+)', self.prev_msg)[1]
                        comment = 'Оплачено: %s\nСпособ оплаты: %s\n' % (paid_sum, pay_method)
                        crm_add_comment_res = BG.crm_add_comment(crm_number, comment, user_name, self.user_id)
                        if crm_add_comment_res['code'] == 0:
                            text = '<code>В задачу %s Добавлен комментарий: </code>\n%s' % (crm_number, comment)

                            crm_ch_status_res = BG.crm_ch_status(crm_number, 'выполнена', user_name, self.user_id)
                            if crm_ch_status_res['code'] == 0:
                                text = text + '\n<code>Статус задачи %s изменен на "выполнена"</code>' % crm_number
                            else:
                                text = text + '\n<b>Не удалось изменить статус задачи на "выполнена"!</b>'

                            self.crm_number = crm_number
                            self.user_crm_info[self.user_id] = BG.crm_info(self.crm_number, self.user_id)
                            self.user_crm_info[self.user_id]['crm_number'] = self.crm_number
                        else:
                            text = '<code>Ошибка добавления комментария: %s</code>' % crm_add_comment_res['message']
                    except Exception:
                        text = '<code>Не определен способ оплаты!</code>'

                    resp = BG.crm_set_checkpoint(crm_number, config.done_checkpoint, user_name, self.user_id)
                    if resp['code'] == 0:
                        text = text + '\n<code>Проставлен чек-поинт "%s"</code>' % config.done_checkpoint
                    else:
                        text = text + '\n<b>Не удалось проставить чекпоинт "%s"!</b>' % config.done_checkpoint
                else:
                    text = '<b>Некорректный ввод!</b>\n' \
                           '<code>Попробуйте выбрать предыдущее действие и повторить ввод заново!</code>'

            elif self.msg == 'Активация':
                if self.user_id in self.user_crm_info and self.user_crm_info[self.user_id]:
                    contract_num = self.user_crm_info[self.user_id]['clean_data']['contract']['title']
                    splited = contract_num.split(" ")
                    contract_num = splited[0]
                    text = 'Вы действительно хотите активировать договор <b>' + str(contract_num) + '</b>?'
                else:
                    text = 'Для начала выберите задачу для работы!'

            elif self.prev_msg == 'Активация' and self.msg == 'Да':
                contract_num = self.user_crm_info[self.user_id]['clean_data']['contract']['title']
                usr = self.users_property('name')
                res = BG.ab_activate(contract_num, usr, self.user_id)
                if res['code'] == 0:
                    text = 'Активация договора <b>' + str(contract_num) + '</b> выполнена'
                else:
                    text = res['message']

            elif self.msg == 'Последняя в работе':
                self.crm_number = self.users_property('crm_number')
                if self.crm_number != '0':
                    self.user_crm_info[self.user_id] = BG.crm_info(self.crm_number, self.user_id)
                    text = self.user_crm_info[self.user_id]['text']
                    self.user_crm_info[self.user_id]['crm_number'] = self.crm_number
                else:
                    text = '<code>Для начала работы выберите пункт "CRM"!</code>'

            elif self.msg == 'Добавить работы':
                crm_num = self.users_property('crm_number')
                if crm_num:
                    work_list = BG.get_work_list(crm_num, self.user_id)
                    call_data = {}
                    text = already_added = ""
                    if len(work_list):
                        for work_id, info in work_list.items():
                            if info['already_added'] != "0":
                                work_txt = '\nРабота: <code>%s</code> \nКол-во: <code>%s</code>\n' % \
                                           (info['url'], info['already_added'])
                                already_added = already_added + work_txt
                            call_data[info['url'][:64]] = 'add_work_{}_{}'.format(work_id, crm_num)  # 64 symbols limit

                        if len(already_added):
                            text = 'Список уже добавленных работ:\n' + already_added

                        text = text + '\n<b>Список возможных работ по задаче %s:</b>' % crm_num
                        text, inline_kb = Helpers.gen_inline_kb(call_data, text)
                    else:
                        text = text + 'список пуст!'
                else:
                    text = 'Для начала необходимо выбрать задачу для работы'

            elif self.msg == 'Тест кабеля':
                if self.user_id not in self.user_crm_info:
                    text = 'Пожалуйста, для начала выберите пункт <b>"CRM"</b> '  # + ' или <b>"Последняя в работе"</b>'
                else:
                    self.crm_number = self.user_crm_info[self.user_id]['crm_number']
                    res = BG.get_cable_test(self.crm_number, self.user_id)
                    if res['code'] == 0:
                        if res['data']['cable']['log'] == '':
                            text = 'Нет информации!'
                        else:
                            text = "<code>Тест кабеля по задаче %s:</code>\n %s" % \
                                   (self.crm_number, res['data']['cable']['log'])
                            call_data = {'Внести в задачу': 'to_history_crm_%s' % self.crm_number}
                            text, inline_kb = Helpers.gen_inline_kb(call_data, text)
                    else:
                        text = res['message']

            elif self.msg == 'История задачи':
                crm_number = self.users_property('crm_number')
                if self.user_id not in self.user_crm_info and (crm_number == '' or crm_number is None):
                    text = 'Пожалуйста, для начала выберите пункт <b>"CRM"</b> '  # + ' или <b>"Последняя в работе"</b>'
                else:
                    if self.user_id not in self.user_crm_info.keys():
                        self.user_crm_info[self.user_id] = BG.crm_info(crm_number, self.user_id)
                        self.user_crm_info[self.user_id]['crm_number'] = crm_number
                    # print(self.user_crm_info)
                    text = self.user_crm_info[self.user_id]['history'].replace('\n\n\n', '\n\n')
                    if text == '' or text is None:
                        text = 'История по задаче <b>{crm_number}</b> не найдена!'.format(crm_number=self.crm_number)

            elif self.msg == 'Да' and self.prev_msg in BG.get_group_list(self.user_id):
                # print(self.prev_msg)
                crm_number = self.users_property('crm_number')
                usr = self.users_property('name')
                res = BG.crm_ch_group(crm_number, self.prev_msg, usr, self.user_id)
                if res['code'] == 0:
                    text = 'Задача переведена на [' + self.prev_msg + ']'
                else:
                    text = res['message']

            elif re.search(r'crm_(\d)*_task_delegate', self.prev_msg) and self.msg not in BG.get_group_list(
                    self.user_id):
                usr = self.users_property('name')
                crm_num = self.users_property('crm_number')
                res = BG.crm_ch_resp(crm_num, self.msg, usr, self.user_id)
                if res['code'] == 0:
                    text = 'Задача переведена на [' + self.msg + ']'
                else:
                    text = res['message']

            elif re.search(r'crm_(\d)*_history_change', self.msg):
                self.crm_number = re.search(r'\d+', self.msg).group(0)
                text = 'Введите текст для добавления в историю изменений по задаче ' + \
                       '<b>' + str(self.crm_number) + '</b>'

            elif re.search(r'crm_(\d)*_history_change', self.prev_msg) and self.msg:
                self.crm_number = re.search(r'\d+', self.prev_msg).group(0)
                comment = self.msg
                user = self.users_property('name')
                res = BG.crm_add_comment(self.crm_number, comment, user, self.user_id)
                if res['code'] == 0:
                    text = 'Комментарий успешно добавлен'
                    self.user_crm_info[self.user_id] = BG.crm_info(self.crm_number, self.user_id)
                    self.user_crm_info[self.user_id]['crm_number'] = self.crm_number
                else:
                    text = 'Данные не отравлены! \n<code>Код ошибки=[' + str(res['code']) + ']. '
            elif re.search(r'crm_(\d)*_task_done', self.msg) or self.prev_msg == 'Изменить статус':
                text = '<code>Изменение статуса задачи</code>'
            elif re.search(r'crm_(\d)*_task_(open|done|close|suspend)', self.prev_msg) and self.msg == 'Да':
                status = 'не определен!'
                if re.search(r'open', self.prev_msg):
                    status = 'открыта'
                elif re.search(r'done', self.prev_msg):
                    status = 'выполнена'
                elif re.search(r'close', self.prev_msg):
                    status = 'закрыта'
                elif re.search(r'suspend', self.prev_msg):
                    status = 'отложена'

                crm_number = self.users_property('crm_number')
                user = self.users_property('name')
                res = BG.crm_ch_status(crm_number, status, user, self.user_id)
                # print('result: ')
                # print(res)
                if res['code'] == 0:
                    text = 'Задача ' + status + '!'
                else:
                    text = 'Ошибка закрытия задачи! ' + res['message'] if 'message' in res else ''

            elif self.msg == 'Изменить статус':
                text = 'Выберите статус, в который хотите перевести задачу ' + '<b>' + \
                       str(self.users_property('crm_number')) + '</b>'

            elif self.msg == 'Фотоотчет':
                crm_num = self.users_property('crm_number')
                if crm_num:
                    crm_url_list = BG.get_url_list(crm_num, self.user_id)
                    if self.user_crm_info and "type" in self.user_crm_info[self.user_id]['clean_data']:
                        try:
                            crm_type = config.crm_types[self.user_crm_info[self.user_id]['clean_data']['type']]
                            call_data = {}
                            ind = 0

                            for key in config.report_points[crm_type]['calldaata_short_text']:
                                ind = ind + 1
                                call_data[key] = 'crm_{}_report_photo_{}_{}'.format(str(crm_num), ind, crm_type)
                                # example: 'crm_243245_report_photo_1_inetflmk'

                            text, inline_kb = Helpers.gen_inline_kb(call_data)
                            text = '\nВыберите какое фото хотите загрузить:\n' + text
                        except KeyError:
                            text = '\nПо данному типу задачи нет списка для фотоотчета!\n' + text
                    else:
                        text = '\nПо данному типу задачи нет списка для фотоотчета!:\n' + text

                    if not crm_url_list:
                        text_header = 'На данный момент к задаче не прикреплено ни одной ссылки!\n'
                    else:
                        text_header = '<code>Прикрепленные к задаче ссылки:</code>'
                        num = 0
                        for item in crm_url_list:
                            num = num + 1
                            text_header = text_header + '\n\n<code>Ссылка ' + str(num) + \
                                          '</code>\n    <b>Описание:</b> ' + item['description'] + \
                                          '\n    <b>url:</b> ' + item['url'] + '\n'
                        # print(crm_url_list)
                    text = text_header + text
                else:
                    text = 'Для начала необходимо выбрать задачу для работы'

            elif self.msg == 'Мои задачи':
                bg_id = self.users_property('bg_id')
                res = BG.get_active_tasks(self.user_id, bg_id)
                if res['code'] == 0:
                    if res['data']:
                        crm_data = '\n'
                        crm_count = len(res['data'])
                        text = 'Список Ваших задач <b>[всего %s]</b>:\n' % crm_count
                        text = text + '<code>провайдер %s\n</code>' % self.users_property('bg_servername')
                        if crm_count > 10:
                            text = text + '(показаны первые 10)\n'
                            res['data'] = res['data'][:10]
                        for crm_item in res['data']:
                            crm_data = crm_data + \
                                       '\n<b>ID задачи:</b> %s\n' % crm_item['id'] + \
                                       '<b>выполнить до:</b> %s\n' % crm_item['deadline'] + \
                                       '<b>Тип:</b> %s\n' % crm_item['type'] + \
                                       '<b>Тема:</b> %s\n' % crm_item['subject'] + \
                                       '<b>Абонент:</b> %s\n' % crm_item['abonent'] + \
                                       '<b>Адрес:</b> %s \n' % (
                                           crm_item['адрес'] if 'адрес' in crm_item else 'не указан')

                        text = text + crm_data
                    else:
                        text = '<code>У Вас нет активных задач.</code>'
                else:
                    text = 'Ошибка: ' + res['message']

            if self.msg == 'Чек-поинты':
                crm_num = self.users_property('crm_number')
                if crm_num:
                    # print(BG.get_checkpoint_list(crm_num))
                    checkpoint_list = BG.get_checkpoint_list(crm_num, self.user_id)
                    text = 'Список доступных чек-поинтов \nпо задаче <b>%s</b>:\n' % crm_num
                    call_data = dict(zip(checkpoint_list, checkpoint_list))
                    if not checkpoint_list:
                        text = text + 'список пуст!'
                    else:
                        text = text + '\n<code>Выберите из списка</code>'
                        text, inline_kb = Helpers.gen_inline_kb(call_data, text)
                else:
                    text = 'Для начала необходимо выбрать задачу для работы'

            elif self.msg == 'Изменить статус':
                crm_num = self.users_property('crm_number')
                if crm_num:
                    status_list = {
                        'открыта': 'crm_' + str(crm_num) + '_task_open',
                        'выполнена': 'crm_' + str(crm_num) + '_task_done',
                        'закрыта': 'crm_' + str(crm_num) + '_task_close',
                        'отложена': 'crm_' + str(crm_num) + '_task_suspend'
                    }
                    text, inline_kb = Helpers.gen_inline_kb(status_list)
                else:
                    text = 'Для начала необходимо выбрать задачу для работы'

            elif re.search(r'crm_(\d)*_task_delegate', self.msg):
                call_data = {}
                group_list = BG.get_group_list(self.user_id)
                for item in group_list:
                    call_data[item] = item
                text, inline_kb = Helpers.gen_inline_kb(call_data)
                text = 'Выберите группу, на которую хотите перевести задачу \n' \
                       'или введите вручную фамилию и имя реципиента\n' + text
            # elif self.msg == 'Да' and self.prev_msg in BG.get_group_list(self.user_id):
            #     print('SUCCESS!')

        else:
            text = self.reg_try(self.msg)
            if 'Поздравл' not in text:
                custom_keyboard = not_reg_kb

        if inline_kb:
            reply_markup = inline_kb
        else:
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)

        return text, reply_markup
