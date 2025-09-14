import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters.command import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, BufferedInputFile, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import ClientSession  # подключение aiohttp
from config import TELEGRAM_TOKEN

# Инстанцирование бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Название файла с изображением велосипеда
BIKE_IMAGE_PATH = "bike.png"

# Класс состояний для FSM
class RouteStates(StatesGroup):
    START_POINT = State()
    NEXT_POINT = State()

# Переменные для хранения начальных координат и списка точек маршрута
start_point = None
route_points = []

# Функция для получения высоты по координатам
async def fetch_elevation(lat, lon):
    base_url = 'https://api.opentopodata.org/v1/srtm30m'
    params = {'locations': f'{lat},{lon}', 'interpolation': 'cubic'}
    async with ClientSession() as session:  # создаем клиентскую сессию aiohttp
        async with session.get(base_url, params=params) as resp:
            data = await resp.json()
            return float(data['results'][0]['elevation'])

# Приветствие при старте бота
@dp.message(CommandStart())
async def greet_user(message: Message):
    await message.answer("""
Привет! Я помогаю рассчитать профиль маршрута. Используйте команды:
/menu - открывает меню для работы с маршрутом
    """)

...

# Меню выбора операций
@dp.message(Command("menu"))
async def send_menu(message: Message):
    markup = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text="🚴 Старт маршрута"),
            KeyboardButton(text="✨ Следующая точка"),
            KeyboardButton(text="➡️ Показать профиль маршрута")
        ]
    ], resize_keyboard=True, one_time_keyboard=False, is_persistent=True)
    await message.answer("""
Меню для работы с маршрутом:
🚴 Старт маршрута - начало нового маршрута
✨ Следующая точка - добавить новую точку маршрута
➡️ Показать профиль маршрута - вывести информацию о маршруте
    """, reply_markup=markup)

...
# Начало маршрута
@dp.message(F.text == "🚴 Старт маршрута")
async def start_route(message: Message, state: FSMContext):
    global start_point, route_points
    start_point = None
    route_points.clear()
    with open(BIKE_IMAGE_PATH, "rb") as bike_image:
        image_bytes = BufferedInputFile(bike_image.read(), filename=BIKE_IMAGE_PATH)
        await bot.send_photo(chat_id=message.chat.id, photo=image_bytes)
    await message.answer("Введите координаты начальной точки маршрута в формате широта, долгота (пример: 55.115923, 82.970700)")
    await state.set_state(RouteStates.START_POINT)

# Обработка начальной точки маршрута
@dp.message(RouteStates.START_POINT)
async def process_start_point(message: Message, state: FSMContext):
    try:
        lat, lon = map(float, message.text.split(','))
        height = await fetch_elevation(lat, lon)
        global start_point, route_points
        start_point = (lat, lon)
        route_points.clear()
        route_points.append((height, 0))  # Первая точка маршрута с высотой и дельтой 0
        await message.answer(f"""
Точка старта установлена!
Широта: {lat}
Долгота: {lon}
Высота: {height:.2f} м
Разница высот: 0 м
        """)
        await state.clear()
    except ValueError:
        await message.answer("Ошибка ввода координат. Повторите попытку.")

# Продолжение маршрута
@dp.message(F.text == "✨ Следующая точка")
async def next_point(message: Message, state: FSMContext):
    if not start_point:
        await message.answer("Сначала запустите маршрут командой 🚴 Старт маршрута.")
    else:
        await message.answer("Введите координаты следующей точки маршрута в формате широта, долгота (пример: 55.115923, 82.970700)")
        await state.set_state(RouteStates.NEXT_POINT)

# Обработка последующих точек маршрута
@dp.message(RouteStates.NEXT_POINT)
async def process_next_point(message: Message, state: FSMContext):
    try:
        lat, lon = map(float, message.text.split(','))
        current_height = await fetch_elevation(lat, lon)
        first_height = route_points[0][0]
        delta_height = current_height - first_height
        route_points.append((current_height, delta_height))
        await message.answer(f"""
Высота текущей точки: {current_height:.2f} м
Разница высот: {delta_height:.2f} м
        """)
        await state.clear()
    except ValueError:
        await message.answer("Ошибка ввода координат. Повторите попытку.")

# Просмотр профиля маршрута
@dp.message(F.text == "➡️ Показать профиль маршрута")
async def show_route_profile(message: Message):
    if not route_points:
        await message.answer("Маршрут ещё не начат. Воспользуйтесь командой 🚴 Старт маршрута.")
    else:
        profile_text = "\n".join([
            f"{i + 1}. Высота: {h:.2f} м, Разница высот: {dh:.2f} м" for i, (h, dh) in enumerate(route_points)
        ])
        await message.answer(f"Профиль маршрута:\n{profile_text}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())