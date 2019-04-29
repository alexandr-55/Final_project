# импортируем библиотеки
from flask import Flask, request
import logging
import random

import json

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

    # Отправляем request.json и response в функцию handle_dialog. Она сформирует оставшиеся поля JSON, которые отвечают
    # непосредственно за ведение диалога
    handle_dialog(request.json, response)

    logging.info('Response: %r', request.json)

    # Преобразовываем в JSON и возвращаем
    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.
        # Запишем подсказки, которые мы ему покажем в первый раз

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
        # создаём словарь, диапазона чисел
        sessiondiap[user_id] = {
            'start':  1,
            'end':    100,
            'tis':    0,
            'step':   0,
            'itis':   50,
            'znak':   '',
            'regim':  '0',
            'stepAlisa': 0,
            'stepI':   0
            }
        res['response']['text'] = 'Привет! Я - Алиса.  Назови свое имя.'
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь ещё не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = \
                'Не расслышала имя. Повтори, пожалуйста!'

        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться!     ' + first_name.title()\
                          + ',   загадай число от 1 до 100, а я попробую его отгадать.'
            sessiondiap[user_id]['regim'] = 'загадай' #111111111111111
            res['response']['buttons'] = get_suggests(user_id, sessiondiap[user_id]['regim'])

        return

    if sessiondiap[user_id]['regim'] == 'загадай':
        if 'загада' in req['request']['original_utterance'].lower():
            sessiondiap[user_id]['regim'] = 'игра'
            sessiondiap[user_id]['znak'] = '>'
            res['response']['text'] = 'Тогда начнем.    Задуманное число > %s ?' % (
                sessiondiap[user_id]['itis'])
            res['response']['buttons'] = get_yes_no(user_id)

        else:
            res['response']['text'] = 'Хорошо.  Поиграем в другой раз...  Пока!'
            res['response']['end_session'] = True
        return

    if sessiondiap[user_id]['regim'] == 'загадай2':
        res['response']['text'] = '%s, теперь твоя очередь отгадывать.  Я ЗАГАДАЛА ЧИСЛО!\
            Задавай мне вопросы, используя слова или знаки сравнения "<" или ">" или "="\
            (но не больше одного условия в вопросе)' % (
                sessionStorage[user_id]['first_name'].title())
        res['response']['buttons'] = get_suggests(user_id, sessiondiap[user_id]['regim'])
        sessiondiap[user_id]['tis'] = random.randint(1, 100)
        sessiondiap[user_id]['regim'] = 'игра2'
        return

    if sessiondiap[user_id]['regim'] == 'игра2':
        st = read_otvet3(user_id, req['request']['original_utterance'].lower())
        if st == 'ok':
#           случайным образом строим ответ: "на вопрос" или "на твой вопрос"
            sp_ask = ['На вопрос', 'На твой вопрос']
            isp = random.randint(0, len(sp_ask)-1)

            put_name = random.randint(0, 1)
            if put_name == 1:  #перед вопросом вывести имя
                str0 = sessionStorage[user_id]['first_name'].title() + ', ' + sp_ask[isp].lower()
            else:
                str0 = sp_ask[isp]

            sessiondiap[user_id]['stepI'] += 1
            if sessiondiap[user_id]['znak'] == '>':
                str_uslovie = '> ' + str(sessiondiap[user_id]['itis'])
                if sessiondiap[user_id]['tis'] > sessiondiap[user_id]['itis']:
                    res['response']['text'] = '%s "%s"?   Отвечаю -  ДА' % (
                        str0, str_uslovie)
                else:
                    res['response']['text'] = '%s "%s"?   Отвечаю -  НЕТ' % (
                        str0, str_uslovie)

            elif sessiondiap[user_id]['znak'] == '<':
                str_uslovie = '< ' + str(sessiondiap[user_id]['itis'])
                if sessiondiap[user_id]['tis'] < sessiondiap[user_id]['itis']:
                    res['response']['text'] = '%s "%s"?   Отвечаю -  ДА' % (
                        str0, str_uslovie)
                else:
                    res['response']['text'] = '%s "%s"?   Отвечаю -  НЕТ' % (
                        str0, str_uslovie)

            elif sessiondiap[user_id]['znak'] == '=':
                if sessiondiap[user_id]['tis'] == sessiondiap[user_id]['itis']:
                    if sessiondiap[user_id]['step'] == sessiondiap[user_id]['stepI']:
                        s_victoria = ' Итоги игры: НИЧЬЯ - число ходов одинаковое (по ' + str(sessiondiap[user_id]['step']) + ')'
                    elif sessiondiap[user_id]['step'] < sessiondiap[user_id]['stepI']:
                        s_victoria = ' Итоги игры: Победа АЛИСЫ (я потратила меньше ходов - ' + str(sessiondiap[user_id]['step']) + ')'
                    else:
                        s_victoria = ' Итоги игры: Твоя победа!!! (я потратила больше ходов - ' + str(sessiondiap[user_id]['step']) + ')'
                    res['response']['text'] = 'Верно,  я задумала число  %s.  Сделано ходов - %s. %s' % (
                        str(sessiondiap[user_id]['tis']), str(sessiondiap[user_id]['stepI']), s_victoria )
                else:
                    res['response']['text'] = '%s, к сожалению, ОШИБКА!  Я задумала число  %s.  Победила Алиса.  Игра окончена.' % (
                        sessionStorage[user_id]['first_name'].title(), str(sessiondiap[user_id]['tis']) )
                res['response']['end_session'] = True
        else:
            res['response']['text'] = 'Не поняла твой вопрос  "%s". Ошибка: %s.\
                Пожалуйста, спроси еще раз!' % (req['request']['original_utterance'], st)

#        res['response']['text'] = '%s, otvet = %' % (
#                sessionStorage[user_id]['first_name'].title(), req['request']['original_utterance'].lower())
#        res['response']['buttons'] = get_suggests(user_id, sessiondiap[user_id]['regim'])
        sessiondiap[user_id]['regim'] = 'игра2'
        return

    # сюда попадаем когда начата игра
    sp = ['Задуманное число', 'Загаданное число', 'Твоё число', 'Число']
    st = get_otvet(user_id, req['request']['original_utterance'].lower())
    if st == 'да' or st == 'нет':
        change_diap(user_id, st)
        if find_chislo(user_id):
            res['response']['text'] = '%s, я уже  знаю твое число!  Было задумано число = %s.\
            (мне потребовалось ходов = %s).  Продолжим?' % (
                sessionStorage[user_id]['first_name'].title(), sessiondiap[user_id]['tis'], sessiondiap[user_id]['step'])
            res['response']['buttons'] = get_yes_no(user_id)
            # для перехода в режим, когда пользователь отгадывает число regim = 'загадай2'
            sessiondiap[user_id]['regim'] = 'загадай2'
            return
        else:
            zn = random.randint(0, 1)
            isp = random.randint(0, len(sp)-1)

            put_name = random.randint(0, 1)
            if put_name == 1:  #перед вопросом вывести имя
                str0 = sessionStorage[user_id]['first_name'].title() + ', ' + sp[isp].lower()
            else:
                str0 = sp[isp]

            if sessiondiap[user_id]['end'] - sessiondiap[user_id]['start'] == 1:
                zn = 0
                sessiondiap[user_id]['itis'] = sessiondiap[user_id]['end']
                sessiondiap[user_id]['znak'] = '<'
            if zn == 1:
                res['response']['text'] = '%s > %s ?' % (
                str0, sessiondiap[user_id]['itis']) #, sessiondiap[user_id]['start'], sessiondiap[user_id]['end'])
 #               res['response']['text'] = '%s число  > %s?' % (
 #               sp[isp], sessiondiap[user_id]['itis'])
                sessiondiap[user_id]['znak'] = '>'
            else:
                res['response']['text'] = '%s  < %s  ?' % (
                str0, sessiondiap[user_id]['itis']) #, sessiondiap[user_id]['start'], sessiondiap[user_id]['end'])
#                res['response']['text'] = '%s число  < %s ?' % (
#                sp[isp], sessiondiap[user_id]['itis'])
                sessiondiap[user_id]['znak'] = '<'
            res['response']['buttons'] = get_yes_no(user_id)
#        req['request']['original_utterance'])
    else:
        res['response']['text'] = 'Не поняла твой ответ  "%s".  Пожалуйста, ответь еще раз!%s' % (
            req['request']['original_utterance'], sessiondiap[user_id]['regim'])
#    res['response']['buttons'] = get_suggests(user_id)


# по вопросу пользователя распознать число и знак сравнения >\<\=
def read_otvet3(user_id, sss):
    s0 = ''
    sp = [ '<', 'меньше', '>', 'больше', '=', 'равно']
    mi = [ -1, -1, -1, -1, -1, -1]
    ni = -1

    sessiondiap[user_id]['znak'] = ''
    for i in range(len(sss)):
        if sss[i] == ' ' or sss[i] == '?':
            pass
        else:
           s0 += sss[i]

    #искать в ответе знаки сравнения и считать их кол-во в  n_find
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
        return "Нельзя использовать несколько условий в вопросе"

    n = 0
    if n_find == 0:  # в ответе не было знака,если ответ начинается с цифра, то считаем знак =
        if not s0[0].isdigit():
            return("В вопросе нет знака сравнения < или > или =")

        sessiondiap[user_id]['znak'] = '='
#        i = 0
#        for i in range(len(s0)):
#            if s0[i].isdigit():
#                break;
#        if not s0[i].isdigit():
#            return 'В ответе нет числа'
        # находим число
        i = 0
        while i < len(s0) and s0[i].isdigit():
            n = n * 10 + int(s0[i])
            i += 1

    elif n_find == 1:
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

# реализация алгоритма поиска числа методом половинного деления диапазона
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


def find_chislo(user_id):
    if sessiondiap[user_id]['end'] - sessiondiap[user_id]['start'] <= 0:
        if sessiondiap[user_id]['znak'] == '>':
            sessiondiap[user_id]['tis'] = sessiondiap[user_id]['end']
        else:  # sessiondiap[user_id]['znak'] == '<':
            sessiondiap[user_id]['tis'] = sessiondiap[user_id]['start']
        return True
    else:
        return False



def get_yes_no(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    mas = [
        {'title': i, 'hide': True}
        for i in session['yes_no']
    ]

    return mas

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

    # Если осталась только одна подсказка, предлагаем подсказку
    # со ссылкой на Яндекс.Маркет.
    if len(suggests) < 2:
        suggests.append({
            "title": "Ладно",
            "url": "https://market.yandex.ru/search?text=слон",
            "hide": True
        })

    return suggests

def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)





if __name__ == '__main__':
    app.run()