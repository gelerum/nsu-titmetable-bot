import asyncio
import logging
import sys
from os import getenv
from re import match

import requests
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from bs4 import BeautifulSoup
from dotenv import load_dotenv


class Lesson:
    def __init__(self, number, subject, type_, room, tutor):
        self.number = number
        self.subject = subject
        self.type_ = type_
        self.room = room
        self.tutor = tutor


declensions = {
    "понедельник": "понедельник",
    "вторник": "вторник",
    "среда": "среду",
    "четверг": "четверг",
    "пятница": "пятницу",
    "суббота": "субботУ",
}


class Form(StatesGroup):
    group = State()
    day = State()


load_dotenv()
TOKEN = getenv("TOKEN")

form_router = Router()


@form_router.message(Form.group)
async def process_group(message: Message, state: FSMContext) -> None:
    if not match(r"^\d{5}(?:\.\d)?$", message.text):
        await message.answer("Неправильный номер группы. Попробуйте еще раз")
        return
    await state.update_data(group=message.text)
    await state.set_state(Form.day)
    await message.answer(
        "Выберите день недели",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Понедельник"),
                    KeyboardButton(text="Вторник"),
                    KeyboardButton(text="Среда"),
                    KeyboardButton(text="Четверг"),
                    KeyboardButton(text="Пятница"),
                    KeyboardButton(text="Суббота"),
                ]
            ],
            resize_keyboard=True,
        ),
    )


@form_router.message(Form.day)
async def process_day(message: Message, state: FSMContext) -> None:
    if message.text.lower() not in [
        "понедельник",
        "вторник",
        "среда",
        "четверг",
        "пятница",
        "суббота",
    ]:
        await message.answer("Неправильный день недели. Попробуйте еще раз")
        return
    user_data = await state.get_data()
    group = user_data["group"]
    day = message.text.lower()
    await response = requests.get(f"https://table.nsu.ru/group/{group}")

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        time_table_class = soup.find("table", class_="time-table")

        rows = time_table_class.find_all("tr")

        time_table: list[Lesson] = []
        i = 1
        for row in rows[1:]:
            cells = row.find_all(["th", "td"])
            row_data = []
            j = 0
            for cell in cells[1:]:
                if j == list(declensions.keys()).index(day):
                    cell_div = cell.find("div", class_="cell")
                    if cell_div is not None:
                        tutor = cell_div.find("a", class_="tutor")
                        if tutor is not None:
                            tutor = tutor.text.strip()
                        else:
                            tutor = ""
                        time_table.append(
                            Lesson(
                                i,
                                cell_div.find("div", class_="subject").text.strip(),
                                cell_div.find("span").text.strip(),
                                cell_div.find("div", class_="room").text.strip(),
                                tutor,
                            )
                        )
                j += 1
            i += 1
    else:
        await message.answer(
            f"Ошибка запроса: {response.status_code}",
            reply_markup=ReplyKeyboardRemove(),
        )

    text = f"Расписание на {declensions[day]} {group} группы:\n"
    for lesson in time_table:
        text += f"{lesson.number}. {lesson.subject} {lesson.type_} {lesson.tutor} {lesson.room}\n"

    await message.answer(
        text,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()


@form_router.message()
async def any_command_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.group)
    await message.answer("Введите номер группы", reply_markup=ReplyKeyboardRemove())


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
