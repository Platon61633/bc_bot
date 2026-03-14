import telebot
from telebot import types

# Initialize the bot with your token
API_TOKEN = 'YOUR_API_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

# Function to show events for registration
@bot.message_handler(commands=['register'])
def register_event(message):
    # Fetch last 3 announcements from #анонс@bcmsu
    announcements = get_last_announcements()  # Assume this function fetches announcements

    if announcements:
        keyboard = types.InlineKeyboardMarkup()
        for announcement in announcements:
            button = types.InlineKeyboardButton(text=announcement['title'], callback_data=announcement['id'])
            keyboard.add(button)
        bot.send_message(message.chat.id, "Выберите мероприятие для регистрации:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Нет доступных анонсов.")

# Function to fetch the last 3 announcements (stub)
def get_last_announcements():
    return [
        {'id': 'event1', 'title': 'Анонс мероприятия 1'},
        {'id': 'event2', 'title': 'Анонс мероприятия 2'},
        {'id': 'event3', 'title': 'Анонс мероприятия 3'},
    ]

# Function to handle callback queries
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    # Handle event registration based on button clicked
    event_id = call.data
    # Proceed to register the user for the event using event_id
    bot.answer_callback_query(call.id, text="Вы зарегистрированы на событие!")  # Feedback to user

# Start the bot
bot.polling()