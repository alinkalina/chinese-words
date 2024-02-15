import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from sql import add_word, change_word, check_symbol, check_user, get_user_words, search_word, check_user_word, \
    add_user, get_user_settings, change_send_time, change_quantity, change_level
import traceback
import pymysql
from secret_data import token, developers_list  # токен для бота и список chat.id юзеров, которым доступно вносить изменения в бд
import time


bot = telebot.TeleBot(token)

new_word_params = {}
changing_symbol = {}

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='12345',
                       db='chinese_words',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)


@bot.message_handler(commands=['start'])  # запуск бота и добавление нового юзера в бд
def send_start_message(message):
    bot.send_message(message.chat.id, 'lets start')
    if not check_user(conn, message.chat.id):
        add_user(conn, message.chat.id)


@bot.message_handler(commands=['help'])  # список доступных команд бота
def send_help_message(message):
    bot.send_message(message.chat.id, '/start - старт бота /help - описание команд, инструкция и тд /learnwords - запустить тест на слова /addword - добавить слово в мои слова /mywords - посмотреть список моих слов /settings - настроить кол-во ежедневных слов, уровень и время /modify - добавить, изменить или удалить слово из базы, доступно только разработчикам')


@bot.message_handler(commands=['learnwords'])
def start_learning(message):
    pass


def get_searching_param(param):
    if not param.text.startswith('/'):
        res = search_word(conn, param.text)
        if res:
            markup = InlineKeyboardMarkup()
            for r in res:
                markup.add(InlineKeyboardButton(text=str(r), callback_data=f'choose-word-{r["id"]}'))
            bot.send_message(param.chat.id, 'Вот что мы нашли', reply_markup=markup)
        else:
            msg = bot.send_message(param.chat.id, 'not found')
            bot.register_next_step_handler(msg, get_searching_param)
    else:
        msg = bot.send_message(param.chat.id, 'Поиск прерван')


@bot.message_handler(commands=['addword'])  # добавление слова в список юзера
def add_word_to_list(message):
    msg = bot.send_message(message.chat.id, 'Попробуйте найти слово в базе через иероглиф, пиньинь или перевод')
    bot.register_next_step_handler(msg, get_searching_param)


@bot.message_handler(commands=['mywords'])  # список слов юзера
def send_words_list(message):
    try:
        bot.send_message(message.chat.id, str(get_user_words(conn, message.chat.id)))
    except telebot.apihelper.ApiTelegramException:
        bot.send_message(message.chat.id, 'В Вашем списке пока нет слов. Можете добавить их /addword')


def set_send_time(send_time):
    if not send_time.text.startswith('/'):
        try:
            time.strptime(send_time.text, '%H:%M')
            change_send_time(conn, send_time.chat.id, send_time.text)
            bot.send_message(send_time.chat.id, 'Изменения внесены')
        except ValueError:
            msg = bot.send_message(send_time.chat.id, 'В формате ЧЧ:ММ !!!')
            bot.register_next_step_handler(msg, set_send_time)
    else:
        bot.send_message(send_time.chat.id, 'Запись прервана')


def set_quantity(quantity):
    if not quantity.text.startswith('/'):
        if quantity.text.isdigit() and 0 < int(quantity.text) < 11:
            change_quantity(conn, quantity.chat.id, quantity.text)
            bot.send_message(quantity.chat.id, 'Изменения внесены')
        else:
            msg = bot.send_message(quantity.chat.id, 'От 1 до 10 числом !!!')
            bot.register_next_step_handler(msg, set_quantity)
    else:
        bot.send_message(quantity.chat.id, 'Запись прервана')


def set_level(level):
    if not level.text.startswith('/'):
        if level.text.isdigit() and 0 < int(level.text) < 7:
            change_level(conn, level.chat.id, level.text)
            bot.send_message(level.chat.id, 'Изменения внесены')
        else:
            msg = bot.send_message(level.chat.id, 'От 1 до 6 числом !!!')
            bot.register_next_step_handler(msg, set_level)
    else:
        bot.send_message(level.chat.id, 'Запись прервана')


@bot.message_handler(commands=['settings'])  # изменение настроек
def send_settings(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text='Время отправки', callback_data='change-send-time'))
    markup.add(InlineKeyboardButton(text='Количество слов', callback_data='change-quantity'))
    markup.add(InlineKeyboardButton(text='Уровень слов', callback_data='change-words-level'))
    bot.send_message(message.chat.id, str(get_user_settings(conn, message.chat.id)), reply_markup=markup)


def get_new_symbol(symbol):
    if not symbol.text.startswith('/'):
        if not check_symbol(conn, symbol.text):
            new_word_params[symbol.chat.id]['symbol'] = symbol.text
            msg = bot.send_message(symbol.chat.id, 'Введите пиньинь')
            bot.register_next_step_handler(msg, get_new_pinyin)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text='Изменить', callback_data='change'))
            bot.send_message(symbol.chat.id, 'Такой иероглиф уже записан. Можете его изменить', reply_markup=markup)
    else:
        bot.send_message(symbol.chat.id, 'Запись прервана')


def get_new_pinyin(pinyin):
    if not pinyin.text.startswith('/'):
        new_word_params[pinyin.chat.id]['pinyin'] = pinyin.text
        msg = bot.send_message(pinyin.chat.id, 'Введите перевод')
        bot.register_next_step_handler(msg, get_new_translate)
    else:
        bot.send_message(pinyin.chat.id, 'Запись прервана')


def get_new_translate(translate):
    if not translate.text.startswith('/'):
        new_word_params[translate.chat.id]['translate'] = translate.text
        msg = bot.send_message(translate.chat.id, 'Введите уровень')
        bot.register_next_step_handler(msg, get_new_level)
    else:
        bot.send_message(translate.chat.id, 'Запись прервана')


def get_new_level(level):
    if not level.text.startswith('/'):
        new_word_params[level.chat.id]['level'] = level.text
        try:
            add_word(conn, new_word_params[level.chat.id])
            bot.send_message(level.chat.id, 'Успешно сохранено')
        except Exception as e:
            bot.send_message(level.chat.id, 'Произошла ошибка')
            print(e)
    else:
        bot.send_message(level.chat.id, 'Запись прервана')


def get_changing_symbol(symbol):
    if not symbol.text.startswith('/'):
        current = check_symbol(conn, symbol.text)
        if current:
            changing_symbol[symbol.chat.id] = symbol.text
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text='Иероглиф', callback_data='change-symbol'))
            markup.add(InlineKeyboardButton(text='Пиньинь', callback_data='change-pinyin'))
            markup.add(InlineKeyboardButton(text='Перевод', callback_data='change-translate'))
            markup.add(InlineKeyboardButton(text='Уровень', callback_data='change-level'))
            bot.send_message(symbol.chat.id, f'{current}\nЧто вы хотите изменить?', reply_markup=markup)
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text='Добавить', callback_data='add'))
            bot.send_message(symbol.chat.id, 'Такого иероглифа ещё нет. Сначала добавьте его', reply_markup=markup)
    else:
        bot.send_message(symbol.chat.id, 'Запись прервана')


def get_changed_symbol(symbol):
    try:
        change_word(conn, 'symbol', symbol.text, changing_symbol[symbol.chat.id])
        bot.send_message(symbol.chat.id, 'Успешно сохранено')
    except Exception as e:
        bot.send_message(symbol.chat.id, 'Произошла ошибка')
        print(e)


def get_changed_pinyin(pinyin):
    try:
        change_word(conn, 'pinyin', pinyin.text, changing_symbol[pinyin.chat.id])
        bot.send_message(pinyin.chat.id, 'Успешно сохранено')
    except Exception as e:
        bot.send_message(pinyin.chat.id, 'Произошла ошибка')
        print(e)


def get_changed_translate(translate):
    try:
        change_word(conn, 'translate', translate.text, changing_symbol[translate.chat.id])
        bot.send_message(translate.chat.id, 'Успешно сохранено')
    except Exception as e:
        bot.send_message(translate.chat.id, 'Произошла ошибка')
        print(e)


def get_changed_level(level):
    try:
        change_word(conn, 'level', level.text, changing_symbol[level.chat.id])
        bot.send_message(level.chat.id, 'Успешно сохранено')
    except Exception as e:
        bot.send_message(level.chat.id, 'Произошла ошибка')
        print(e)


@bot.message_handler(commands=['modify'])  # изменить базу слов через бота, только для разработчиков
def modify_db(message):
    if message.chat.id in developers_list:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text='Добавить', callback_data='add'))
        markup.add(InlineKeyboardButton(text='Изменить', callback_data='change'))
        bot.send_message(message.chat.id, 'Вы хотите добавить новое слово или изменить старое?', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'У Вас нет прав на выполнение этой команды')


@bot.callback_query_handler(func=lambda call: True)  # обработка нажатия инлайн кнопок
def function(call):
    mes_id = call.message.message_id
    chat_id = call.message.chat.id
    if call.data == 'add':
        new_word_params[chat_id] = {'symbol': '', 'pinyin': '', 'translate': '', 'level': ''}
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите иероглиф')
        bot.register_next_step_handler(msg, get_new_symbol)
    elif call.data == 'change':
        changing_symbol[chat_id] = ''
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите иероглиф, данные о котором хотите изменить')
        bot.register_next_step_handler(msg, get_changing_symbol)
    elif call.data == 'change-symbol':
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите новый иероглиф')
        bot.register_next_step_handler(msg, get_changed_symbol)
    elif call.data == 'change-pinyin':
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите новый пиньинь')
        bot.register_next_step_handler(msg, get_changed_pinyin)
    elif call.data == 'change-translate':
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите новый перевод')
        bot.register_next_step_handler(msg, get_changed_translate)
    elif call.data == 'change-level':
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите новый уровень')
        bot.register_next_step_handler(msg, get_changed_level)
    elif call.data.startswith('choose-word-'):
        already_saved = check_user_word(conn, chat_id, int(call.data[12:]))
        if already_saved:
            bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='already saved')
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='successfully saved')
    elif call.data == 'change-send-time':
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите ежедневное время отправки новых слов в формате ЧЧ:ММ')
        bot.register_next_step_handler(msg, set_send_time)
    elif call.data == 'change-quantity':
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите количество слов в день числом (от 1 до 10)')
        bot.register_next_step_handler(msg, set_quantity)
    elif call.data == 'change-words-level':
        msg = bot.edit_message_text(chat_id=chat_id, message_id=mes_id, text='Введите уровень сложности новых слов (от 1 до 6)')
        bot.register_next_step_handler(msg, set_level)


try:
    bot.polling()
except Exception as e:
    print(e)
    print(traceback.extract_tb(e.__traceback__))
