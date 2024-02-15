# change_db и get_result_from_db - общие функции для взаимодействия в бд, принимают строку sql

def change_db(conn, sql):  # для внесения изменений в бд типа INSERT, UPDATE
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    conn.commit()


def get_result_from_db(conn, sql):  # для получения данных из бд (SELECT)
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    conn.commit()
    return result


# в следующих функциях вызываются 1 или 2 из тех, что выше

def add_word(conn, values):  # добавляет в новое слово в базу
    symbol, pinyin, translate, level = values['symbol'], values['pinyin'], values['translate'], values['level']
    sql = f'INSERT INTO words(symbol, pinyin, translate, level) VALUES("{symbol}", "{pinyin}", "{translate}", "{level}")'
    change_db(conn, sql)


def change_word(conn, key, new_value, symbol):  # ищет слово с symbol и меняет значение по ключу key на new_value
    sql = f'UPDATE words SET {key} = "{new_value}" WHERE symbol = "{symbol}"'
    change_db(conn, sql)


def add_user(conn, chat_id):
    sql = f'INSERT INTO users(chat_id) VALUES({chat_id})'
    change_db(conn, sql)
    sql = f'INSERT INTO user_settings(chat_id) VALUES({chat_id})'
    change_db(conn, sql)


def check_symbol(conn, symbol):  # проверяет, есть ли слово в базе
    sql = f'SELECT * FROM words WHERE symbol = "{symbol}"'
    return get_result_from_db(conn, sql)


def check_user(conn, chat_id):  # проверяет, есть ли юзер в базе
    sql = f'SELECT * FROM users WHERE chat_id = {chat_id}'
    return get_result_from_db(conn, sql)


def get_user_words(conn, chat_id):  # получает список слов юзера
    sql = f'SELECT w.symbol FROM words as w, users as u, user_words as uw WHERE u.chat_id = {chat_id} and uw.user_id = u.id and uw.word_id = w.id'
    return get_result_from_db(conn, sql)


def search_word(conn, param):  # ищет слово в базе по всем параметрам
    keys = ['symbol', 'pinyin', 'translate']
    result = []
    for key in keys:
        sql = f'SELECT * FROM words WHERE {key} LIKE "%{param}%"'
        result = get_result_from_db(conn, sql)
        if result:
            break
    return result


def check_user_word(conn, chat_id, word_id):  # проверяет, есть ли слово у юзера, если нет, добавляет (см. ниже)
    sql = f'SELECT * FROM user_words as uw, users as u WHERE uw.user_id = u.id and u.chat_id = {chat_id} and uw.word_id = {word_id}'
    result = get_result_from_db(conn, sql)
    print(result)
    if not result:
        sql = f'SELECT id FROM users WHERE chat_id = {chat_id}'
        add_word_to_user(conn, get_result_from_db(conn, sql)[0]['id'], word_id)
        return False
    return True


def add_word_to_user(conn, user_id, word_id):  # добавляет слово юзеру
    sql = f'INSERT INTO user_words(user_id, word_id) VALUES({user_id}, {word_id})'
    change_db(conn, sql)


def get_user_settings(conn, chat_id):
    sql = f'SELECT * FROM user_settings WHERE chat_id = {chat_id}'
    return get_result_from_db(conn, sql)


def change_send_time(conn, chat_id, new_time):
    sql = f'UPDATE user_settings SET send_time = "{new_time}" WHERE chat_id = {chat_id}'
    change_db(conn, sql)


def change_quantity(conn, chat_id, new_quantity):
    sql = f'UPDATE user_settings SET quantity = {new_quantity} WHERE chat_id = {chat_id}'
    change_db(conn, sql)


def change_level(conn, chat_id, new_level):
    sql = f'UPDATE user_settings SET level = {new_level} WHERE chat_id = {chat_id}'
    change_db(conn, sql)
