# !/usr/bin/python3
# -*- coding: utf-8 -*
import re
import urllib.parse
import copy

import config
from local_helpers import Helpers

bg_config = copy.deepcopy(config.bg_config)


class BG(object):
    """class for working with BG"""

    endpoints = {
        'check_mail': '/api/?action=User&email='
    }

    @staticmethod
    # проверка зарегистрирован ли пользователь с указанным email в BG
    def check_mail(mail, user_id):
        endpoint = '/api/?action=User&email=' + mail.lower()
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # присваиваем данные, полученные из БГ (CRM), согласно ключам из шаблона + кастом
    def crm_data_assign(crm_info, result, data, crm_num):
        echo_tpl = config.crm_tpl
        for key in echo_tpl:
            if key in data:
                mean = data[key]
                if key == 'contract':
                    tariffs = 'нет информации'
                    if isinstance(data[key]['tariffs'], list):
                        if len(data[key]['tariffs']) > 0:
                            list_mean = []
                            for item in data[key]['tariffs']:
                                list_mean.append(', '.join(list(item.values())))
                            tariffs = re.sub(r'( - )?\d{2,} руб/мес( - )?', r'', '; '.join(list_mean))
                    # print(data[key])
                    balance_modified = "положительный" if data[key]['balance'] >= 0 else "отрицательный"

                    if data[key]['limit'] > data[key]['balance']:
                        limit_modified = "отрицательный"
                    elif data[key]['limit'] < data[key]['balance']:
                        limit_modified = "положительный"
                    else:
                        limit_modified = "не установлен"
                    mean = '\n   <b>Абонент:</b> ' + data['fio'] + '\n' + \
                           '   <b>Номер договора:</b> ' + data[key]['title'] + '\n' + \
                           '   <b>Тарифы:</b> ' + tariffs + '\n' + \
                           '   <b>Баланс:</b> ' + balance_modified + '\n' + \
                           '   <b>Лимит:</b> ' + limit_modified
                if isinstance(mean, list):
                    if len(mean) > 0:
                        list_mean = []
                        for item in mean:
                            list_mean.append(', '.join(list(item.values())))
                        mean = '; '.join(list_mean)
                    else:
                        mean = 'нет информации'
            else:
                mean = ''
                if 'delimiter' not in str(key):
                    mean = 'нет информации'
            result['text'] = result['text'] + '<b>' + str(echo_tpl[key]) + '</b>' + str(mean) + '\n' + \
                             ('\n' if str(key) not in ['delimiter1', 'description'] else '')
        history = ['История по задаче ' + '<b>' + crm_num + '</b>:']
        if isinstance(crm_info['data']['history'], list) and len(crm_info['data']['history']) > 0:
            if len(crm_info['data']['history']) > config.history_max_length:
                history_max_len = str(config.history_max_length)
                history.append('<code>*** история задачи содержит более ' +
                               history_max_len + ' сообщений.'
                                                 '\nОтображено последних ' + history_max_len + ' ***</code>')
            for item in crm_info['data']['history'][-config.history_max_length:]:
                item_text = '<code>' + item['date'] + ' [' + item['user'] + ']' + '</code> ' + '\n' + item['text']
                history.append(item_text)
        else:
            history.append('Пока нет ни одного сообщения ...')
        result['history'] = '\n\n'.join(history)

        return result

    @staticmethod
    # полная информация по задаче
    def crm_info(crm_num, user_id):
        endpoint = '/api/?action=Task&taskId=' + str(crm_num)
        crm_info = Helpers.send_request(bg_config, endpoint, user_id)
        # print(crm_info)

        result = {
            'text': '',
            'history': '',
            'clean_data': ''
        }
        if crm_info['code'] == 0:
            result['clean_data'] = crm_info['data']
            # print(result['clean_data'])
            data = {
                'crm_num': crm_num,
                'status': crm_info['data']['stauts'],
                # 'abonent': crm_info['data']['contract']['name'] if 'name' in crm_info['data']['contract'] else 'не заполнено',
                # 'abonent': crm_info['data']['contract']['title'] if 'title' in crm_info['data']['contract'] else '',
                'contract': crm_info['data']['contract'] if 'contract' in crm_info['data'] else '',
                'subject': crm_info['data']['subject'] if 'subject' in crm_info['data'] else '',
                'author': crm_info['data']['author'] if 'author' in crm_info['data'] else '',
                'description': '\n'.join(crm_info['data']['description'].split('\n')[1:]) if 'description' in crm_info[
                    'data'] else 'отсутствует',
                'responsible': crm_info['data']['responsible'] if 'responsible' in crm_info['data'] else '',
                # 'limit': crm_info['data']['contract']['limit'],
                # 'balance': crm_info['data']['contract']['balance'],
                # 'tariffs': crm_info['data']['contract']['tariffs'] if 'tariffs' in crm_info['data']['contract'] else '',
                'fio': crm_info['data']['fio'] if 'fio' in crm_info['data'] else 'не указано',
                'group': crm_info['data']['group'] if 'group' in crm_info['data'] else 'не указана',
            }

            result = BG.crm_data_assign(crm_info, result, data, crm_num)

        else:
            result['text'] = crm_info['message']

        return result  # Helpers.send_request(bg_config, endpoint)

    @staticmethod
    # изменение статуса задачи
    def crm_ch_status(crm_num, status, user, user_id):
        endpoint = '/api/?action=ChangeTaskStatus&taskId=' + str(crm_num) + '&status=' + status + '&user=' + user
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # добавление комментария по задаче
    def crm_add_comment(crm_num, comment, user, user_id):
        comment = urllib.parse.quote_plus(comment)  # декодируем спецсимволы
        endpoint = '/api/?action=AppendComment&taskId=' + str(crm_num) + '&message=' + comment + '&user=' + user
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # изменение ответственной группы по задаче
    def crm_ch_group(crm_num, group_name, user, user_id):
        endpoint = '/api/?action=ChangeGroup&taskId=' + str(crm_num) + '&group=' + group_name + '&user=' + user
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # изменение ответственного по задаче
    def crm_ch_resp(crm_num, resp_user, user, user_id):
        endpoint = '/api/?action=ChangeResponsible&taskId=' + str(crm_num) + \
                   '&responsible=' + resp_user + '&user=' + user
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # получение списка чекпоинтов по задаче
    def get_checkpoint_list(crm_num, user_id):
        endpoint = '/api/?action=CheckPointList&tid=' + crm_num
        resp_data = Helpers.send_request(bg_config, endpoint, user_id)
        checkpoint_list = []
        if 'data' in resp_data:
            for item in resp_data['data']['check_list']:
                if item['available'] == 'true' and item['selected'] == 'false':
                    # print(item)
                    checkpoint_list.append(item['title'])
        return checkpoint_list  # ['test1','test2'] checkpoint_list

    @staticmethod
    # проставление чек-поинта по задаче
    def crm_set_checkpoint(crm_num, check_point, user, user_id):
        endpoint = '/api/?action=SetCheckPoint&taskId=' + str(crm_num) + '&check_point=' + check_point + '&user=' + user
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # активация абонента
    def ab_activate(contract_num, user, user_id):
        endpoint = '/api/?action=SubscriberActivation&contract_number=' + contract_num + '&user=' + user
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # получение списка групп
    def get_group_list(user_id):
        endpoint = '/api/?action=GroupList'
        resp_data = Helpers.send_request(bg_config, endpoint, user_id)
        group_list = []
        if 'data' in resp_data:
            for item in resp_data['data']:
                group_list.append(item['title'])
        return group_list

    @staticmethod
    # получение списка ссылок, прикрепленных к задаче
    def get_url_list(crm_num, user_id):
        endpoint = '/api/?action=WebLinkList&taskId=' + str(crm_num)
        resp_data = Helpers.send_request(bg_config, endpoint, user_id)
        url_list = []
        if 'data' in resp_data:
            for item in resp_data['data']:
                url_list.append(item)
        return url_list

    @staticmethod
    # добавление ссылки к задаче
    def post_url_to_task(crm_num, user_id, url, description):
        endpoint = '/api/?action=SetWebLink'
        send_data = {
            'method': 'post',
            'body': {
                "taskId": str(crm_num),
                "links": [
                    {"url": url, "description": description}
                ]
            }
        }
        return Helpers.send_request(bg_config, endpoint, user_id, send_data)

    @staticmethod
    # получение результатов тестирования кабеля по номеру задачи
    def get_cable_test(crm_num, user_id):
        endpoint = '/api/?action=VirtualCableTest&taskId=' + str(crm_num)
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # получение активных задач пользователя
    def get_active_tasks(user_id, bg_id):
        endpoint = '/api/?action=GetActiveTasks&userId=' + str(bg_id)
        return Helpers.send_request(bg_config, endpoint, user_id)

    @staticmethod
    # получение списка работ по задаче
    def get_work_list(crm_num, user_id):
        endpoint = '/api/?action=WorkList&taskId=' + str(crm_num)

        resp_data = Helpers.send_request(bg_config, endpoint, user_id)
        work_list = {}
        if 'data' in resp_data:
            for item in resp_data['data']:
                work_list[item['id']] = {
                    'url': item['url'],
                    'already_added': item['already_added'],
                    'scores': item['scores']
                }
        return work_list

    @staticmethod
    # проставление работ по задаче
    def add_work(crm_num, work_id, count, resp_ids, bg_id, user_id):
        str_resp = ",".join(resp_ids)
        endpoint = "/api/?action=WorkAdd&taskId=%s&wid=%s&count=%s&responsible=%s&userId=%d" % \
                   (crm_num, work_id, count, str_resp, bg_id)
        return Helpers.send_request(bg_config, endpoint, user_id)
