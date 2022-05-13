from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import BotBlocked


token = '5381219717:AAGmW2vYBGKaqnOpH3ng3iGC_o9Bff4KvsQ'
base_url = 'https://api.telegram.org/bot' + token

bot = Bot(token)
dp = Dispatcher(bot)

# TODO write tests for api
# TODO write doc for pixela
# TODO create git repositary
# TODO implement bot behaviour


@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked):
    print(f'Меня заблокировали!\nСообщение: {update}\nОшибка: {exception}')
    return True


@dp.message_handler(commands='test')
async def test1(message: types.Message):
    await message.reply('Test 1')


executor.start_polling(dp, skip_updates=True)