import os
import requests
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

updater = Updater(token=os.getenv('BOT_TOKEN'), use_context=True)

dispatcher = updater.dispatcher

MAIN_COMMANDS = [['Рейтинг по домашкам', 'Общий рейтинг']]


def send(bot, chat_id, text, keyboard=None):
    reply_markup = None
    if keyboard:
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        )

    bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


def start_action(update, context):
    send(context.bot, update.effective_chat.id, "Привет, жду указаний!", MAIN_COMMANDS)


def get_homework(num):
    response = requests.get('https://metabase.foxford.ru/api/public/card/'
                            'e6dd6e4d-0a6b-429b-9f0a-e84c4d33106b/query/json?'
                            'parameters=[{"type":"category","target":["variable",'
                            f'["template-tag","lesson_number"]],"value":"{num}"'
                            '},{"type":"category","target":["variable",["template-tag",'
                            '"course_id"]],"value":"2393"}]')
    return response.json()


def get_homeworks_nums():
    homeworks = []

    for num in range(1, 31):
        data = get_homework(num)
        if len(data) > 0:
            homeworks.append(num)

    return homeworks


def get_results_from_homework(hw):
    results = []
    for task in hw:
        if task.get('to_char') == 'Итого':
            name = ' '.join(task.get('user+email').split()[:-1])
            results.append((name, task.get('rel_point')))
    return results


def list2bi_list(data):
    new_data = []
    for n in range(0, len(data), 2):
        new_data.append(data[n: n + 2])
    return new_data


def send_results(bot, chat_id, results):
    results = list(filter(lambda x: x[1] > 0, results))
    results.sort(key=lambda x: x[1], reverse=True)
    send(bot, chat_id,
         '\n'.join(map(lambda x: str(round(x[1], 2)) + ' ' + x[0], results)), MAIN_COMMANDS)


def text_action(update, context):
    cmd = update.message.text.lower()
    if cmd == 'рейтинг по домашкам':
        homeworks = get_homeworks_nums()
        send(context.bot, update.effective_chat.id, 'Эти домашки уже открыты',
             keyboard=list2bi_list(list(map(lambda x: f'Домашка {x}', homeworks))))

    elif cmd == 'общий рейтинг':
        homeworks = get_homeworks_nums()
        total_results = {}
        for num in homeworks:
            hw = get_homework(num)
            results = get_results_from_homework(hw)
            for result in results:
                total_results[result[0]] = total_results.get(result[0], 0) + result[1]

        total_results_list = []
        for name, value in total_results.items():
            total_results_list.append((name, value))

        send_results(context.bot, update.effective_chat.id, total_results_list)

    elif cmd.startswith('домашка'):
        num = cmd.split()[-1]
        hw = get_homework(num)
        if not hw:
            send(context.bot, update.effective_chat.id, 'Нет еще такой домашки', MAIN_COMMANDS)
        else:
            results = get_results_from_homework(hw)
            send_results(context.bot, update.effective_chat.id, results)


start_handler = CommandHandler('start', start_action)
dispatcher.add_handler(start_handler)

text_handler = MessageHandler(Filters.text & (~Filters.command), text_action)
dispatcher.add_handler(text_handler)

updater.start_polling()
updater.idle()
