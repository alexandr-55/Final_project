# импортируем библиотеки
from flask import Flask, request
import logging
import random

import json
#from test import get_first_name

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}
# создаём словарь, диапазона чисел
sessiondiap = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    # Отправляем request.json и response в функцию handle_dialog. Она сформирует оставшиеся поля JSON,
    # которые отвечают  непосредственно за ведение диалога
    handle_dialog(request.json, response)

    logging.info('Response: %r', request.json)

    # Преобразовываем в JSON и возвращаем
    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']


    if req['session']['new']:        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем Пользователя.

        Init_start_game(user_id)     # заполним словари начальными данными
        res['response']['text'] = 'Привет! Я - Алиса.  Назови свое имя.'
        return

    if res['response']['end_session'] or sessiondiap[user_id]['itis'] == -1:
        res['response']['text'] = 'Игра закончена.  Для продолжения - перезапустите игру'
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, значит, пользователь ещё не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'

        # если нашли, то приветствуем пользователя.
        # и предлагаем поиграть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться!     ' + first_name.title()\
                          + ',   загадай число от 1 до 100, а я попробую его отгадать.'
            res['response']['buttons'] = get_suggests(user_id, sessiondiap[user_id]['regim'])
            # устанавливаем режим 'загадай' - Пользователь загадывает число
            sessiondiap[user_id]['regim'] = 'загадай'
        return

    if sessiondiap[user_id]['regim'] == 'загадай':
        if 'загада'  in req['request']['original_utterance'].lower() and\
            not 'не' in req['request']['original_utterance'].lower():
            # пользователь согласился играть и загадал число
            # показываем первый вопрос
            sessiondiap[user_id]['znak'] = '>'
            res['response']['text'] = 'Тогда начнем.    Задуманное число > %s ?' % (
                sessiondiap[user_id]['itis'])
            res['response']['buttons'] = get_yes_no(user_id)
            # устанавливаем режим 'игра' - Алиса начала отгадывать число
            sessiondiap[user_id]['regim'] = 'игра'
        else:
            # Пользователь отказался от игры
            res['response']['text'] = 'Хорошо.  Поиграем в другой раз...  Пока!'
            res['response']['end_session'] = True
        return

    if sessiondiap[user_id]['regim'] == 'загадай2':
        res['response']['text'] = '%s, теперь твоя очередь отгадывать.  Я ЗАГАДАЛА ЧИСЛО!\
            Задавай мне вопросы, используя слова или знаки сравнения "<" или ">" или "="\
            (но не больше одного условия в вопросе)' % (
                sessionStorage[user_id]['first_name'].title())
        res['response']['buttons'] = get_suggests(user_id, sessiondiap[user_id]['regim'])
        #  !!! Алиса загадала число
        sessiondiap[user_id]['tis'] = random.randint(1, 100)
        sessiondiap[user_id]['regim'] = 'игра2'
        return

    if sessiondiap[user_id]['regim'] == 'игра2':
        # Пользователь начал отгадывать число
        # проанализируем его вопрос
        st = get_User_question(user_id, req['request']['original_utterance'].lower())
        if 'пока' in st.lower():  # пользователь отказался от игры
            res['response']['text'] = st
            res['response']['end_session'] = True
            sessiondiap[user_id]['itis'] = -1
        elif st == 'ok':
            # сюда попадаем если вопрос пользователя понятен
            # случайным образом строим ответ Алисы: "на вопрос" или "на твой вопрос"

            if sessiondiap[user_id]['znak'] != '=':   # Пользователь еще ищет число

                res['response']['text'] = create_Alisa_answer(user_id)

            elif sessiondiap[user_id]['znak'] == '=':   # Пользователь назвал число
                # если отгадал, то определим кто победил
                res['response']['text'] = Itog_game(user_id)
                res['response']['end_session'] = True
        else:
            res['response']['text'] = 'Не поняла твой вопрос  "%s". Ошибка: %s.\
                Пожалуйста, спроси еще раз!' % (req['request']['original_utterance'], st)
        sessiondiap[user_id]['regim'] = 'игра2'
        return

    # сюда попадаем когда начата игра - режим: игра (Пользователь задумал число - Алиса отгадывает)
    st = get_otvet(user_id, req['request']['original_utterance'].lower())
    if st == 'да' or st == 'нет':
        change_diap(user_id, st)
        if find_chislo(user_id):
            res['response']['text'] = '%s, я уже  знаю твое число!  Было задумано число = %s.\
                (мне потребовалось ходов = %s).  Продолжим?' % (
                sessionStorage[user_id]['first_name'].title(), sessiondiap[user_id]['tis'], sessiondiap[user_id]['step'])
            res['response']['buttons'] = get_yes_no(user_id)
            # для перехода в режим, когда Пользователь отгадывает число устанавливаем regim = 'загадай2'
            sessiondiap[user_id]['regim'] = 'загадай2'
            return
        else:
            # сюда попадаем, если Алиса еще не отгадала число
            res['response']['text'] = get_Alisa_question(user_id)
            res['response']['buttons'] = get_yes_no(user_id)
    else:
        res['response']['text'] = 'Не поняла твой ответ  "%s".  Пожалуйста, ответь еще раз!' % (
            req['request']['original_utterance']) #, sessiondiap[user_id]['regim'])


#===================================================================
# Если Пользователь назвал правильно число, то определить победителя
# по кол-ву сделанных ходов
def Itog_game(user_id):

    if sessiondiap[user_id]['tis'] == sessiondiap[user_id]['itis']:
        svictory = 'Верно,  я задумала число ' + str(sessiondiap[user_id]['tis']) + \
                    ' Сделано ходов - ' + str(sessiondiap[user_id]['stepI']) + '. '
        if sessiondiap[user_id]['step'] == sessiondiap[user_id]['stepI']:
            itog = ' Итоги игры: НИЧЬЯ - число ходов одинаковое (по ' + str(sessiondiap[user_id]['step']) + ')'
        elif sessiondiap[user_id]['step'] < sessiondiap[user_id]['stepI']:
            itog = ' Итоги игры: Победа АЛИСЫ (я потратила меньше ходов - ' + str(sessiondiap[user_id]['step']) + ')'
        else:
            itog = ' Итоги игры: Твоя победа!!! (я потратила больше ходов - ' + str(sessiondiap[user_id]['step']) + ')'
        return(svictory + itog)

    else:
        itog = sessionStorage[user_id]['first_name'].title() + ', к сожалению, ОШИБКА!  \
               Я задумала число  '+ str(sessiondiap[user_id]['tis']) + \
               '.  Победила Алиса.  Игра окончена.'
        return(itog)

#=================================================================
# создать ответ Алисы на запрос пользователя
# для разнообразия диалога случайным образом строим ответ Алисы
# в str0
def create_Alisa_answer(user_id):
    sp_ask = ['На вопрос', 'На твой вопрос']
    isp = random.randint(0, len(sp_ask))

    put_name = random.randint(0, 1)
    if put_name == 1:  # перед ответом  вывести имя
        str0 = sessionStorage[user_id]['first_name'].title() + ', ' + sp_ask[isp].lower()
    else:
        str0 = sp_ask[isp]

    if sessiondiap[user_id]['znak'] == '>':
        str0 = str0 + ' > ' + str(sessiondiap[user_id]['itis'])
        if sessiondiap[user_id]['tis'] > sessiondiap[user_id]['itis']:
            return(str0 + '?   Отвечаю -  ДА')
        else:
            return(str0 + '?   Отвечаю -  НЕТ')

    elif sessiondiap[user_id]['znak'] == '<':
        str0 = str0 + ' < ' + str(sessiondiap[user_id]['itis'])
        if sessiondiap[user_id]['tis'] < sessiondiap[user_id]['itis']:
            return(str0 + '?   Отвечаю -  ДА')
        else:
            return(str0 + '?   Отвечаю -  НЕТ')
    else:
        return('')



#=================================================================
# по вопросу Пользователя распознать число и знак сравнения >\<\=
# вернуть:
#   ошибку, которая помешала Алисе понять вопрос
#   или  'ok' - если все верно, тогда из вопроса заполнить
#               sessiondiap[user_id]['znak'] и  sessiondiap[user_id]['itis']
#
def get_User_question(user_id, sss):
    sp_not = ['не хочу', 'надоело', 'отстань', 'позже', 'в другой раз', 'потом', 'выхо']
    s0 = ''
    sp = [ '<', 'меньше', '>', 'больше', '=', 'равно']
    mi = [ -1, -1, -1, -1, -1, -1]
    ni = -1

    # проверим если Пользователь отказывается от игры
    for i in sp_not:
        if i in sss:
            # Пользователь отказался от игры
            return('Хорошо.  Поиграем в другой раз...  Пока!')

    sessiondiap[user_id]['znak'] = ''
    # убираем из вопроса Пользователя все пробелы и знак ?
    for i in range(len(sss)):
        if sss[i] == ' ' or sss[i] == '?':
            pass
        else:
           s0 += sss[i]

    # проанализируем введенный вопрос

    # искать в ответе знаки сравнения и считать их кол-во в  n_find
    n_find = 0
    for i in range(len(sp)):
        pred = mi[i]
        mi[i] = s0.find(sp[i])
        if ( mi[i] > -1):
            if pred > -1:
                n_find += 1
            else:
                sessiondiap[user_id]['znak'] = sp[int(i/2)*2]
                mi[i] += len(sp[i])
                n_find += 1
                ni = i

    if n_find > 1:
        return('Нельзя использовать несколько условий в вопросе')

    n = 0
    if n_find == 0:  # в ответе не было знака, если ответ начинается с цифра, то считаем знак =
        if not s0[0].isdigit():
            return('В вопросе нет знака сравнения < или > или =')

        sessiondiap[user_id]['znak'] = '='
#        i = 0
#        for i in range(len(s0)):
#            if s0[i].isdigit():
#                break;
#        if not s0[i].isdigit():
#            return('В вопросе нет числа')
        # находим число
        i = 0
        while i < len(s0) and s0[i].isdigit():
            n = n * 10 + int(s0[i])
            i += 1

    elif n_find == 1:  # в вопросе нашли один знак сравнения
        i = mi[ni]
        # находим число
        while i < len(s0) and s0[i].isdigit():
            n = n * 10 + int(s0[i])
            i += 1
#        return(s0+'!ok!'+str(mi[ni])+ '_'+str(n))

    if n < 1 or   n > 100:
        return('число в вопросе выходит за установленные пределы от 1 до 100')
    else:
        sessiondiap[user_id]['itis'] = n
    return 'ok'


#=====================================================================
# получить ответ от пользователя -  больше или меньше число того что в вопросе Алисы
def get_otvet(user_id, st):

    st0 = st
    if st in  ['да' , 'конечно', 'немного', 'намного']:   # эти ответы считаются как ДА (больше)
        st0 = 'да'
    elif '>' in st or 'больше' in st:
        if sessiondiap[user_id]['znak'] == '>':
            st0 = 'да'
        else:
            st0 = 'нет'

    elif '<' in st or 'меньше' in st:       # ответы нет и меньше   считаются как нет (меньше)
        if sessiondiap[user_id]['znak'] == '<':
            st0 = 'да'
        else:
            st0 = 'нет'

    return st0

#===================================================================================================
# реализация алгоритма поиска числа методом половинного деления диапазона
#
def change_diap(user_id, st):
    if sessiondiap[user_id]['znak'] == '>' and st == 'да':
        sessiondiap[user_id]['start'] = sessiondiap[user_id]['itis'] + 1

    elif sessiondiap[user_id]['znak'] == '>' and st == 'нет':
        sessiondiap[user_id]['end'] = sessiondiap[user_id]['itis']

    elif sessiondiap[user_id]['znak'] == '<' and st == 'да':
        sessiondiap[user_id]['end'] = sessiondiap[user_id]['itis'] - 1

    elif sessiondiap[user_id]['znak'] == '<' and st == 'нет':
            sessiondiap[user_id]['start'] = sessiondiap[user_id]['itis']

    sessiondiap[user_id]['itis'] = int((sessiondiap[user_id]['end'] + sessiondiap[user_id]['start']) / 2)
    sessiondiap[user_id]['step'] = sessiondiap[user_id]['step'] + 1


#===========================================================================
# возврашает True, если число отгадоно   иначе - False
def find_chislo(user_id):
    if sessiondiap[user_id]['end'] - sessiondiap[user_id]['start'] <= 0:
        if sessiondiap[user_id]['znak'] == '>':
            sessiondiap[user_id]['tis'] = sessiondiap[user_id]['end']
        else:  # sessiondiap[user_id]['znak'] == '<':
            sessiondiap[user_id]['tis'] = sessiondiap[user_id]['start']
        return True
    else:
        return False


#===================================================================
# формируем подсказки Да\Нет
def get_yes_no(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    mas = [
        {'title': i, 'hide': True}
        for i in session['yes_no']
    ]
    return mas

#=========================================================

# Функция возвращает две подсказки для ответа.
def get_suggests(user_id, regim):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    if regim == 'загадай2':
        suggests = [
            {'title': suggest, 'hide': True}
            for suggest in session['suggests'][1:2]
        ]
    else:
        suggests = [
            {'title': suggest, 'hide': True}
            for suggest in session['suggests'][:2]
        ]

    # Убираем первую подсказку, чтобы подсказки менялись каждый раз.
#    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    return suggests


#==================================================================
# в последнем сообщении  ищем имя Пользователя
def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


#==================================================================
# Инициируем начало игры
# заполним словари стартовыми данными

def Init_start_game(user_id):

    # Запишем подсказки, которые мы  покажем Пользователю в первый раз
    sessionStorage[user_id] = {
        'suggests': [
            "Число загадано.",
            "Не хочу играть.",
            "Отстань!"
            ],
        'first_name': None,
        'yes_no' : [
            "Да",
            "Нет"
            ]
        }

    # создаём и заполняем словарь, диапазона чисел
    sessiondiap[user_id] = {
        'start':  1,        # начало диапазона
        'end':    100,      # конец диапазона
        'itis':   50,       # середина диапазона (end + start)\2
        'tis':    0,        # здесь число отгаданное Алисой или число, которое Алиса загадала
        'step':   0,        # номер хода (уточняющего вопроса) Алисы
        'stepI':  0,        # номер хода (уточняющего вопроса) Пользователя
        'znak':   '',       # знак в последнем заданном вопросе > или < или =
        'regim':  ''        # режим игры: начальное значение  '', затем по ходу игры меняется
                            # 'загадай' - пользователь загадывает число
                            # 'игра'    - Алиса  отгадывает число, задуманное Пользователем
                            # 'загадай2'- Алиса загадывает число
                            # 'игра2'   - Пользователь отгадывает число, задуманное Алисой
        }


#===========================================================================
# формируем случайным способом вопрос Алисы, для поиска числа в строке str0

def get_Alisa_question(user_id):
    sp = ['Задуманное число', 'Загаданное число', 'Твоё число', 'Число']

    # чтобы диалог был разнообразнее случайлым образом формируем вопрос в str0
    isp = random.randint(0, len(sp)-1)  # случайный выбор части вопроса
    zn = random.randint(0, 1)           # случайный выбор знака сравнения в вопроса

    put_name = random.randint(0, 1)
    if put_name == 1:  #перед вопросом вывести имя
        str0 = sessionStorage[user_id]['first_name'].title() + ', ' + sp[isp].lower()
    else:
        str0 = sp[isp]

    if sessiondiap[user_id]['end'] - sessiondiap[user_id]['start'] == 1:
        # когда для выбора осталось 2 числа
        zn = 0
        sessiondiap[user_id]['itis'] = sessiondiap[user_id]['end']
        sessiondiap[user_id]['znak'] = '<'
    if zn == 1:
        sessiondiap[user_id]['znak'] = '>'
        str0 = str0 + ' > ' + str(sessiondiap[user_id]['itis'])

    else:
        sessiondiap[user_id]['znak'] = '<'
        str0 = str0 + ' < ' + str(sessiondiap[user_id]['itis'])

    return(str0)


if __name__ == '__main__':
    app.run()