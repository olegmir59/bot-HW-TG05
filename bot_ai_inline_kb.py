import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters.command import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import ClientSession
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
    async with ClientSession() as session:
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

# Меню выбора операций
@dp.message(Command("menu"))
async def send_menu(message: Message):
    inline_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚴 Старт маршрута", callback_data="start_route")],
        [InlineKeyboardButton(text="✨ Следующая точка", callback_data="next_point")],
        [InlineKeyboardButton(text="➡️ Показать профиль маршрута", callback_data="show_profile")]
    ])
    await message.answer("Выберите действие:", reply_markup=inline_markup)

# Обработка кликов по inline-кнопкам
@dp.callback_query(F.data.in_(["start_route", "next_point", "show_profile"]))  # Исправили синтаксис
async def handle_inline_buttons(callback: CallbackQuery, state: FSMContext):
    action = callback.data
    match action:
        case "start_route":
            global start_point, route_points
            start_point = None
            route_points.clear()
            with open(BIKE_IMAGE_PATH, "rb") as bike_image:
                image_bytes = BufferedInputFile(bike_image.read(), filename=BIKE_IMAGE_PATH)
                await bot.send_photo(chat_id=callback.message.chat.id, photo=image_bytes)
            await callback.message.answer("Введите координаты начальной точки маршрута в формате широта, долгота (пример: 55.115923, 82.970700)")
            await state.set_state(RouteStates.START_POINT)
        case "next_point":
            if not start_point:
                await callback.message.answer("Сначала запустите маршрут командой 🚴 Старт маршрута.")
            else:
                await callback.message.answer("Введите координаты следующей точки маршрута в формате широта, долгота (пример: 55.115923, 82.970700)")
                await state.set_state(RouteStates.NEXT_POINT)
        case "show_profile":
            if not route_points:
                await callback.message.answer("Маршрут ещё не начат. Воспользуйтесь командой 🚴 Старт маршрута.")
            else:
                profile_text = "\n".join([
                    f"{i + 1}. Высота: {h:.2f} м, Разница высот: {dh:.2f} м" for i, (h, dh) in enumerate(route_points)
                ])
                await callback.message.answer(f"Профиль маршрута:\n{profile_text}")

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

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())