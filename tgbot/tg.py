
import telebot 
import webbrowser
from telebot import types
import sqlite3
from datetime import datetime
import os

bot = telebot.TeleBot()

user_data = {}

ADMIN_USER_IDS = [1892368075,706043482,980013497]


questions = [
    {"question": "Вопрос 1: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 0},
    {"question": "Вопрос 2: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 2},
    {"question": "Вопрос 3: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 3},
    {"question": "Вопрос 4: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 1},
    {"question": "Вопрос 5: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 3},
    {"question": "Вопрос 6: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 2},
    {"question": "Вопрос 7: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 0},
    {"question": "Вопрос 8: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 3},
    {"question": "Вопрос 9: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 2},
    {"question": "Вопрос 10: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 2},
    {"question": "Вопрос 11: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 1},
    {"question": "Вопрос 12: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 0},
    {"question": "Вопрос 13: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 3},
    {"question": "Вопрос 14: Сосал?", "options": ["Да", "Да", "Да", "Да"], "correct": 1},
    {"question": "Вопрос 15: Сколько?", "options": ["5", "10", "15", "20"], "correct": 0}
]

def init_database():
    connection = sqlite3.connect('base.sql')
    curr = connection.cursor()
    
  
    curr.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            name TEXT,
            score INTEGER,
            total_questions INTEGER,
            percentage REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    connection.commit()
    curr.close()
    connection.close()

def is_admin(user_id): 
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        print(f"Ошибка: Некорректный user_id: {user_id}")
        return False
    
    is_admin_result = user_id_int in ADMIN_USER_IDS

    print(f"Отладка is_admin:")
    print(f"  user_id: {user_id} (тип: {type(user_id)})")
    print(f"  user_id_int: {user_id_int} (тип: {type(user_id_int)})")
    print(f"  ADMIN_USER_IDS: {ADMIN_USER_IDS}")
    print(f"  Результат: {is_admin_result}")
    
    return is_admin_result

@bot.message_handler(commands=['start'])
def start(message):
    init_database()

    user_id = message.from_user.id
    print(f"Пользователь {user_id} запустил бота")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Начать тест')
    btn2 = types.KeyboardButton('Информация о проекте')
    
    admin_status = is_admin(user_id)
    print(f"Статус администратора для {user_id}: {admin_status}")
    
    if admin_status:
        btn3 = types.KeyboardButton('📊 Статистика')
        btn4 = types.KeyboardButton('🗑️ Очистить статистику')
        markup.row(btn1, btn2)
        markup.row(btn3, btn4)
        bot.send_message(message.chat.id, 'Привет, администратор! Добро пожаловать в тест-бот.', reply_markup=markup)
    else:
        markup.row(btn1, btn2)
        bot.send_message(message.chat.id, 'Привет! Добро пожаловать в тест-бот.', reply_markup=markup)

@bot.message_handler(commands=['myid'])
def show_my_id(message):

    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    
    info_message = f"""
Ваша информация:
ID: {user_id}
Имя: {first_name}
Фамилия: {last_name if last_name else 'не указана'}
Username: @{username if username else 'не указан'}

Текущие администраторы: {ADMIN_USER_IDS}
"""
    bot.send_message(message.chat.id, info_message)

@bot.message_handler(commands=['debug_admin'])
def debug_admin(message):
    user_id = message.from_user.id
    admin_status = is_admin(user_id)
    
    debug_message = f"""
Отладочная информация:
Ваш ID: {user_id}
Тип ID: {type(user_id)}
Список администраторов: {ADMIN_USER_IDS}
Вы администратор: {admin_status}
"""
    bot.send_message(message.chat.id, debug_message)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text
    
    print(f"Получено сообщение от {user_id}: {text}")
    
    if user_id in user_data and user_data[user_id].get('in_test', False):
        if user_data[user_id]['current_question'] >= len(questions):
            finish_test(message.chat.id, user_id)
            return
        else:
            handle_test_answer(message)
            return
    
    if text == 'Начать тест':
        msg = bot.send_message(message.chat.id, 'Перед началом теста, пожалуйста, введите ваше имя:')
        bot.register_next_step_handler(msg, process_name)
    
    elif text == 'Информация о проекте':
        markup = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton("Открыть сайт", url="https://pytba.readthedocs.io/ru/latest/")
        markup.add(url_button)
        bot.send_message(
            message.chat.id,
            'Сайт открывается... Нажмите кнопку ниже:',
            reply_markup=markup
        )
        start(message)
    
    elif text == '📊 Статистика':

        if is_admin(user_id):
            show_statistics(message)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к просмотру статистики.")
            start(message)
    
    elif text == '🗑️ Очистить статистику':
        if is_admin(user_id):
            confirm_clear_statistics(message)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к этой функции.")
            start(message)
    
    elif text == '✅ Да, очистить статистику':
        if is_admin(user_id):
            clear_statistics(message)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к этой функции.")
            start(message)
    
    elif text == '❌ Нет, отменить':
        bot.send_message(message.chat.id, "Очистка статистики отменена.")
        start(message)
    
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите опцию из меню:")
        start(message)

def confirm_clear_statistics(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('✅ Да, очистить статистику'))
    markup.add(types.KeyboardButton('❌ Нет, отменить'))
    
    bot.send_message(
        message.chat.id,
        "⚠️ ВНИМАНИЕ! Вы собираетесь удалить ВСЮ статистику тестирования.\n\n"
        "Это действие невозможно отменить. Все данные будут утеряны.\n\n"
        "Вы уверены, что хотите очистить статистику?",
        reply_markup=markup  
    )

def clear_statistics(message):
    try:
        connection = sqlite3.connect('base.sql')
        curr = connection.cursor()
        
    
        curr.execute('SELECT COUNT(*) FROM results')
        count_before = curr.fetchone()[0]
        
    
        curr.execute('DELETE FROM results')
        connection.commit()
        
        curr.close()
        connection.close()
        
        bot.send_message(
            message.chat.id,
            f"✅ Статистика успешно очищена!\n\n"
            f"Удалено записей: {count_before}\n\n"
            f"Все данные тестирования были удалены из базы данных."
        )
        
        start(message)
        
    except Exception as e:
        print(f"Ошибка при очистке статистики: {e}")
        bot.send_message(
            message.chat.id,
            f"❌ Произошла ошибка при очистке статистики:\n{str(e)}"
        )
        start(message)  

def show_statistics(message):
    connection = sqlite3.connect('base.sql')
    curr = connection.cursor()
    
    # 
    curr.execute('SELECT COUNT(*) as total_users, AVG(score) as avg_score, MAX(score) as max_score FROM results')
    stats = curr.fetchone()
    
    
    curr.execute('SELECT name, score, total_questions, timestamp FROM results ORDER BY timestamp DESC LIMIT 10')
    recent_results = curr.fetchall()
    

    curr.execute('SELECT name, score, total_questions FROM results ORDER BY score DESC LIMIT 5')
    top_results = curr.fetchall()
    
    curr.close()
    connection.close()
    
    if not stats or not stats[0]: 
        bot.send_message(message.chat.id, "📭 База данных пуста. Нет результатов тестирования.")
        start(message)
        return
    
    total_users, avg_score, max_score = stats
    
    stats_message = f"""
📊 ОБЩАЯ СТАТИСТИКА ТЕСТА:

👥 Всего участников: {total_users}
📈 Средний балл: {round(avg_score, 1)} из {len(questions)}
🏆 Лучший результат: {max_score} из {len(questions)}

🏅 ТОП-5 результатов:
"""
    
    for i, (name, score, total) in enumerate(top_results, 1):
        stats_message += f"\n{i}. {name}: {score}/{total}"
    
    stats_message += "\n\n📋 Последние результаты:"
    
    for i, (name, score, total, timestamp) in enumerate(recent_results, 1):
        date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
        stats_message += f"\n{i}. {name}: {score}/{total} ({date})"
    
    bot.send_message(message.chat.id, stats_message)
    start(message)

def process_name(message):
    name = message.text.strip()
    user_id = message.from_user.id
    

    user_data[user_id] = {
        'name': name,
        'score': 0,
        'current_question': 0,
        'answers': [],
        'in_test': True
    }
    
    ask_question(message.chat.id, user_id)

def ask_question(chat_id, user_id):
    current_question_index = user_data[user_id]['current_question']
    
    if current_question_index < len(questions):
        question_data = questions[current_question_index]
        

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for option in question_data['options']:
            markup.add(types.KeyboardButton(option))
        
        bot.send_message(
            chat_id, 
            question_data['question'], 
            reply_markup=markup
        )
    else:

        finish_test(chat_id, user_id)

def handle_test_answer(message):
    user_id = message.from_user.id
    

    if user_id not in user_data:
        bot.send_message(message.chat.id, "Пожалуйста, начните тест с помощью команды /start")
        start(message)
        return
    
    current_question_index = user_data[user_id]['current_question']
    

    if current_question_index >= len(questions):
        finish_test(message.chat.id, user_id)
        return
    
    question_data = questions[current_question_index]
    user_answer = message.text
    

    if user_answer == question_data['options'][question_data['correct']]:
        user_data[user_id]['score'] += 1
    

    user_data[user_id]['answers'].append({
        'question': question_data['question'],
        'user_answer': user_answer,
        'correct_answer': question_data['options'][question_data['correct']]
    })
    user_data[user_id]['current_question'] += 1
    ask_question(message.chat.id, user_id)

def finish_test(chat_id, user_id):

    if user_id not in user_data:
        bot.send_message(chat_id, "Тест не был начат. Используйте /start для начала теста.")
        start_by_chat_id(chat_id, user_id)
        return
        
    name = user_data[user_id]['name']
    score = user_data[user_id]['score']
    total_questions = len(questions)
    percentage = round((score/total_questions)*100, 2)
    

    try:
        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else "Не указан"
        first_name = user_info.first_name if user_info.first_name else "Не указано"
        last_name = user_info.last_name if user_info.last_name else "Не указано"
    except:
        username = "Не указан"
        first_name = "Не указано"
        last_name = "Не указано"
    

    connection = sqlite3.connect('base.sql')
    curr = connection.cursor()
    curr.execute(
        '''INSERT INTO results 
        (user_id, username, first_name, last_name, name, score, total_questions, percentage) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, username, first_name, last_name, name, score, total_questions, percentage)
    )
    connection.commit()
    curr.close()
    connection.close()
    
    result_message = f"""
🎉 Тест завершен!

👤 Имя: {name}
📊 Результат: {score} из {total_questions}
📈 Процент правильных ответов: {percentage}%

{'🎯 Отличный результат!' if score >= 12 else '👍 Хороший результат!' if score >= 8 else '💪 Есть над чем поработать!'}

Хотите пройти тест еще раз?
"""
    
    bot.send_message(chat_id, result_message)
    
    if user_id in user_data:
        del user_data[user_id]
    

    start_by_chat_id(chat_id, user_id)

def start_by_chat_id(chat_id, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Начать тест')
    btn2 = types.KeyboardButton('Информация о проекте')
    
    admin_status = is_admin(user_id)
    
    if admin_status:
        btn3 = types.KeyboardButton('📊 Статистика')
        btn4 = types.KeyboardButton('🗑️ Очистить статистику')
        markup.row(btn1, btn2)
        markup.row(btn3, btn4)
        bot.send_message(chat_id, 'Главное меню:', reply_markup=markup)
    else:
        markup.row(btn1, btn2)
        bot.send_message(chat_id, 'Главное меню:', reply_markup=markup)

if __name__ == "__main__":
    print("Бот запущен...")
    print(f"Текущие администраторы: {ADMIN_USER_IDS}")
    print("Используйте команду /myid в боте, чтобы узнать свой ID")
    print("Используйте команду /debug_admin для отладки проверки администратора")
    bot.infinity_polling()
