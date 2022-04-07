# coding=utf-8
TOKEN = '1214783130:AAHk7MdV2tpsnnZ-9afXPP27e9Dcf77jMrE'
BOT_SERVER_IP = '94.143.164.48'
PORT = 8443

bot_folder = '/home/bot/service_bot/'
bot_url = 'http://172.16.0.83:1234/'

# DB
db_config = {
    'db_host': 'localhost',
    'db_name': 'servicemans',
    'db_user': 'root',
    'db_pass': 'jdjobhektp'
}

# BG
bg_port = 8443
gigavider_host = 'my.gigavider.ru'
himkismi_host = 'bill.himkismi.ru'
default_host = gigavider_host
bg_config = {
    'server': 'https://' + default_host + ':' + str(bg_port),
    'user': 'telegram',
    'pass': 'heRnh34_Rh',
    'verify': False  # включение или отключение верификации https запросов
}

ch_host_list = {
    'ch_host_to_himki': himkismi_host,
    'ch_host_to_gigavider': gigavider_host
}

provider_names = {
    himkismi_host: 'ХимкиСМИ',
    gigavider_host: 'Гигавайдер'
}

phone_delimiters = [',', ';']

# EMAIL FOR SEND CODES
email_address = "email.report.bot@gmail.com"
mail_host = "smtp.gmail.com"
email_pswd = 'flV7vZp@'

# BOT SYSTEM
menu_items = [
    'CRM',
    'Добавить работы',  # Последняя в работе
    'Чек-поинты',
    'История задачи',
    'Фотоотчет',
    'Изменить статус',
    'Мои задачи'
]
exclude_crm_action = [
    'CRM',
    'Чек-поинты',
    'Изменить статус'
]
history_max_length = 15
delimiter = '========================'
crm_tpl = {
    'crm_num': '№ задачи: ',
    'contract': 'Инф-ия по договору: ',
    'subject': 'Тема: ',
    'author': 'Автор: ',
    'delimiter1': delimiter,
    'description': 'Описание : 🖊',
    'delimiter2': delimiter,
    'group': 'Группа: ',
    'responsible': 'Ответственный: ',
    'status': 'Статус: ',
}

# Типы задач и соотв. ключи для списков фотографий
crm_types = {
    "Подключение Интернет ФЛ в МК": 'inetflmk',
    "Подключение Интернет+ КТВ  ФЛ в МК": 'inetktvflmk',
    "Подключение КТВ ФЛ в МК": 'ktvfl',
    "Подключение КТВ ФЛ": 'ktvfl',
    "Реорганизация узла": 'reorg',
    "Организация узла": 'reorg',
    "Сервис Центр": 'service',
    "Интернет неисправность": 'service',
}

# Списки загружаемых фотографий (ключи - коды inline-кнопок)
report_points = {
    'inetflmk': {
        'send_photo': {
            1: 'Фото открытого ящика с оборудованием (до подключения кабеля абонента)',
            2: 'Фото закрытого ящика с оборудованием (после подключения кабеля абонента)',
            3: 'Фото установленного оборудования у абонента',
            4: 'Фото скорости абонента со страницы https://www.speedtest.net/ru'
        },
        'calldaata_short_text': {
            '1. Ящик открытый': '',
            '2. Ящик закрытый': '',
            '3. Оборудование': '',
            '4. Speedtest': ''
        }
    },
    'inetktvflmk': {
        'send_photo': {
            1: 'Фото открытого ящика с оборудованием (до подключения кабеля абонента)',
            2: 'Фото закрытого ящика с оборудованием (после подключения кабеля абонента)',
            3: 'Фото установленного оборудования у абонента',
            4: 'Фото скорости абонента со страницы https://www.speedtest.net/ru',
            5: 'Фотография тана (УАР) с биркой, на кабеле подключенного абонента в щитке'
        },
        'calldaata_short_text': {
            '1. Ящик открытый': '',
            '2. Ящик закрытый': '',
            '3. Оборудование': '',
            '4. Speedtest': '',
            '5. Фотография тана (УАР)': ''
        },
    },
    "ktvfl": {
        'send_photo': {
            1: 'Фотография тана (УАР) с биркой, на кабеле подключенного абонента в щитке'
        },
        'calldaata_short_text': {
            '1. Фотография тана (УАР)': ''
        }
    },
    "reorg": {
        'send_photo': {
            1: 'фотография ящика с установленным коммутатором',
            2: 'Фотография коммутатора с наклейкой IP адрес(читабельно)',
            3: 'Фотография подключения к сети 220 В в щитке с автоматом'
        },
        'calldaata_short_text': {
            '1. фотография ящика': '',
            '2. Фотография коммутатора': '',
            '3. Фотография подкл. 220 В': '',
        }
    },
    'service': {
        'send_photo': {
            1: 'Фотография проблемы (причины)',
            2: 'Фотография исправленной проблемы'
        },
        'calldaata_short_text': {
            '1. Фото проблемы': '',
            '2. Фото исправл. проблемы': ''
        }
    },
}

photo_report_text = "<b>Пожалуйста, отправьте боту фото в следующей последовательности:</b>\n" \
                    "<code>1.</code> Фото открытого ящика с оборудованием (до подключения кабеля абонента).\n" \
                    "<code>2.</code> Фото закрытого ящика с оборудованием (после подключения кабеля абонента).\n" \
                    "<code>3.</code> Фото установленного оборудования у абонента.\n" \
                    "<code>4.</code> Фото скорости абонента со страницы https://www.speedtest.net/ru\n"

photo_report_count = 4

report_provider_folders = {
    gigavider_host: 'gigavider',
    himkismi_host: 'khimki'
}

# bot calls
inf_call_tables = {
    himkismi_host: 'Table_5021246795',
    gigavider_host: 'Table_5021246789'
}

db_inf_config = {
    'db_host': '172.16.0.160',
    'db_port': 10000,
    'db_name': 'Cx_Work',
    'db_user': 'cxdbuser',
    'db_pass': 'cxdbwizard'
}

custom_processing_type = {
    'TV неисправности': 'debt_processing',
    'Отключение должников': 'debt_processing'
}

# дерево алгоритма по задаче на отключение
debt_processing_tree = {
    '1. Позвони в дверь': {
        '1. Открыли': {
            '1. Клиент оплатил?': {
                '1. Оплатил на месте': {
                    '1. Указать способ оплаты': {
                        '1. СбербанкОнлайн': {'1. Указать сумму оплаты': 'func_processing_debt_paid'},
                        '2. Личный кабинет': {'1. Указать сумму оплаты': 'func_processing_debt_paid'}
                    }
                },
                '2. Не оплатил': {
                    '1. Приложить фото оставленного уведомления': 'func_processing_add_photo#debt_notification'
                }
            }
        },
        '2. Не открыли': {
            '1. Приложить фото оставленного уведомления': 'func_processing_add_photo#debt_notification'
        }
    }
}

# дерево алгоритма по отключению должников
unplug_processing_tree = {
    '1. Произвести отключение':  {
        '1. Отключение произведено': {'1. Приложить фото бирки': 'func_processing_add_photo#unplug_badge'},
        '2. Отключение не произведено': {
            '1. Указать причину': {
                '1. Клиент фактически не подключен': {
                    '1. Приложить фото слаботочного щитка / фото обрезанного кабеля у входа в квартиру':
                        'func_processing_add_photo#unplug_not_connected'
                },
                '2. Нет доступа к слаботочному щитку': {
                    '1. Приложить фото закрытого объекта': 'func_processing_add_photo#unplug_closed_object'
                },
                '3. Другое': 'func_processing_add_comment'
            }
        }
    }
}

processing_photo_list = {
    'debt_notification': {
        'name': 'Фото уведомления',
        'text': 'Отправь в чат фото оставленного уведомления',
    },
    'unplug_badge': {
        'name': 'Фото бирки',
        'text': 'Отправь ФОТО бирки в чат'
    },
    'unplug_not_connected': {
        'name': 'Клиент не подключен',
        'text': 'Приложи фото слаботочного щитка / фото обрезанного кабеля у входа в квартиру',
        'comment': 'Клиент фактически не подключен.'
    },
    'unplug_closed_object': {
        'name': 'Фото закрытого объекта',
        'text': 'Приложи фото закрытого объекта',
        'comment': 'Нет доступа к слаботочному щитку.'
    },
}

done_checkpoint = 'Заявка выполнена'

# руководитель ТО
tech_department = 'ХИМКИ-СМИ Техотдел'
tech_department_supervisor = 'Александр Паниотов'
