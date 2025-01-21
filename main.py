import logging, os, random, requests, nest_asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    JobQueue
)

# ID администратора, чтобы бот уведомлял вас о новых пользователях
ADMIN_ID = 843926334  # Замените на ваш Telegram ID

karma_score = {}
user_language = {}

# Папка для хранения сообщений
messages_folder = "messages"
os.makedirs(messages_folder, exist_ok=True)

# Функция для сохранения сообщения в файл
def save_message(user_id: int, username: str, message: str) -> None:
    # Используем user_id и username как имя файла для безопасности
    username_safe = username if username else "unknown_user"
    file_name = f"{user_id}_{username_safe}.txt"
    file_path = os.path.join(messages_folder, file_name)
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception as e:
        logger.error(f"Ошибка при сохранении сообщения пользователя {user_id}: {e}")


# Функция для получения случайного хадиса
def get_random_hadith():
    hadiths = {
        "ru": [
            "«Лучший из вас тот, кто учит Коран и учит ему других». (Бухари)",
            "«Деяния оцениваются по намерениям». (Муслим)"
        ],
        "ar": [
            "خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ (البخاري)",
            "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ (مسلم)"
        ]
    }
    return {lang: random.choice(hadiths[lang]) for lang in ["ru", "ar"]}


# Получение локации
async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    location = update.message.location
    user_logger.info(f"Пользователь {user.id} ({user.username}) отправил локацию: {location.latitude}, {location.longitude}")
    await update.message.reply_text("Спасибо за предоставление локации!")

# Получение контакта
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    contact = update.message.contact
    user_logger.info(f"Пользователь {user.id} ({user.username}) отправил контакт: {contact.phone_number}")
    await update.message.reply_text("Спасибо за предоставление контакта!")


# Функция установка языка
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    if query.data == "lang_ru":
        user_language[user.id] = "ru"
        await query.answer("Выбран русский язык.")
    elif query.data == "lang_ar":
        user_language[user.id] = "ar"
        await query.answer("تم اختيار اللغة العربية.")

    lang = user_language[user.id]
    user_logger.info(f"User {user.id} ({user.username}) selected language: {lang}.")

    messages = {
        "ru": "🤖 Добро пожаловать в Исламский Бот! 🤖\nНажмите на кнопки ниже для взаимодействия.",
        "ar": "🤖 مرحباً بك في البوت الإسلامي! 🤖\nاضغط على الأزرار أدناه للتفاعل.",
    }
    keyboard = [
        [InlineKeyboardButton("✅ Халяль / حلال", callback_data="halal")],
        [InlineKeyboardButton("❌ Харам / حرام", callback_data="haram")],
        [InlineKeyboardButton("📊 Очки Кармы / نقاط الكارما", callback_data="score")],
        [InlineKeyboardButton("📖 Аят и Хадис / آية وحديث", callback_data="daily")],
        [InlineKeyboardButton("🕋 Время Намаза / مواقيت الصلاة", callback_data="prayer_times")],
        [InlineKeyboardButton("🎲 Рандомное действие / عمل عشوائي", callback_data="random")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(messages[lang], reply_markup=reply_markup)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Настройка логирования пользователей
user_log_handler = logging.FileHandler("userlogs.txt")
user_log_handler.setLevel(logging.INFO)
user_log_formatter = logging.Formatter('%(asctime)s - %(message)s')
user_log_handler.setFormatter(user_log_formatter)
user_logger = logging.getLogger("user_logger")
user_logger.addHandler(user_log_handler)
user_logger.setLevel(logging.INFO)

# Логирование уникальных пользователей
unique_users_file = "uniqusers.txt"
unique_users = set()
try:
    with open(unique_users_file, "r") as f:
        unique_users = set(f.read().splitlines())
except FileNotFoundError:
    pass


# Сохранение уникальных пользователей в файл
def log_unique_user(user_id, username):
    username_safe = username if username else "unknown_user"
    user_entry = f"{user_id}_{username_safe}"

    if user_entry not in unique_users:
        unique_users.add(user_entry)
        try:
            with open(unique_users_file, "a", encoding="utf-8") as f:
                f.write(f"{user_entry}\n")
        except Exception as e:
            logger.error(f"Ошибка при сохранении уникального пользователя: {e}")

# Функция для обработки всех сообщений
async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    message = update.message.text

    # Получаем имя пользователя или устанавливаем "unknown_user", если имя отсутствует
    username = user.username if user.username else "unknown_user"

    # Сохраняем сообщение в файл
    save_message(user.id, username, message)
    logging.info(f"Сообщение от пользователя {user.id}: {message}")

    if not message:  # Пропуск пустых сообщений
        return "skibidi error"


# Переменные для хранения данных
halal_actions = {
    "ru": [
        "Помолитесь за кого-то.",
        "Пожертвуйте в местную благотворительную организацию.",
        "Поститесь день и размышляйте.",
        "Попейте воду Замзам.",
        "Помогите другу или члену семьи.",
        "Прочитайте главу из священной книги.",
        "Улыбнитесь незнакомцу.",
        "Позвоните родственнику, с которым давно не общались.",
        "Подарите что-то нуждающееся семье.",
        "Посадите дерево или ухаживайте за растением.",
        "Учите кого-то новому навыку.",
        "Совершите добрый поступок тайно.",
        "Уберите мусор в общественном месте.",
        "Подарите еду голодному человеку.",
        "Поддержите морально друга в трудной ситуации.",
        "Помогите пожилому человеку с покупками.",
    ],
    "ar": [
        "صلّي لأجل أحد.",
        "تبرّع لجمعية خيرية محلية.",
        "صُم ليوم وتأمل.",
        "اشرب ماء زمزم.",
        "ساعد صديقًا أو أحد أفراد العائلة.",
        "اقرأ فصلًا من كتاب مقدس.",
        "ابتسم لشخص غريب.",
        "اتصل بأحد الأقارب الذين لم تتحدث معهم منذ فترة.",
        "قدم شيئًا مفيدًا لعائلة محتاجة.",
        "ازرع شجرة أو اعتنِ بنبتة.",
        "علم شخصًا مهارة جديدة.",
        "قم بعمل خيري دون أن يعلم به أحد.",
        "نظف مكانًا عامًا من القمامة.",
        "أطعم شخصًا جائعًا.",
        "ادعم صديقًا معنويًا في وقت عصيب.",
        "ساعد شخصًا مسنًا في حمل أغراضه.",
    ],
}

haram_actions = {
    "ru": [
        "Съешьте бургер с беконом.",
        "Пропустите молитвы, чтобы смотреть Netflix.",
        "Танцуйте тренды из TikTok.",
        "Играйте в казино на свои сбережения.",
        "Пейте вино за ужином.",
        "Слушайте запретную музыку всю ночь.",
        "Покупайте дорогие вещи для тщеславия.",
        "Обманывайте людей в своих интересах.",
        "Смотрите неподобающие материалы.",
        "Сорьтесь с родителями.",
        "Пейте энергетики для развлечения.",
        "Злитесь и кричите на других без причины.",
        "Говорите неправду на работе или учебе.",
        "Распространяйте слухи о людях.",
        "Игнорируйте бедных и нуждающихся.",
        "Срывайте злость на животных.",
    ],
    "ar": [
        "تناول برجر مع لحم الخنزير.",
        "تخطَّ الصلوات لمشاهدة Netflix.",
        "ارقص على ترندات TikTok.",
        "اقمِر مدخراتك في الكازينو.",
        "اشرب النبيذ مع العشاء.",
        "استمع إلى الموسيقى المحرمة طوال الليل.",
        "اشترِ أشياء باهظة من أجل التفاخر.",
        "اخدع الآخرين لتحقيق مكاسب شخصية.",
        "شاهد مواد غير لائقة.",
        "تشاجر مع والديك.",
        "اشرب مشروبات الطاقة للتسلية.",
        "اغضب واصرخ في الآخرين بلا سبب.",
        "اكذب في العمل أو الدراسة.",
        "انشر الشائعات عن الآخرين.",
        "تجاهل الفقراء والمحتاجين.",
        "اسخط على الحيوانات بلا مبرر.",
    ],
}


    # Функция для получения времени намаза
def get_prayer_times(city):
    try:
        response = requests.get(f"https://api.aladhan.com/v1/timingsByCity", params={
        "city": city,
            "country": "",
            "method": 2
        })
        if response.status_code == 200:
            data = response.json()["data"]["timings"]
            return data
        else:
            return None
    except Exception:
        return None

# Функция для получения случайного аята
def get_random_ayat():
    ayats = {
        "ru": [
            "«Воистину, Аллах с терпеливыми». (Коран 2:153)",
            "«И поминайте Меня — и Я буду помнить вас». (Коран 2:152)"
        ],
        "ar": [
              "إِنَّ اللَّهَ مَعَ الصَّابِرِينَ (البقرة 153)",
              "فَاذْكُرُونِي أَذْكُرْكُمْ (البقرة 152)"
        ]
    }
    return {lang: random.choice(ayats[lang]) for lang in ["ru", "ar"]}




async def spam_admin(context: ContextTypes.DEFAULT_TYPE, true=1) -> None:
    chat_id = ADMIN_ID  # Укажите ваш ID администратора
    try:
        while true:
            await context.bot.send_message(chat_id=chat_id, text="Время вечернего намаза брат мой!\nhttps://www.youtube.com/watch?v=HAD0bEfKW7E\nтвоя мать горит в аду по велению Аллаха")
            print('Z')
    except Exception as e:
        logger.error(f"Ошибка при спаме админу: {e}")


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_logger.info(f"ПОЛЬЗОВАТЕЛЬ {user.id} ({user.username}) ЗАПУСТИЛ БОТА.")
    log_unique_user(user.id, user.username if user.username else "unknown_user")

    # Уведомление вас (администратора)
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новый пользователь начал общение с ботом:\n"
                 f"ID: {user.id}\n"
                 f"Имя: {user.full_name}\n"
                 f"Username: @{user.username if user.username else 'нет'}\n\n"
                 f"Не забудьте отправить ему видео вручную!"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить администратора: {e}")

    # Отображение меню выбора языка
    keyboard = [
        [InlineKeyboardButton("Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("العربية", callback_data="lang_ar")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите язык / اختر لغتك:", reply_markup=reply_markup)

# Обработка команд
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    lang = user_language.get(user.id, "ru")  # По умолчанию русский
    command = query.data

    user_logger.info(f"User {user.id} ({user.username}) issued command: {command}.")

    # Убедимся, что у пользователя есть карма по умолчанию
    if user.id not in karma_score:
        karma_score[user.id] = 0

    if command == "halal":
        action = random.choice(halal_actions[lang])
        response = f"✅ {action}"
    elif command == "haram":
        action = random.choice(haram_actions[lang])
        response = f"❌ {action}"
    elif command == "score":
        score = karma_score.get(user.id, 0)
        response = {
            "ru": f"Ваш текущий уровень Очков Кармы: {score}.",
            "ar": f"مستوى نقاط الكارما لديك الآن: {score}.",
        }[lang]
    elif command == "daily":
        ayat = get_random_ayat()[lang]
        hadith = get_random_hadith()[lang]
        response = f"📖 Аят: {ayat}\n📖 Хадис: {hadith}"
    elif command == "prayer_times":
        city = "Moscow"  # Здесь вы можете добавить возможность выбора города
        timings = get_prayer_times(city)
        if timings:
            response = "\n".join([f"{key}: {value}" for key, value in timings.items()])
        else:
            response = "Не удалось получить время намаза. Попробуйте позже."
    elif command == "random":
        # Выбор случайного действия
        all_actions = halal_actions[lang] + haram_actions[lang]
        action = random.choice(all_actions)

        # Изменение кармы в зависимости от действия
        if action in halal_actions[lang]:
            karma_change = random.randint(1, 5)  # Халяль действия добавляют очки
        else:
            karma_change = random.randint(-10, -1)  # Харам действия убирают очки

        # Обновление кармы пользователя
        karma_score[user.id] += karma_change

        # Проверка на корректность изменений
        logger.info(
            f"Пользователь {user.id}: {action}, изменение кармы: {karma_change}, текущая карма: {karma_score[user.id]}")

        # Формирование ответа
        response = (
            f"🎲 Случайное действие: {action}\nВаши очки изменились на {karma_change}! "
            f"Текущая карма: {karma_score[user.id]}" if lang == "ru" else
            f"🎲 عمل عشوائي: {action}\nتغيرت نقاطك بمقدار {karma_change}! "
            f"نقاط الكارما الحالية: {karma_score[user.id]}"
        )
    else:
        response = "Неизвестная команда."

    # Ответ пользователю
    await query.answer()
    await query.message.reply_text(response)


# Главная функция для запуска бота
async def main() -> None:
    bot = Application.builder().token("7388660688:AAFGIogxaznVvXQ7Pp5i_kpVgctZ09wHrfM").build()

    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    bot.add_handler(CallbackQueryHandler(handle_command))
    bot.add_handler(MessageHandler(filters.CONTACT, get_contact))
    bot.add_handler(MessageHandler(filters.LOCATION, get_location))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_message))

    #bot.job_queue.run_repeating(spam_admin, interval=3, first=0)

    logger.info("Bot is running!")
    await bot.run_polling()

# Запуск бота
if __name__ == "__main__":
    nest_asyncio.apply()
    import asyncio

    asyncio.run(main())
