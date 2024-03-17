from flask import Flask, request, jsonify
import logging
import random


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1030494/9d09d09504ef81cfaf8e', '997614/6fa22eee0948054dedfa'],
    'нью-йорк': ['1521359/75528a1da67b15a2ec6e', '997614/7674c60b79a126f94a77'],
    'париж': ["1030494/95719c32b8859355ddfc", '965417/730876d325ce72b14876']
}

sessionStorage = {}

@app.route('/')
def index():
    return "Угадай город на Яндекс картах"


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

    handle_dialog(response, request.json)

    logging.info('Request: %r', response)

    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }

        return

    first_name = get_first_name(req)

    if sessionStorage[user_id]['first_name'] is None:

        if first_name is None:
            res['response']['text'] = 'Не раслышала имя. Повтори!'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            sessionStorage[user_id]['guessed_cities'] = []
            res['response']['text'] = 'Приятно познакомиться, ' + first_name.title() + '. Я Алиса. ' \
                                                                                       'Отгадаешь город по фото?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True

                },
                {
                    'title': 'Нет',
                    'hide': True

                }
            ]

    else:

        if not sessionStorage[user_id]['game_started']:

            if 'да' in req['request']['nlu']['tokens']:

                if len(sessionStorage[user_id]['guessed_cities']) == 3:

                    res['response']['text'] = 'Ты отгадал все города!'
                    res['end_session'] = True

                else:

                    sessionStorage[user_id]['game_started'] = True
                    sessionStorage[user_id]['attempt'] = 1
                    play_game(res, req)

            elif 'нет' in req['request']['nlu']['tokens']:
                res['response']['text'] = 'Ну и ладно!'
                res['end_session'] = True
            elif "Покажи город на карте" == req['request']['original_utterance']:
                res['response']['text'] = 'Показала. Сыграем еще? '
            else:
                res['response']['text'] = 'Не понял ответа! Так да или нет?'
                res['response']['buttons'] = [
                    {
                        'title': 'Да',
                        'hide': True

                    },
                    {
                        'title': 'Нет',
                        'hide': True

                    }
                ]

        else:

            play_game(res, req)


def play_game(res, req):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']

    if attempt == 1:

        city = list(cities.keys())[random.randint(0, 2)]

        while (city in sessionStorage[user_id]['guessed_cities']):
            city = list(cities.keys())[random.randint(0, 2)]

        sessionStorage[user_id]['city'] = city

        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Что это за город?'
        res['response']['card']['image_id'] = cities[city][attempt - 1]

    else:

        city = sessionStorage[user_id]['city']

        if get_city(req) == city:

            res['response']['text'] = 'Правильно! Сыграем еще?'

            res['response']['buttons'] = [
                {
                    "title": "Да",
                    "hide": True
                },
                {
                    "title": "Нет",
                    "hide": True
                },
                {
                    "title": "Покажи город на карте",
                    "url": "https://yandex.ru/maps/?mode=search&text=%s" % (city),
                    "hide": True
                }
            ]

            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = False
            return

        else:

            res['response']['text'] = 'Неправильно'
            if attempt == 3:
                res['response']['text'] = 'Вы пытались. Это ' + city.title() + '. Сыграем еще?'
                sessionStorage[user_id]['game_started'] = False
                sessionStorage[user_id]['guessed_cities'].append(city)
                return
            else:
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Неправильно. Вот тебе дополнительное фото'
                res['response']['card']['image_id'] = cities[city][attempt - 1]

    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:

        if entity['type'] == 'YANDEX.GEO':

            if 'city' in entity['value'].keys():
                return entity['value']['city']
            else:
                return None

    return None


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:

        if entity['type'] == 'YANDEX.FIO':

            if 'first_name' in entity['value'].keys():
                return entity['value']['first_name']
            else:
                return None
    return None


if __name__ == '__main__':
    app.run()
