

import telebot 
import webbrowser
from telebot import types
import sqlite3
from datetime import datetime
import os
import json

bot = telebot.TeleBot()
bot = telebot.TeleBot()

user_data = {}


TESTS_DIR = 'tests'
CURRENT_TEST_FILE = os.path.join(TESTS_DIR, 'current_test.json')


admin_states = {}

ADMIN_USER_IDS = [1892368075,706043482,980013497,337700107]



def ensure_tests_dir():
    """Создаёт директорию для тестов, если её нет."""
    os.makedirs(TESTS_DIR, exist_ok=True)


def load_questions_from_file(file_path):
    """
    Загружает тест из JSON-файла формата:
    {
        "title": "Название теста",
        "questions": [
            {
                "question": "Текст вопроса",
                "options": ["Вариант 1", "Вариант 2"],
                "correct_answers": [0, 1],
                "max_points": 1.0
            },
            ...
        ]
    }
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, dict) or 'questions' not in data:
        raise ValueError("Неверный формат файла теста: нужен объект с полем 'questions'")

    q_list = data['questions']
    if not isinstance(q_list, list) or not q_list:
        raise ValueError("В тесте должен быть непустой список 'questions'")

    
    for idx, q in enumerate(q_list, 1):
        if not isinstance(q, dict):
            raise ValueError(f"Вопрос #{idx} должен быть объектом")
        if 'question' not in q or 'options' not in q or 'correct_answers' not in q:
            raise ValueError(f"В вопросе #{idx} должны быть поля 'question', 'options', 'correct_answers'")
        if not isinstance(q['options'], list) or len(q['options']) == 0:
            raise ValueError(f"У вопроса #{idx} должен быть непустой список 'options'")
        if not isinstance(q['correct_answers'], list) or len(q['correct_answers']) == 0:
            raise ValueError(f"У вопроса #{idx} должен быть непустой список 'correct_answers'")
        if 'max_points' not in q:
            q['max_points'] = 1.0

    return data


def try_load_current_test():
    """Если есть сохранённый текущий тест – загружаем его в questions."""
    global questions
    ensure_tests_dir()
    if os.path.exists(CURRENT_TEST_FILE):
        try:
            data = load_questions_from_file(CURRENT_TEST_FILE)
            questions = data['questions']
            print(f"Загружен тест из {CURRENT_TEST_FILE}")
        except Exception as e:
            print(f"Не удалось загрузить текущий тест: {e}")


def list_available_tests():
    """Возвращает список доступных JSON-тестов в папке tests/."""
    ensure_tests_dir()
    return [f for f in os.listdir(TESTS_DIR) if f.endswith('.json')]

def init_database():
    connection = None
    try:
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
                score REAL,
                total_questions INTEGER,
                percentage REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        curr.execute('''
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_number INTEGER,
                user_answers TEXT,
                correct_answers TEXT,
                points_earned REAL,
                max_points REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        connection.commit()
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
    finally:
        if connection:
            connection.close()

def is_admin(user_id): 
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        print(f"Ошибка: Некорректный user_id: {user_id}")
        return False
    
    return user_id_int in ADMIN_USER_IDS

def save_user_answer(user_id, question_num, user_answers, correct_answers, points_earned, max_points):
    """Сохраняет ответ пользователя в базу данных"""
    try:
        connection = sqlite3.connect('base.sql')
        curr = connection.cursor()
        
        curr.execute('''
            INSERT INTO user_answers (user_id, question_number, user_answers, correct_answers, points_earned, max_points)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, question_num, '; '.join(user_answers), '; '.join(correct_answers), points_earned, max_points))
        
        connection.commit()
    except Exception as e:
        print(f"Ошибка при сохранении ответа: {e}")
    finally:
        if connection:
            connection.close()

@bot.message_handler(commands=['start'])
def start(message):
    init_database()
    try_load_current_test()

    user_id = message.from_user.id
    print(f"Пользователь {user_id} запустил бота")
    
    if user_id in user_data:
        del user_data[user_id]
        print(f"Данные пользователя {user_id} сброшены")
    
    if user_id in user_data:
        del user_data[user_id]
        print(f"Данные пользователя {user_id} сброшены")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Начать тест')
    
    admin_status = is_admin(user_id)
    
    if admin_status:
        btn3 = types.KeyboardButton('📊 Статистика')
        btn4 = types.KeyboardButton('📋 Все результаты')
        btn5 = types.KeyboardButton('🗑️ Очистить статистику')
        btn6 = types.KeyboardButton('📂 Управление тестами')
        markup.row(btn1)
        markup.row(btn3, btn4)
        markup.row(btn5, btn6)
        bot.send_message(message.chat.id, 'Привет, администратор! Добро пожаловать в тест-бот.', reply_markup=markup)
    else:
        markup.row(btn1)
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

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text
    
    print(f"Получено сообщение от {user_id}: {text}")
    
   
    if user_id in user_data and user_data[user_id].get('state') == 'choosing_test':
        tests = user_data[user_id].get('available_tests', [])

        if text == '⬅️ Назад в меню':
            user_data[user_id]['state'] = None
            start(message)
            return

        if text in tests:
            try:
                test_path = os.path.join(TESTS_DIR, text)
                data = load_questions_from_file(test_path)

                global questions
                questions = data['questions']

             
                with open(CURRENT_TEST_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                title = data.get('title', text)

                
                user_data[user_id].update({
                    'name': None,
                    'score': 0.0,
                    'current_question': 0,
                    'selected_answers': [],
                    'answers': [],
                    'in_test': False,
                    'state': None
                })

                msg = bot.send_message(
                    message.chat.id,
                    f"Вы выбрали тест: {title}\n\nТеперь введите ваше имя:"
                )
                bot.register_next_step_handler(msg, process_name)
                return
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Не удалось загрузить тест: {e}")
                user_data[user_id]['state'] = None
                start(message)
            return
        else:
            bot.send_message(
                message.chat.id,
                "Пожалуйста, выберите тест из списка или нажмите '⬅️ Назад в меню'."
            )
            return

    if user_id in user_data and user_data[user_id].get('in_test', False):
            handle_test_answer(message)
            return
    
    if text == 'Начать тест':
        tests = list_available_tests()
        if not tests:
            bot.send_message(
                message.chat.id,
                "📭 Доступных тестов не найдено. Обратитесь к администратору, чтобы загрузить тест."
            )
            return

        # Сбрасываем предыдущие данные пользователя и инициируем выбор теста
        user_data[user_id] = {
            'state': 'choosing_test',
            'available_tests': tests
        }

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for t in tests:
            markup.add(types.KeyboardButton(t))
        markup.add(types.KeyboardButton('⬅️ Назад в меню'))

        bot.send_message(
            message.chat.id,
            "Выберите тест, который хотите пройти:",
            reply_markup=markup
        )
    
    elif text == '📊 Статистика':
        if is_admin(user_id):
            show_statistics(message)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к просмотру статистики.")
            start(message)
    
    elif text == '📋 Все результаты':
        if is_admin(user_id):
            show_all_results(message)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к этой функции.")
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
    
    elif text == '📂 Управление тестами':
        if is_admin(user_id):
            ensure_tests_dir()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(types.KeyboardButton('📥 Загрузить тест'), types.KeyboardButton('🗑️ Удалить тест'))
            markup.row(types.KeyboardButton('📄 Список тестов'))
            markup.row(types.KeyboardButton('⬅️ Назад в меню'))
            bot.send_message(message.chat.id, "Управление тестами. Выберите действие:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к управлению тестами.")
            start(message)
    
    elif text == '📄 Список тестов':
        if is_admin(user_id):
            ensure_tests_dir()
            files = [f for f in os.listdir(TESTS_DIR) if f.endswith('.json')]
            if not files:
                bot.send_message(message.chat.id, "📭 Тесты не найдены. Загрузите новый тест в формате JSON.")
            else:
                msg = "📄 Доступные тесты (JSON-файлы):\n\n" + "\n".join(f"- {name}" for name in files)
                bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к управлению тестами.")
            start(message)
    
    elif text == '📥 Загрузить тест':
        if is_admin(user_id):
            ensure_tests_dir()
            admin_states[user_id] = 'upload_test'
            bot.send_message(
                message.chat.id,
                "📥 Отправьте JSON-файл с тестом.\n"
                "Формат:\n"
                "{\n"
                "  \"title\": \"Название теста\",\n"
                "  \"questions\": [\n"
                "    {\n"
                "      \"question\": \"Текст вопроса\",\n"
                "      \"options\": [\"Вариант 1\", \"Вариант 2\"],\n"
                "      \"correct_answers\": [0, 1],\n"
                "      \"max_points\": 1.0\n"
                "    }\n"
                "  ]\n"
                "}"
            )
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к загрузке тестов.")
            start(message)
    
    elif text == '🗑️ Удалить тест':
        if is_admin(user_id):
            ensure_tests_dir()
            admin_states[user_id] = 'delete_test'
            files = [f for f in os.listdir(TESTS_DIR) if f.endswith('.json')]
            files_list = "\n".join(files) if files else "тесты отсутствуют"
            bot.send_message(
                message.chat.id,
                f"🗑️ Введите имя JSON-файла теста для удаления (из папки '{TESTS_DIR}'):\n\n{files_list}"
            )
        else:
            bot.send_message(message.chat.id, "❌ У вас нет доступа к удалению тестов.")
            start(message)
    
    elif text == '⬅️ Назад в меню':
        start(message)
    
    else:
        # Обработка ввода имени файла для удаления теста
        if user_id in admin_states and admin_states[user_id] == 'delete_test' and is_admin(user_id):
            ensure_tests_dir()
            file_name = text.strip()
            file_path = os.path.join(TESTS_DIR, file_name)
            if not file_name.endswith('.json'):
                bot.send_message(message.chat.id, "❌ Укажите имя файла с расширением .json")
            elif not os.path.exists(file_path):
                bot.send_message(message.chat.id, f"❌ Файл '{file_name}' не найден в папке '{TESTS_DIR}'.")
            else:
                try:
                    os.remove(file_path)
                    bot.send_message(message.chat.id, f"✅ Тест '{file_name}' удалён.")
                except Exception as e:
                    bot.send_message(message.chat.id, f"❌ Не удалось удалить тест: {e}")
            admin_states[user_id] = None
        else:
            bot.send_message(message.chat.id, "Пожалуйста, выберите опцию из меню:")
            start(message)

def show_all_results(message):
    """Показывает все результаты тестирования"""
    try:
        connection = sqlite3.connect('base.sql')
        curr = connection.cursor()
        
    
        curr.execute('''
            SELECT name, score, total_questions, percentage, timestamp, user_id 
            FROM results 
            ORDER BY timestamp DESC
        ''')
        all_results = curr.fetchall()
        
        if not all_results:
            bot.send_message(message.chat.id, "📭 База данных пуста. Нет результатов тестирования.")
            start(message)
            return
        
        results_per_message = 20
        total_results = len(all_results)
        
        for i in range(0, total_results, results_per_message):
            batch = all_results[i:i + results_per_message]
            
            results_message = f"📋 ВСЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ\n\n"
            results_message += f"Всего участников: {total_results}\n\n"
            
            for idx, (name, score, total, percentage, timestamp, user_id) in enumerate(batch, i + 1):
                date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
                results_message += f"{idx}. {name} (ID: {user_id}): {score:.2f}/{total} ({percentage:.2f}%) - {date}\n"
            
    
            if total_results > results_per_message:
                current_page = (i // results_per_message) + 1
                total_pages = (total_results + results_per_message - 1) // results_per_message
                results_message += f"\nСтраница {current_page} из {total_pages}"
            
            bot.send_message(message.chat.id, results_message)
        

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📊 Общая статистика", callback_data="show_stats"))
        bot.send_message(message.chat.id, "Для просмотра общей статистики нажмите кнопку ниже:", reply_markup=markup)
        
    except Exception as e:
        print(f"Ошибка при получении всех результатов: {e}")
        bot.send_message(message.chat.id, f"❌ Ошибка при получении результатов: {str(e)}")
        start(message)
    finally:
        if connection:
            connection.close()

@bot.callback_query_handler(func=lambda call: call.data == "show_stats")
def handle_stats_callback(call):
    """Обработчик кнопки для показа статистики"""
    show_statistics(call.message)

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
        curr.execute('DELETE FROM user_answers')
        connection.commit()
        
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
    finally:
        if connection:
            connection.close()


@bot.message_handler(content_types=['document'])
def handle_test_document(message):
    """Обработка загрузки JSON-файла с тестом от администратора."""
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.send_message(message.chat.id, "❌ У вас нет прав для загрузки тестов.")
        return

    if admin_states.get(user_id) != 'upload_test':
    
        bot.send_message(message.chat.id, "Отправьте команду '📂 Управление тестами' → '📥 Загрузить тест' перед загрузкой файла.")
        return

    ensure_tests_dir()

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_name = message.document.file_name
        if not file_name.endswith('.json'):
            file_name += '.json'

        save_path = os.path.join(TESTS_DIR, file_name)

        with open(save_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        
        data = load_questions_from_file(save_path)

        global questions
        questions = data['questions']

       
        with open(CURRENT_TEST_FILE, 'w', encoding='utf-8') as f:
            __import__('json').dump(data, f, ensure_ascii=False, indent=2)

        title = data.get('title', file_name)
        bot.send_message(
            message.chat.id,
            f"✅ Тест '{title}' успешно загружен и установлен как текущий.\n"
            f"Всего вопросов: {len(questions)}"
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при загрузке теста: {e}")
    finally:
        admin_states[user_id] = None

def show_statistics(message):
    """Показывает общую статистику"""
    connection = None
    try:
        connection = sqlite3.connect('base.sql')
        curr = connection.cursor()
        
        curr.execute('SELECT COUNT(*) as total_users, AVG(score) as avg_score, MAX(score) as max_score FROM results')
        stats = curr.fetchone()
        
        curr.execute('SELECT name, score, total_questions, timestamp FROM results ORDER BY timestamp DESC LIMIT 10')
        recent_results = curr.fetchall()
        
        curr.execute('SELECT name, score, total_questions FROM results ORDER BY score DESC LIMIT 10')
        top_results = curr.fetchall()
        
        if not stats or not stats[0]: 
            bot.send_message(message.chat.id, "📭 База данных пуста. Нет результатов тестирования.")
            start(message)
            return
        
        total_users, avg_score, max_score = stats
        
        stats_message = f"""
📊 ОБЩАЯ СТАТИСТИКА ТЕСТА:

👥 Всего участников: {total_users}
📈 Средний балл: {round(avg_score, 2)} из {len(questions)}
🏆 Лучший результат: {max_score:.2f} из {len(questions)}

🏅 ТОП-10 результатов:
"""
        
        for i, (name, score, total) in enumerate(top_results, 1):
            stats_message += f"\n{i}. {name}: {score:.2f}/{total}"
        
        stats_message += "\n\n📋 Последние 10 результатов:"
        
        for i, (name, score, total, timestamp) in enumerate(recent_results, 1):
            date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
            stats_message += f"\n{i}. {name}: {score:.2f}/{total} ({date})"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📋 Все результаты", callback_data="all_results"))
        
        bot.send_message(message.chat.id, stats_message, reply_markup=markup)
        start(message)
        
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        bot.send_message(message.chat.id, f"❌ Ошибка при получении статистики: {str(e)}")
        start(message)
    finally:
        if connection:
            if connection:
                connection.close()

@bot.callback_query_handler(func=lambda call: call.data == "all_results")
def handle_all_results_callback(call):
   
    show_all_results(call.message)

def process_name(message):
    name = message.text.strip()
    user_id = message.from_user.id
    
    if not name:
        msg = bot.send_message(message.chat.id, "Имя не может быть пустым. Пожалуйста, введите ваше имя:")
        bot.register_next_step_handler(msg, process_name)
        return

    user_data[user_id] = {
        'name': name,
        'score': 0.0,
        'current_question': 0,
        'selected_answers': [],
        'answers': [],
        'in_test': True
    }
    
    ask_question(message.chat.id, user_id)

def ask_question(chat_id, user_id):
    current_question_index = user_data[user_id]['current_question']
    
    if current_question_index < len(questions):
        question_data = questions[current_question_index]
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

        buttons = []
        for option in question_data['options']:
            if option in user_data[user_id]['selected_answers']:
                buttons.append(types.KeyboardButton(f"✅ {option}"))
            else:
                buttons.append(types.KeyboardButton(option))
        

        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                markup.row(buttons[i], buttons[i + 1])
            else:
                markup.row(buttons[i])

        markup.row(types.KeyboardButton('💾 Сохранить ответ'))
        

        progress = f"Вопрос {current_question_index + 1}/{len(questions)}"
        
        selected_info = ""
        if user_data[user_id]['selected_answers']:
            selected_info = f"\n\n✅ Вы выбрали: {', '.join(user_data[user_id]['selected_answers'])}"
        
        message_text = f"{progress}\n\n{question_data['question']}{selected_info}"
        
        bot.send_message(chat_id, message_text, reply_markup=markup)
    else:
        finish_test(chat_id, user_id)

def handle_test_answer(message):
    user_id = message.from_user.id
    text = message.text

    if user_id not in user_data:
        bot.send_message(message.chat.id, "Пожалуйста, начните тест с помощью команды /start")
        start(message)
        return
    
    current_question_index = user_data[user_id]['current_question']

    if current_question_index >= len(questions):
        finish_test(message.chat.id, user_id)
        return
    
    question_data = questions[current_question_index]
    
    if text == '💾 Сохранить ответ':
        if not user_data[user_id]['selected_answers']:
            bot.send_message(message.chat.id, "❌ Пожалуйста, выберите хотя бы один ответ перед сохранением.")
            return
        
        # Определяем индексы выбранных пользователем ответов
        selected_indices = []
        for selected_text in user_data[user_id]['selected_answers']:
            clean_text = selected_text.replace("✅ ", "")
            if clean_text in question_data['options']:
                index = question_data['options'].index(clean_text)
                selected_indices.append(index)
        
        correct_indices = question_data['correct_answers']
        max_points = question_data['max_points']
        total_correct = len(correct_indices)
        
        selected_set = set(selected_indices)
        correct_set = set(correct_indices)
        
        # Количество правильно выбранных вариантов
        correct_selected_count = len(selected_set & correct_set)
        
        # Лишние (неверные) ответы, которых нет среди правильных
        wrong_selected_count = len(selected_set - correct_set)
        
        # Базовое правило начисления:
        # - если всего правильных ответов 2, а выбрали только один правильный -> 1 / 2 = 0.5
        # - если всего правильных ответов 3, а выбрали только один правильный -> 1 / 3 ≈ 0.33
        # Балл за вопрос всегда равен max_points (обычно 1), который делится
        # поровну между всеми правильными вариантами.
        if total_correct > 0:
            base_points = (correct_selected_count / total_correct) * max_points
        else:
            base_points = 0.0
        
        # Штраф за неверные варианты:
        # - каждый неверный вариант вычитает такую же "долю", как один правильный
        #   (max_points / total_correct)
        # Пример:
        #   всего правильных 2, выбрано 2 правильных и 1 неверный:
        #   base_points = 2/2 * 1 = 1
        #   penalty = 1 * (1/2) = 0.5
        #   итого points_earned = 0.5
        if total_correct > 0:
            penalty_per_wrong = max_points / total_correct
            penalty = wrong_selected_count * penalty_per_wrong
        else:
            penalty = 0.0
        
        points_earned = max(0.0, base_points - penalty)
        
        user_data[user_id]['score'] += points_earned
        
        selected_texts = [question_data['options'][i] for i in selected_indices]
        correct_texts = [question_data['options'][i] for i in correct_indices]
        
        save_user_answer(
            user_id,
            current_question_index + 1,
            selected_texts,
            correct_texts,
            points_earned,
            max_points
        )
        
        user_data[user_id]['answers'].append({
            'question': question_data['question'],
            'user_answers': selected_texts,
            'correct_answers': correct_texts,
            'points_earned': points_earned,
            'max_points': max_points
        })
        
        user_data[user_id]['selected_answers'] = []
        user_data[user_id]['current_question'] += 1
        
        if points_earned == max_points:
            bot.send_message(message.chat.id, f"✅ Отлично! Вы получили {points_earned:.2f} балла из {max_points}")
        elif points_earned > 0:
            bot.send_message(message.chat.id, f"⚠️ Частично верно! Вы получили {points_earned:.2f} балла из {max_points}")
        else:
            bot.send_message(message.chat.id, f"❌ Неверно! Вы получили 0 баллов из {max_points}")
        
        ask_question(message.chat.id, user_id)
    
    elif any(option in text for option in question_data['options']):
        clean_text = text.replace("✅ ", "")
        
        if clean_text in user_data[user_id]['selected_answers']:
            user_data[user_id]['selected_answers'].remove(clean_text)
            bot.send_message(message.chat.id, f"❌ Ответ '{clean_text}' удален из выбранных")
        else:
            user_data[user_id]['selected_answers'].append(clean_text)
            bot.send_message(message.chat.id, f"✅ Ответ '{clean_text}' добавлен")
        
        ask_question(message.chat.id, user_id)
    
    else:
        bot.send_message(
            message.chat.id,
            "Пожалуйста, выберите вариант ответа из предложенных или нажмите '💾 Сохранить ответ'."
        )

def finish_test(chat_id, user_id):
    if user_id not in user_data:
        bot.send_message(chat_id, "Тест не был начат. Используйте /start для начала теста.")
        start_by_chat_id(chat_id, user_id)
        return
        
    name = user_data[user_id]['name']
    score = user_data[user_id]['score']
    total_questions = len(questions)
    percentage = round((score/total_questions)*100, 2)
    
    score_details = f"""
📊 ДЕТАЛИ РЕЗУЛЬТАТА:

✅ Набрано баллов: {score:.2f} из {total_questions}
📈 Процент правильных ответов: {percentage:.2f}%

🎯 Ваш результат: {score:.2f} баллов из {total_questions} возможных
"""

    try:
        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else "Не указан"
        first_name = user_info.first_name if user_info.first_name else "Не указано"
        last_name = user_info.last_name if user_info.last_name else "Не указано"
    except:
        username = "Не указан"
        first_name = "Не указано"
        last_name = "Не указано"
    
    connection = None
    try:
        connection = sqlite3.connect('base.sql')
        curr = connection.cursor()
        curr.execute(
            '''INSERT INTO results 
            (user_id, username, first_name, last_name, name, score, total_questions, percentage) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, username, first_name, last_name, name, score, total_questions, percentage)
        )
        connection.commit()
    except Exception as e:
        print(f"Ошибка при сохранении результата: {e}")
    finally:
        if connection:
            connection.close()
    
    result_message = f"""
🎉 Тест завершен!

👤 Имя: {name}
{score_details}
{'🎯 Отличный результат! 🏆' if score >= total_questions * 0.8 else '👍 Хороший результат!' if score >= total_questions * 0.6 else '💪 Нужно тренироваться!'}

Хотите пройти тест еще раз?
"""
    
    bot.send_message(chat_id, result_message)
    
    if user_id in user_data:
        del user_data[user_id]

    start_by_chat_id(chat_id, user_id)

def start_by_chat_id(chat_id, user_id):
    if user_id in user_data:
        del user_data[user_id]
        print(f"Данные пользователя {user_id} сброшены в start_by_chat_id")
    
    if user_id in user_data:
        del user_data[user_id]
        print(f"Данные пользователя {user_id} сброшены в start_by_chat_id")
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Начать тест')
    
    admin_status = is_admin(user_id)
    
    if admin_status:
        btn3 = types.KeyboardButton('📊 Статистика')
        btn4 = types.KeyboardButton('📋 Все результаты')
        btn5 = types.KeyboardButton('🗑️ Очистить статистику')
        btn6 = types.KeyboardButton('📂 Управление тестами')
        markup.row(btn1)
        markup.row(btn3, btn4)
        markup.row(btn5, btn6)
        bot.send_message(chat_id, 'Главное меню:', reply_markup=markup)
    else:
        markup.row(btn1)
        bot.send_message(chat_id, 'Главное меню:', reply_markup=markup)

if __name__ == "__main__":
    print("Бот запущен...")
    print(f"Текущие администраторы: {ADMIN_USER_IDS}")
    print("Используйте команду /myid в боте, чтобы узнать свой ID")
    bot.infinity_polling()
