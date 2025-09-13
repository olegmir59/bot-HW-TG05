import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from io import BytesIO
import requests
from config import TELEGRAM_TOKEN


# Токен нашего Telegram-бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Название файла с изображением велосипеда
BIKE_IMAGE_PATH = "bike.png"


# Функция для получения высоты по координатам
def fetch_elevation(lat, lon):
    base_url = 'https://api.opentopodata.org/v1/srtm30m'
    params = {'locations': f'{lat},{lon}', 'interpolation': 'cubic'}
    response = requests.get(base_url, params=params)
    data = response.json()
    return float(data['results'][0]['elevation'])


# Переменные для хранения начальных координат и списка точек маршрута
start_point = None
route_points = []


# Команда "/start" выводит приветствие
@bot.message_handler(commands=['start'])
def greet_user(message):
    bot.send_message(message.chat.id, """
Привет! Я помогаю рассчитать профиль маршрута. Используйте команды:
/menu - открывает меню для работы с маршрутом
    """)


# Команда "/menu" выводит меню
@bot.message_handler(commands=['menu'])
def send_menu(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button_start_route = KeyboardButton("🚴 Старт маршрута")
    button_next_point = KeyboardButton("✨ Следующая точка")
    button_show_profile = KeyboardButton("➡️ Показать профиль маршрута")
    markup.add(button_start_route, button_next_point, button_show_profile)
    bot.send_message(message.chat.id, """
Меню для работы с маршрутом:
🚴 Старт маршрута - начало нового маршрута
✨ Следующая точка - добавить новую точку маршрута
➡️ Показать профиль маршрута - вывести информацию о маршруте
    """, reply_markup=markup)


# Основная логика обработки кнопок
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    global start_point, route_points
    if message.text == "🚴 Старт маршрута":
        # Открываем изображение заново перед каждым использованием
        with open(BIKE_IMAGE_PATH, "rb") as bike_image:
            bot.send_photo(message.chat.id, bike_image)
        msg = bot.reply_to(message,
                          "Введите координаты начальной точки маршрута в формате широта, долгота (пример: 55.115923, 82.970700)")
        bot.register_next_step_handler(msg, process_start_point)

    elif message.text == "✨ Следующая точка":
        if not start_point:
            bot.reply_to(message, "Сначала запустите маршрут командой 🚴 Старт маршрута.")
        else:
            msg = bot.reply_to(message,
                              "Введите координаты следующей точки маршрута в формате широта, долгота (пример: 55.115923, 82.970700)")
            bot.register_next_step_handler(msg, process_next_point)

    elif message.text == "➡️ Показать профиль маршрута":
        show_route_profile(message)


def process_start_point(message):
    try:
        lat, lon = map(float, message.text.split(','))
        height = fetch_elevation(lat, lon)
        global start_point

        start_point = (lat, lon)
        route_points.clear()
        route_points.append((height, 0))  # Первая точка маршрута с высотой и дельтой 0
        bot.reply_to(message,
                    f"Точка старта установлена!\nШирота: {lat}, Долгота: {lon}\nВысота: {height:.2f} м\nРазница высот: 0 м")
    except Exception as e:
        bot.reply_to(message, "Ошибка ввода координат. Попробуйте снова.")


def process_next_point(message):
    try:
        lat, lon = map(float, message.text.split(','))
        current_height = fetch_elevation(lat, lon)
        first_height = route_points[0][0]
        delta_height = current_height - first_height
        route_points.append((current_height, delta_height))
        bot.reply_to(message, f"Высота текущей точки: {current_height:.2f} м\nРазница высот: {delta_height:.2f} м")
    except Exception as e:
        bot.reply_to(message, "Ошибка ввода координат. Попробуйте снова.")


def show_route_profile(message):
    profile_text = "\n".join(
        [f"{i + 1}. Высота: {h:.2f} м, Разница высот: {dh:.2f} м" for i, (h, dh) in enumerate(route_points)])
    bot.reply_to(message, f"Профиль маршрута:\n{profile_text}")


if __name__ == "__main__":
    print("Telegram бот запущен!")
    bot.polling(none_stop=True)