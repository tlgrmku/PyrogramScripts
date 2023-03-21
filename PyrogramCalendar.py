from pyrogram import Client, filters
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove)
import time
import calendar
import json
from re import fullmatch


users = {}



def gettime(date) -> list:
    with open('timetab.json', 'r') as read_json_file:
        schedule = json.load(read_json_file)
    try:
        timelist = schedule[date]
    except KeyError:
        return False
    else:
        arraytime = []
        for hour in timelist:
            arraytime.append(InlineKeyboardButton(hour, callback_data=hour))
        return [arraytime]



def getcalendar(localyear, localmonth) -> list:
    textmonth = calendar.month_abbr[localmonth]
    arraycalendar = calendar.monthcalendar(localyear, localmonth)
    calendarnow = []
    for week in range(len(arraycalendar)):
        arrayweek = []
        for day in arraycalendar[week]:
            if day == 0:
                arrayweek.append(InlineKeyboardButton(' ', callback_data=' '))
            else:
                arrayweek.append(InlineKeyboardButton(str(day), callback_data=str(day)))
        calendarnow.append(arrayweek)
    control = ['<', textmonth, str(localyear), 'X', '>']
    arraycontrol = []
    for btn in control:
        arraycontrol.append(InlineKeyboardButton(btn, callback_data=btn))
    calendarnow.append(arraycontrol)
    return calendarnow


app = Client('bot')

@app.on_message(filters.command(commands=['start', 's'], prefixes='/'))
async def startmsg(_, msg):
    global users
    year, month = time.strftime('%Y-%m').split('-')
    users[msg.from_user.id] = {'year': int(year), 'month': int(month)}
    await app.send_message(
        msg.from_user.id,
        'Выберите дату',
        reply_markup=InlineKeyboardMarkup(getcalendar(int(year), int(month)))
        )


@app.on_callback_query()
async def callbackmsg(_, callback_query):
    global users
    if users.get(callback_query.from_user.id):
        userdata = users.get(callback_query.from_user.id)
        year = userdata.get('year')
        month = userdata.get('month')
        days = [str(day) for day in range(1, 32)]
        match callback_query.data:
            case callback_query.data as date if date in days:
                datemonthyear = date + '.' + str(month) + '.' + str(year)
                userdata['date'] = date
                timelist = gettime(datemonthyear)
                if timelist:
                    timetext = 'Выберите время'
                else:
                    timetext = 'Свободного времени на это число нет. Выберите другую дату'
                    timelist = [[InlineKeyboardButton('Назад', callback_data='<<')]]
                await app.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, text=timetext, reply_markup=InlineKeyboardMarkup(timelist))
            case callback_query.data as hourmin if fullmatch(r'\d{2}:\d{2}', hourmin):
                userdata['hourmin'] = hourmin
                await callback_query.answer(f"{callback_query.from_user.first_name} проверьте дату и время! {userdata['date']}.{userdata['month']}.{userdata['year']} в {userdata['hourmin']}", show_alert=True)
                await app.edit_message_text(chat_id=callback_query.message.chat.id,
                                            message_id=callback_query.message.id,
                                            text=f"Выбранные вами дата: {userdata['date']}.{userdata['month']}.{userdata['year']} и время: {userdata['hourmin']}",
                                            reply_markup=ReplyKeyboardRemove())
            case '<<':
                await app.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, text='Выберите дату', reply_markup=InlineKeyboardMarkup(getcalendar(year, month)))
            case '>':
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
                users[callback_query.from_user.id] = {'year': int(year), 'month': int(month)}
                await app.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=InlineKeyboardMarkup(getcalendar(year, month)))
            case 'X':
                await app.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, text='Что бы снова воспользоваться выбором даты наберите /start или /s', reply_markup=ReplyKeyboardRemove())
            case '<':
                if month == 1:
                    month = 12
                    year -= 1
                else:
                    month -= 1
                users[callback_query.from_user.id] = {'year': int(year), 'month': int(month)}
                await app.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=InlineKeyboardMarkup(getcalendar(year, month)))
            case _:
                print(callback_query.data)
                pass


app.run()

