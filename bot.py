from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import google.generativeai as genai
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging
import random
import datetime
import re


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

user_sessions = {}
MAX_HISTORY = 15
load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-pro')


horoscope_cache = {
    'date': None,
    'horoscope': {}

}

ZODIAC_SIGNS = {
    'овен': {
        'emoji': '♈',
        'sources': [
            'https://horo.mail.ru/prediction/aries/today/',
            'https://horoscopes.rambler.ru/aries/',
            'https://ignio.com/r/export/utf/xml/daily/aries.xml'
        ]
    },
    'телец': {
        'emoji': '♉', 
        'sources': [
            'https://horo.mail.ru/prediction/taurus/today/',
            'https://horoscopes.rambler.ru/taurus/',
            'https://ignio.com/r/export/utf/xml/daily/taurus.xml'
        ]
    },
    'близнецы': {
        'emoji': '♊',
        'sources': [
            'https://horo.mail.ru/prediction/gemini/today/',
            'https://horoscopes.rambler.ru/gemini/',
            'https://ignio.com/r/export/utf/xml/daily/gemini.xml'
        ]
    },
    'рак': {
        'emoji': '♋',
        'sources': [
            'https://horo.mail.ru/prediction/cancer/today/',
            'https://horoscopes.rambler.ru/cancer/',
            'https://ignio.com/r/export/utf/xml/daily/cancer.xml'
        ]
    },
    'лев': {
        'emoji': '♌',
        'sources': [
            'https://horo.mail.ru/prediction/leo/today/',
            'https://horoscopes.rambler.ru/leo/',
            'https://ignio.com/r/export/utf/xml/daily/leo.xml'
        ]
    },
    'дева': {
        'emoji': '♍',
        'sources': [
            'https://horo.mail.ru/prediction/virgo/today/',
            'https://horoscopes.rambler.ru/virgo/',
            'https://ignio.com/r/export/utf/xml/daily/virgo.xml'
        ]
    },
    'весы': {
        'emoji': '♎',
        'sources': [
            'https://horo.mail.ru/prediction/libra/today/',
            'https://horoscopes.rambler.ru/libra/',
            'https://ignio.com/r/export/utf/xml/daily/libra.xml'
        ]
    },
    'скорпион': {
        'emoji': '♏',
        'sources': [
            'https://horo.mail.ru/prediction/scorpio/today/',
            'https://horoscopes.rambler.ru/scorpio/',
            'https://ignio.com/r/export/utf/xml/daily/scorpio.xml'
        ]
    },
    'стрелец': {
        'emoji': '♐',
        'sources': [
            'https://horo.mail.ru/prediction/sagittarius/today/',
            'https://horoscopes.rambler.ru/sagittarius/',
            'https://ignio.com/r/export/utf/xml/daily/sagittarius.xml'
        ]
    },
    'козерог': {
        'emoji': '♑',
        'sources': [
            'https://horo.mail.ru/prediction/capricorn/today/',
            'https://horoscopes.rambler.ru/capricorn/',
            'https://ignio.com/r/export/utf/xml/daily/capricorn.xml'
        ]
    },
    'водолей': {
        'emoji': '♒',
        'sources': [
            'https://horo.mail.ru/prediction/aquarius/today/',
            'https://horoscopes.rambler.ru/aquarius/',
            'https://ignio.com/r/export/utf/xml/daily/aquarius.xml'
        ]
    },
    'рыбы': {
        'emoji': '♓',
        'sources': [
            'https://horo.mail.ru/prediction/pisces/today/',
            'https://horoscopes.rambler.ru/pisces/',
            'https://ignio.com/r/export/utf/xml/daily/pisces.xml'
        ]
    }
}

BACKUP_HOROSCOPES = {
    'овен': "Сегодня звезды советуют Овнам проявить инициативу. Отличный день для новых начинаний!",
    'телец': "Тельцам сегодня стоит сосредоточиться на финансовых вопросах. Будьте практичны и рассудительны.",
    'близнецы': "Близнецов ждет день общения и новых знакомств. Не бойтесь проявлять любопытство!",
    'рак': "Ракам сегодня важно уделить время семье и домашним делам. Создайте уютную атмосферу.",
    'лев': "Львов ждет внимание окружающих. Используйте этот день для творчества и самовыражения.",
    'дева': "Девам стоит сосредоточиться на работе и планах. Организованность принесет успех.",
    'весы': "Весам сегодня важны гармония и баланс. Решайте конфликты дипломатично.",
    'скорпион': "Скорпионов ждут интригующие события. Доверяйте своей интуиции.",
    'стрелец': "Стрельцов ждут приключения. Открывайтесь новым возможностям!",
    'козерог': "Козерогам стоит проявить амбиции. Работа над долгосрочными целями принесет плоды.",
    'водолей': "Водолеев ждут неожиданные идеи. Делитесь своими мыслями с окружающими.",
    'рыбы': "Рыбам сегодня важно прислушаться к внутреннему голосу. Творчество и мечты на первом плане."
}


TAROT_CARDS = {
    "Шут": {"meaning": "Начало чего-то нового. Не бойся рисковать!", "image": "🃏"},
    "Маг": {"meaning": "У тебя есть все необходимое для успеха. Действуй!", "image": "🪄"},
    "Верховная Жрица": {"meaning": "Доверяй своей интуиции. Твой внутренний голос знает ответ.", "image": "🌙"},
    "Императрица": {"meaning": "Плодородие и изобилие. Твои усилия принесут результаты.", "image": "👑"},
    "Император": {"meaning": "Стабильность и контроль. Пора принимать важные решения.", "image": "⚜️"},
    "Иерофант": {"meaning": "Ищи мудрых советников. Обучение и традиции помогут тебе.", "image": "📖"},
    "Влюбленные": {"meaning": "Перед тобой важный выбор. Слушай свое сердце.", "image": "💑"},
    "Колесница": {"meaning": "Двигайся вперед к своей цели. Успех в путешествиях.", "image": "🛡️"},
    "Сила": {"meaning": "Ты сильнее, чем думаешь. Смелость победит любые страхи.", "image": "🦁"},
    "Отшельник": {"meaning": "Время для размышлений. Побыть одному - это хорошо.", "image": "🧙"},
    "Колесо Фортуны": {"meaning": "Удача на твоей стороне. Жди приятных сюрпризов.", "image": "🎡"},
    "Справедливость": {"meaning": "Все будет по справедливости. Правда восторжествует.", "image": "⚖️"},
    "Повешенный": {"meaning": "Взгляни на ситуацию по-новому. Иногда нужно просто отпустить.", "image": "🙃"},
    "Смерть": {"meaning": "Конец одного и начало другого. Перемены - это хорошо.", "image": "💀"},
    "Умеренность": {"meaning": "Соблюдай баланс во всем. Не торопись.", "image": "⚗️"},
    "Дьявол": {"meaning": "Осторожнее с вредными привычками. Не попадись в ловушку.", "image": "😈"},
    "Башня": {"meaning": "Неожиданные изменения. Старое должно уйти, чтобы пришло новое.", "image": "🏰"},
    "Звезда": {"meaning": "Надежда и вера в лучшее. Твои мечты сбудутся.", "image": "⭐"},
    "Луна": {"meaning": "Не все так, как кажется. Доверяй своим чувствам.", "image": "🌕"},
    "Солнце": {"meaning": "Радость и успех. Все будет хорошо!", "image": "☀️"},
    "Суд": {"meaning": "Время подвести итоги. Пришло время для новых начинаний.", "image": "👼"},
    "Мир": {"meaning": "Гармония и завершение. Ты на правильном пути.", "image": "🌍"}
}

def get_session():
    """Создаем сессию с правильными заголовками"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
    })
    return session

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🔮 Погадать")],
        [KeyboardButton("🎱 Гадание на шаре")],
        [KeyboardButton("🃏 Таро")],
        [KeyboardButton("♊ Гороскоп")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_tarot_keyboard():
    keyboard = [
        [KeyboardButton("1️⃣ Одна карта"), KeyboardButton("3️⃣ Три карты")],
        [KeyboardButton("↩️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def parse_horo_mail(url):
    """Парсинг horo.mail.ru"""
    try:
        session = get_session()
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        selectors = [
            '.article__text',
            '.p-prediction__text', 
            '.article__item__text',
            '.prediction__text',
            '[class*="article"]',
            '[class*="prediction"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if len(text) > 100 and any(word in text.lower() for word in ['сегодня', 'гороскоп', 'день', 'неделя']):
                    return re.sub(r'\s+', ' ', text)
        
        return None
    except Exception as e:
        logger.error(f"Ошибка парсинга horo.mail.ru: {e}")
        return None

def parse_rambler(url):
    try:
        session = get_session()
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        selectors = [
            '.mvh__description',
            '[data-cy="horoscope-description"]',
            '.xN_sL',
            '.h7qoQ',
            '[class*="description"]',
            '[class*="text"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if len(text) > 100:
                    return re.sub(r'\s+', ' ', text)
        
        return None
    except Exception as e:
        logger.error(f"Ошибка парсинга rambler.ru: {e}")
        return None

def parse_ignio(url):
    """Парсинг ignio.com (XML)"""
    try:
        session = get_session()
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            today_match = re.search(r'<today>(.*?)</today>', response.text, re.DOTALL)
            prediction_match = re.search(r'<prediction>(.*?)</prediction>', response.text, re.DOTALL)
            
            text = ""
            if today_match:
                text = today_match.group(1)
            elif prediction_match:
                text = prediction_match.group(1)
            
            if text:
                # Очищаем от XML тегов
                text = re.sub(r'<.*?>', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 50:
                    return text
        
        return None
    except Exception as e:
        logger.error(f"Ошибка парсинга ignio.com: {e}")
        return None

def parse_with_fallback(session, url, selectors, zodiac_sign):
    """Парсинг с несколькими попытками и разными методами"""
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Пробуем разные селекторы
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                text = element.get_text(strip=True)
                if len(text) > 100:  # Проверяем, что текст достаточно длинный
                    return re.sub(r'\s+', ' ', text)
        
        # Если селекторы не сработали
        possible_containers = soup.find_all(['div', 'section', 'article'], class_=True)
        for container in possible_containers:
            text = container.get_text(strip=True)
            if len(text) > 200 and any(word in text.lower() for word in ['гороскоп', 'прогноз', 'сегодня']):
                return re.sub(r'\s+', ' ', text)[:1000]  # Ограничиваем длину
        
        return None
    except Exception as e:
        logger.error(f"Ошибка при парсинге {url}: {e}")
        return None

def get_zodiac_keyboard():
    keyboard = []
    signs_list = list(ZODIAC_SIGNS.items())
    
    # Ряды по 3 кнопки
    for i in range(0, len(signs_list), 3):
        row = []
        for j in range(i, min(i+3, len(signs_list))):
            sign_name, sign_info = signs_list[j]
            # Короткие подписи
            button_text = f"{sign_info['emoji']} {sign_name.capitalize()}"
            row.append(KeyboardButton(button_text))
        keyboard.append(row)
    
    keyboard.append([KeyboardButton("↩️ Назад в меню")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_daily_horoscope(zodiac_sign):
    """Основная функция получения гороскопа"""
    try:
        # Проверяем валидность знака
        if zodiac_sign not in ZODIAC_SIGNS:
            logger.error(f"Неизвестный знак зодиака: {zodiac_sign}")
            return "Неизвестный знак зодиака"
        
        # Проверяем структуру данных
        sign_info = ZODIAC_SIGNS[zodiac_sign]
        if not isinstance(sign_info, dict) or 'sources' not in sign_info:
            logger.error(f"Неправильная структура данных для знака {zodiac_sign}")
            return "Ошибка конфигурации"
        
        # Проверяем кэш
        today = datetime.date.today()
        if horoscope_cache['date'] != today:
            horoscope_cache['date'] = today
            horoscope_cache['horoscopes'] = {}
        
        if zodiac_sign in horoscope_cache['horoscopes']:
            return horoscope_cache['horoscopes'][zodiac_sign]
        
        sources = sign_info['sources']
        horoscope_text = None
        
        logger.info(f"Пытаемся получить гороскоп для {zodiac_sign} из {len(sources)} источников")
        
        # Пробуем все источники по порядку
        for i, url in enumerate(sources):
            try:
                logger.info(f"Источник {i+1}: {url}")
                
                if 'horo.mail.ru' in url:
                    horoscope_text = parse_horo_mail(url)
                elif 'rambler.ru' in url:
                    horoscope_text = parse_rambler(url)
                elif 'ignio.com' in url:
                    horoscope_text = parse_ignio(url)
                
                if horoscope_text and len(horoscope_text) > 50:
                    logger.info(f"Успешно получили гороскоп с источника {i+1}")
                    # Сохраняем в кэш
                    horoscope_cache['horoscopes'][zodiac_sign] = horoscope_text
                    return horoscope_text
                    
            except Exception as e:
                logger.warning(f"Ошибка с источником {i+1}: {e}")
                continue
        
        # Если все источники не сработали
        logger.error("Все источники недоступны, возвращаем заглушку")
        return "К сожалению, не удалось получить актуальный гороскоп. Сайты могут быть временно недоступны. Попробуйте позже."
        
    except Exception as e:
        logger.error(f"Критическая ошибка в get_daily_horoscope: {e}")
        return "Произошла ошибка при получении гороскопа."

def check_site_availability():
    """Проверяем доступность сайтов перед парсингом"""
    session = get_session()
    test_urls = [
        'https://horo.mail.ru',
        'https://horoscopes.rambler.ru',
        'https://www.goroskop.ru'
    ]
    
    available_sites = []
    for url in test_urls:
        try:
            response = session.head(url, timeout=10)
            if response.status_code == 200:
                available_sites.append(url)
        except:
            continue
    
    return available_sites

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для диагностики парсинга"""
    available_sites = check_site_availability()
    message = f"Доступные сайты: {len(available_sites)} из 3\n"
    message += "\n".join(available_sites) if available_sites else "Все сайты недоступны"
    
    # Тестовый парсинг
    test_horoscope = get_daily_horoscope('овен')
    message += f"\n\nТестовый гороскоп: {len(test_horoscope)} символов"
    
    await update.message.reply_text(message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "Привет! Я бот-гадалка. 🔮\nВыбери, как хочешь погадать:"
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Доступные виды гаданий:\n"
        "🔮 Погадать - гадание с AI на любую тему\n"
        "🎱 Гадание на шаре - простой ответ да/нет\n"
        "🃏 Таро - гадание на картах Таро (1 или 3 карты)\n"
        "♊ Гороскоп - ежедневный гороскоп по знаку зодиака\n\n"
        "Просто выбери нужный вариант на клавиатуре!"
    )
    await update.message.reply_text(help_text)

def draw_tarot_cards(count=1):
    cards = random.sample(list(TAROT_CARDS.items()), count)
    return cards

def get_single_card_interpretation(card):
    name, info = card
    interpretations = [
        f"{info['image']} **{name}**\n\n{info['meaning']}\n\nЭта карта указывает на важные энергии в твоей жизни сейчас. Прислушайся к интуиции!",
        f"{info['image']} **{name}**\n\n{info['meaning']}\n\nАркан приносит тебе послание свыше. Задумайся над его значением.",
        f"{info['image']} **{name}**\n\n{info['meaning']}\n\nКарта показывает ключевую тему твоего нынешнего пути.",
        f"{info['image']} **{name}**\n\n{info['meaning']}\n\nЭтот аркан раскрывает тайны твоей судьбы в данный момент.",
        f"{info['image']} **{name}**\n\n{info['meaning']}\n\nМудрость карты поможет тебе найти верное направление."
    ]
    return random.choice(interpretations)

def get_three_cards_interpretation(cards):
    past, present, future = cards
    return (f"📜 **Расклад на три карты**\n\n"
            f"🕰 **Прошлое:** {past[1]['image']} {past[0]}\n{past[1]['meaning']}\n\n"
            f"⚡ **Настоящее:** {present[1]['image']} {present[0]}\n{present[1]['meaning']}\n\n"
            f"🔮 **Будущее:** {future[1]['image']} {future[0]}\n{future[1]['meaning']}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    logger.info(f"Обработка сообщения: {user_text}")

    if user_text in ["🔮 Погадать", "🎱 Гадание на шаре", "🃏 Таро", "♊ Гороскоп", "ℹ️ Помощь", "↩️ Назад"]:
        await handle_button(update, context)
        return
    
    # ТАРО
    if user_text in ["1️⃣ Одна карта", "3️⃣ Три карты"]:
        if user_text == "1️⃣ Одна карта":
            card = draw_tarot_cards(1)[0]
            interpretation = get_single_card_interpretation(card)
            await update.message.reply_text(interpretation, reply_markup=get_tarot_keyboard())
        else:
            cards = draw_tarot_cards(3)
            interpretation = get_three_cards_interpretation(cards)
            await update.message.reply_text(interpretation, reply_markup=get_tarot_keyboard())
        return
    
    # Гороскоп
    for sign_name, sign_info in ZODIAC_SIGNS.items():
        if isinstance(sign_info, dict) and 'emoji' in sign_info:
            if sign_info['emoji'] in user_text or sign_name in user_text.lower():
                # Отправляем сообщение о загрузке и сохраняем его
                loading_message = await update.message.reply_text(f"🔮 Получаю гороскоп для {sign_info['emoji']} {sign_name.capitalize()}...")
                
                # Получаем гороскоп
                horoscope = get_daily_horoscope(sign_name)
                message = f"{sign_info['emoji']} **Гороскоп для {sign_name.capitalize()} на сегодня**\n\n{horoscope}"
                
                # Редактируем сообщение о загрузке, заменяя его на гороскоп
                await loading_message.edit_text(message)
                
                # Отправляем клавиатуру отдельным сообщением
                await update.message.reply_text("Хочешь узнать гороскоп для другого знака?", reply_markup=get_zodiac_keyboard())
                return


    if not context.user_data.get('awaiting_topic'):
        await update.message.reply_text(
            "Пожалуйста, выберите действие на клавиатуре 👇",
            reply_markup=get_main_keyboard()
        )
        return

    # AI
    context.user_data.pop('awaiting_topic', None)
    
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    history = user_sessions[user_id]
    
    prompt = f"Сгенерируй загадочное и немного шутливое предсказание на тему: Всегда выдавай один большой вариант ответа(старайся давать ответы до 1000 символов, но использовать их все). И избегай таких предложений 'вот держи' и ему подобных. Выдавай пользователю сразу предсказание  {user_text}"
    
    user_message_for_history = {"role": "user", "parts": [prompt, user_text]}
    history.append(user_message_for_history)
    

    full_prompt = history[-MAX_HISTORY:]

    try:
        thinking_message = await update.message.reply_text("Думаю... 🔮")
        
        response = model.generate_content(full_prompt)
        bot_reply = response.text
        
        history.append({"role": "model", "parts": [bot_reply]})
        
        await thinking_message.delete()
        await update.message.reply_text(bot_reply)
        
    except Exception as e:
        logger.error(f"Ошибка при работе с Gemini: {e}")
        await update.message.reply_text('Упс! Мои магические кристаллы затуманились...')

    if len(history) > MAX_HISTORY * 2:
        user_sessions[user_id] = history[-(MAX_HISTORY * 2):]

    await update.message.reply_text(
        "Хочешь погадать еще?",
        reply_markup=get_main_keyboard()
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id
    logger.info(f"Обработка кнопки: {user_text}")

    context.user_data.pop('awaiting_topic', None)

    if user_text == "🔮 Погадать":
        context.user_data['awaiting_topic'] = True
        await update.message.reply_text(
            "О чем ты хочешь погадать? Напиши мне свою тему, например: 'любовь', 'работа', 'деньги' ✨"
        )

    elif user_text == "🎱 Гадание на шаре":
        answers = [
            "Знаки говорят — да! ✅",
            "Мои кристаллы показывают — нет ❌",
            "Шансы невелики... но все возможно 🌙",
            "Определенно да! 🌟",
            "Лучше не стоит 🚫",
            "Да, но будь осторожен ⚠️",
            "Нет, и это к лучшему 💫"
        ]
        answer = random.choice(answers)
        await update.message.reply_text(f"🎱 {answer}")

    elif user_text == "🃏 Таро":
        await update.message.reply_text(
            "Выбери, сколько карт Таро хочешь вытянуть:",
            reply_markup=get_tarot_keyboard()
        )

    elif user_text == "♊ Гороскоп":
        await update.message.reply_text(
            "Выбери свой знак зодиака:",
            reply_markup=get_zodiac_keyboard()
        )

    elif user_text == "↩️ Назад":
        await update.message.reply_text(
            "Возвращаюсь в главное меню:",
            reply_markup=get_main_keyboard()
        )

    elif user_text == "ℹ️ Помощь":
        help_text = (
            "Я могу:\n"
            "🔮 Погадать - гадание на любую тему\n"
            "🎱 Гадание на шаре - простой ответ да/нет\n"
            "🃏 Таро - гадание на картах Таро (1 или 3 карты)\n"
            "♊ Гороскоп - ежедневный гороскоп по знаку зодиака\n\n"
            "Просто выбери нужный вариант на клавиатуре!"
        )
        await update.message.reply_text(help_text)

def main():
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("debug", debug_command))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == "__main__":
    main()