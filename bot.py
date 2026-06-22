from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)
import credentials

# ============================================================
#                  ГОЛОВНА СТОРІНКА
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'translate': 'Перекладач 🌐',
        'recommend': 'Рекомендації (фільми, книги) 🎬📚'
    })

# ============================================================
#                  Випадковий факт
# ============================================================

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'random')
    text = load_message('random')
    await send_text(update, context, text)
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, "Розкажи щось цікаве")
    await send_text_buttons(update, context, response,
                            {
                                'random_finish': 'Закінчити',
                                'random_one_more': 'Хочу ще факт'
                            })

async def random_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == 'random_finish':
        await start(update, context)
    elif query == 'random_one_more':
        await random(update, context)
    await update.callback_query.answer()

# ============================================================
#                  ChatGPT інтерфейс
# ============================================================

async def chat_gpt_interface(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'gpt'

    text = load_message('gpt')
    await send_image(update, context, 'gpt')
    await send_text_buttons(update, context, text, {
        'gpt_finish': 'Закінчити ❌'
    })

    prompt = load_prompt('gpt')
    chat_gpt.set_prompt(prompt)

async def chat_gpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    user_text = update.message.text

    if mode == 'gpt':
        response = await chat_gpt.add_message(user_text)
        await send_text_buttons(update, context, response, {
            'gpt_finish': 'Закінчити ❌'
        })

    elif mode == 'talk':
        response = await chat_gpt.add_message(user_text)
        await send_text_buttons(update, context, response, {
            'talk_finish': 'Закінчити ❌'
        })

    elif mode == 'talk_select':
        await send_text(update, context, "Будь ласка, спочатку оберіть особистість за допомогою кнопок вище 👆")

    elif mode == 'quiz_waiting_answer':
        response = await chat_gpt.add_message(user_text)
        if response.startswith('Правильно!'):
            context.user_data['quiz_score'] = context.user_data.get('quiz_score', 0) + 1

        current_score = context.user_data.get('quiz_score', 0)
        full_response = f"{response}\n\n🏆 Ваш поточний рахунок: {current_score}"

        await send_text_buttons(update, context, full_response, {
            'quiz_more': 'Наступне питання ➡️',
            'quiz_change_topic': 'Змінити тему 🔄',
            'quiz_finish': 'Завершити квіз 🏁'
        })

    elif mode == 'quiz_select':
        await send_text(update, context, "Спочатку оберіть тему квізу за допомогою кнопок вище 👆")

    elif mode == 'translate_waiting_text':
        target_lang = context.user_data.get('translate_to', 'англійську GB')

        gpt_request = f'Переклади цей текст на {target_lang}:\n\n{user_text}'
        response = await chat_gpt.add_message(gpt_request)

        await send_text_buttons(update, context, response, {
            'translate_change_lang': 'Змінити мову 🔄',
            'translate_finish': 'Закінчити ❌'
        })

    elif mode == 'translate_select_lang':
        await send_text(update, context, 'Спочатку оберіть мову перекладу за допомогою кнопок вище 👆')

    elif mode == 'recommend_waiting_genre':
        if 'recommend_genre' not in context.user_data or context.user_data.get('recommend_genre') != user_text:
            context.user_data['recommend_genre'] = user_text

        category = context.user_data.get('recommend_category')
        genre = context.user_data.get('recommend_genre')

        gpt_request = f"Категорія: {category}. Жанр/Настрій: {genre}."
        response = await chat_gpt.add_message(gpt_request)

        context.user_data['last_recommendation'] = response
        await send_text_buttons(update, context, response, {
            'recommend_dislike': 'Не подобається 👎',
            'recommend_finish': 'Закінчити ❌'
        })

    elif mode == 'recommend_select_category':
        await send_text(update, context, 'Спочатку оберіть категорію рекомендацій за допомогою кнопок вище 👆')

    else:
        await send_text(update, context, "Будь ласка, оберіть команду в меню 🤖")

async def gpt_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()

    if query == 'gpt_finish':
        await start(update, context)

# ============================================================
#                Діалог з відомою особистістю
# ============================================================

async def dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'talk'

    text = load_message('talk')
    await send_image(update, context, 'talk')
    await send_text_buttons(update, context, text, {
        'talk_cobain': 'Курт Кобейн 🎸',
        'talk_elizabeth': 'Королева Єлизавета II 👑',
        'talk_tolkien': 'Дж. Р. Р. Толкін 📖',
        'talk_nietzsche': 'Фрідріх Ніцше 🧠',
        'talk_hawking': 'Стівен Гокінг 🔬'
    })

async def dialog_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()
    if query == 'talk_finish':
        await start(update, context)
        return
    characters = {
        'talk_cobain': ('talk_cobain', 'Привіт! Я - Курт Кобейн. Про що поговоримо? 🎸'),
        'talk_elizabeth': ('talk_elizabeth', 'Вітаю вас. Я - Королева Єлизавета II. Рада можливості провести цю бесіду. 👑'),
        'talk_tolkien': ('talk_tolkien', 'Вітаю, мій друже! Я - Дж.Р.Р. Толкін. Що вас цікавить? 📖'),
        'talk_nietzsche': ('talk_nietzsche', 'Я - Фрідріх Ніцше. Ну ж бо, зазирнемо у безодню разом. 🧠'),
        'talk_hawking': ('talk_hawking', 'Привіт. Я - Стівен Гокінг. Про що ти хочеш дізнатися? 🔬')
    }

    if query in characters:
        prompt_file, greeting = characters[query]

        context.user_data['mode'] = 'talk'
        prompt = load_prompt(prompt_file)
        chat_gpt.set_prompt(prompt)
        await send_text(update, context, greeting)

# ============================================================
#                  Квіз
# ============================================================

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['quiz_score'] = 0
    context.user_data['mode'] = 'quiz_select'

    text = load_message('quiz')
    await send_image(update, context, 'quiz')

    await send_text_buttons(update, context, text, {
        'quiz_prog': 'ПрограмуванняPython 🐍',
        'quiz_math': 'Математика 📐',
        'quiz_biology': 'Біологія 🧬'
    })

async def quiz_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()

    if query == 'quiz_finish':
        score = context.user_data.get('quiz_score', 0)
        await send_text(update, context, f"Квіз завершено! Ваш результат: {score} 🏆")
        await start(update, context)
        return

    if query == 'quiz_change_topic':
        context.user_data['mode'] = 'quiz_select'
        await  send_text_buttons(update, context, 'Оберіть нову тему для квізу 👇', {
            'quiz_prog': 'Програмування Python 🐍',
            'quiz_math': 'Математика 📐',
            'quiz_biology': 'Біологія 🧬'
        })
        return

    themes = ['quiz_prog', 'quiz_math', 'quiz_biology', 'quiz_more']
    if query in themes:
        context.user_data['mode'] = 'quiz_waiting_answer'

        if query != 'quiz_more':
            prompt = load_prompt('quiz')
            chat_gpt.set_prompt(prompt)
            user_message = query
        else:
            user_message = 'quiz_more'

        question = await chat_gpt.add_message(user_message)
        await send_text(update, context, question)

# ============================================================
#                  Перекладач
# ============================================================

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'translate_select_lang'

    text = load_message('translate')
    await send_image(update, context, 'translate')

    await send_text_buttons(update, context, text, {
        'translation_en': 'Англійська GB',
        'translation_uk': 'Українська UA',
        'translation_es': 'Іспанська ES',
        'translation_de': 'Німецька DE',
        'translation_pl': 'Польська PL'
    })

async def translate_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()

    if query == 'translate_finish':
        await start(update, context)
        return

    if query == 'translate_change_lang':
        context.user_data['mode'] = 'translate_select_lang'
        await send_text_buttons(update, context, 'Оберіть нову мову для перекладу 👇', {
            'translation_en': 'Англійська GB',
            'translation_uk': 'Українська UA',
            'translation_es': 'Іспанська ES',
            'translation_de': 'Німецька DE',
            'translation_pl': 'Польська PL'
        })
        return

    if query.startswith('translation_'):
        languages = {
            'translation_en': 'англійську 🇬🇧',
            'translation_uk': 'українську 🇺🇦',
            'translation_es': 'іспанську 🇪🇸',
            'translation_de': 'німецьку 🇩🇪',
            'translation_pl': 'польську 🇵🇱'
        }

        context.user_data['translate_to'] = languages[query]
        context.user_data['mode'] = 'translate_waiting_text'

        prompt = load_prompt('translate')
        chat_gpt.set_prompt(prompt)

        await send_text(update, context, f'Надішліть текст, який потрібно перекласти на {languages[query]}:')

# ============================================================
#             Рекомендації щодо фільмів та книг
# ============================================================

async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'recommend_select_category'
    context.user_data['ignored_items'] = []

    text = load_message('recommend')
    await send_image(update, context, 'recommend')

    await send_text_buttons(update, context, text, {
        'recommend_movies': 'Фільми 🎬',
        'recommend_books': 'Книги 📚',
        'recommend_music': 'Музика 🎵'
    })

async def recommend_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    await update.callback_query.answer()

    if query == 'recommend_finish':
        await start(update, context)
        return

    if query == 'recommend_dislike':
        last_recommendation = context.user_data.get('last_recommendation', '')
        if last_recommendation:
            context.user_data['ignored_items'].append(last_recommendation)

        context.user_data['mode'] = 'recommend_waiting_genre'

        category = context.user_data.get('recommend_category')
        genre = context.user_data.get('recommend_genre')
        ignored = ', '.join(context.user_data['ignored_items'])

        gpt_request = (
            f"Запропонуй інший варіант у категорії '{category}' (жанр: {genre}). "
            f"Будь ласка, НЕ РЕКОМЕНДУЙ наступні твори/виконавців: {ignored}."
        )

        response = await chat_gpt.add_message(gpt_request)
        context.user_data['last_recommendation'] = response

        await send_text_buttons(update, context, response, {
            'recommend_dislike': 'Не подобається 👎',
            'recommend_finish': 'Закінчити ❌'
        })
        return

    if query in ['recommend_movies', 'recommend_books', 'recommend_music']:
        categories = {
            'recommend_movies': 'фільми 🎬',
            'recommend_books': 'книги 📚',
            'recommend_music': 'музика 🎵'
        }

        context.user_data['recommend_category'] = categories[query]
        context.user_data['mode'] = 'recommend_waiting_genre'

        prompt = load_prompt('recommend')
        chat_gpt.set_prompt(prompt)

        await send_text(update, context, f"Ви обрали категорію: {categories[query]}.\nНапишіть бажаний жанр "
                                         f"або настрій (наприклад: фантастика, комедія, детектив, для відпочинку):")

# ============================================================
#                      Токени
# ============================================================

chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# ============================================================
#                    Обробники команд
# ============================================================

app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', chat_gpt_interface))
app.add_handler(CommandHandler('talk', dialog))
app.add_handler(CommandHandler('quiz', quiz))
app.add_handler(CommandHandler('translate', translate))
app.add_handler(CommandHandler('recommend', recommend))

# ============================================================
#                       Коллбеки
# ===========================================================

app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(gpt_buttons_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(dialog_buttons_handler, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(translate_buttons_handler, pattern='^translate_.*|^translation_.*'))
app.add_handler(CallbackQueryHandler(recommend_buttons_handler, pattern='^recommend_.*'))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt_handler))
app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
