from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)
import  credentials


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })

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


async def chat_gpt_interface(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mode'] = 'gpt'

    text = load_message('gpt')
    await send_image(update, context, 'gpt')
    await send_text(update, context, text)

    prompt = load_prompt('gpt')
    chat_gpt.set_prompt(prompt)

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

async def chat_gpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode')
    user_text = update.message.text

    if mode == 'gpt':
        response = await chat_gpt.add_message(user_text)
        await send_text(update, context, response)

    elif mode == 'talk':
        response = await chat_gpt.add_message(user_text)
        await send_text_buttons(update, context, response, {
            'talk_finish': 'Закінчити ❌'
        })

    elif mode == 'talk_select':
        await send_text(update, context, "Будь ласка, спочатку оберіть особистість за допомогою кнопок вище 👆")
    else:
        await send_text(update, context, "Будь ласка, оберіть команду в меню 🤖")


chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
# app.add_handler(CommandHandler('command', handler_func))
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', chat_gpt_interface))
app.add_handler(CommandHandler('talk', dialog))


# Зареєструвати обробник колбеку можна так:
# app.add_handler(CallbackQueryHandler(app_button, pattern='^app_.*'))
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
# app.add_handler(CallbackQueryHandler(default_callback_handler))
app.add_handler(CallbackQueryHandler(dialog_buttons_handler, pattern='^talk_.*'))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt_handler))
app.run_polling()
