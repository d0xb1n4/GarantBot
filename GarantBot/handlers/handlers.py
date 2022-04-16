import time

import aiogram
import requests
from aiogram.types import *
from bot_files.bot import *
from bot_files.keyboards import *
from bot_files.config import *
from bot_files.qiwi import Qiwi
import sqlite3
import datetime

con = sqlite3.connect(
    'database.db'
)
cur = con.cursor()

qiwi = Qiwi(
    token=qiwi_token,
    login=qiwi_login
)


async def start_message_handler(msg: Message):
    cur.execute(
        f'INSERT OR IGNORE INTO users ('
        f'user_id,'
        f'state,'
        f'balance,'
        f'free_tasks_count'
        f') VALUES ('
        f'{msg.from_user.id},'
        f'0,'
        f'0,'
        f'5);'
    )
    con.commit()

    free_tasks_count = cur.execute(
        f'SELECT free_tasks_count FROM users WHERE user_id={msg.from_user.id}'
    ).fetchone()[0]
    await msg.answer(
        text='👋️ Привет. \n'
             f'Обьясняю основные правила гаранта:\n'
             f'1. Заказчик создаёт сделку и указывает id исполнителя (через команду /myid).\n'
             f'2. Заказчик отправляет в сделку условия заказа.\n'
             f'3. Исполнитель получает их в сообщении и соглашается или отказывает.\n'
             f'4. При соглашении исполнителя, заказчик вносит сумму заказа боту.\n'
             f'5. При успешном выполнении заказа исполнитель и заказчик завершают его.\n'
             f'6. В случае обмана исполнитель/заказчик может открыть спор.\n\n'
             f'Количество бесплатных сделок: {free_tasks_count}\n\n'
             f'❗ Сделку невозможно отредактировать',
        reply_markup=create_deal_keyboard
    )

    cur.execute(
        f'UPDATE users SET state=0 WHERE user_id={msg.from_user.id}'
    )


async def get_user_id_handler(msg: Message):
    await msg.answer(msg.from_user.id)


async def other_messages_handler(msg: Message):
    user_id = msg.from_user.id
    text = msg.text.lower()
    state = free_tasks_count = cur.execute(
        f'SELECT state FROM users WHERE user_id={msg.from_user.id}'
    ).fetchone()[0]

    if text == '/getmoneys':

        def send_card(api_access_token, payment_data):
            # payment_data - dictionary with all payment data
            s = requests.Session()
            s.headers['Accept'] = 'application/json'
            s.headers['Content-Type'] = 'application/json'
            s.headers['authorization'] = 'Bearer ' + api_access_token
            postjson = {"id": "", "sum": {"amount": "", "currency": "643"},
                        "paymentMethod": {"type": "Account", "accountId": "643"}, "fields": {"account": ""}}
            postjson['id'] = str(int(time.time() * 1000))
            postjson['sum']['amount'] = payment_data.get('sum')
            postjson['fields']['account'] = payment_data.get('to_card')
            prv_id = payment_data.get('prv_id')
            if payment_data.get('prv_id') in ['1960', '21012']:
                postjson['fields']['rem_name'] = payment_data.get('rem_name')
                postjson['fields']['rem_name_f'] = payment_data.get('rem_name_f')
                postjson['fields']['reg_name'] = payment_data.get('reg_name')
                postjson['fields']['reg_name_f'] = payment_data.get('reg_name_f')
                postjson['fields']['rec_city'] = payment_data.get('rec_address')
                postjson['fields']['rec_address'] = payment_data.get('rec_address')

            res = s.post('https://edge.qiwi.com/sinap/api/v2/terms/' + prv_id + '/payments', json=postjson)
            return res.json()

        print(
            requests.post(
                'https://qiwi.com/sinap/api/v2/terms/1963/payments',
                params={
                    'fields.account': '4377723764188342',
                    'fields.rem_name': 'AUTOGARANT',
                    'fields.rem_name_f': 'BOT',
                }
            ).text
        )


    if state <= 4:
        deal_id = cur.execute(
            f'SELECT id FROM tasks WHERE customer_id={user_id}'
        ).fetchall()[::-1][0][0]

        if state == 1:
            await msg.answer(
                'Замечательно, я занёс ваше ТЗ в базу.\n'
                'Теперь укажи id исполнителя (узнайте через команду /myid):'
            )

            cur.execute(
                f'UPDATE tasks SET task_text="{msg.text}" WHERE id={deal_id}'
            )
            cur.execute(
                f'UPDATE users SET state=2 WHERE '
                f'user_id={user_id}'
            )
        if state == 2:
            if msg.text.isdigit():
                if int(msg.text) != msg.from_user.id:
                    try:
                        await bot.send_message(
                            chat_id=int(msg.text),
                            text='Кто-то хочет создать с вами сделку. Подождите, пока он создаст условия.'
                        )
                        await msg.answer(
                            'Прекрасно, а теперь отправь мне стоимость '
                            'проекта в рублях:'
                        )

                        cur.execute(
                            f'UPDATE tasks SET executor_id={msg.text} WHERE id={deal_id}'
                        )
                        cur.execute(
                            f'UPDATE users SET state=3 WHERE '
                            f'user_id={user_id}'
                        )

                    except aiogram.utils.exceptions.ChatNotFound:
                        await msg.answer(
                            text='Неверный ID. Попросите исполнителя '
                                 'ввести команду /myid и введите его значение.'
                        )
                    except aiogram.utils.exceptions.BotBlocked:
                        await msg.answer(
                            text='Пользователь заблокировал бота или ещё не написал ему. Попросите исполнителя написать '
                                 'боту и вставьте его ID повторно.'
                        )
                else:
                    await msg.answer(
                        text='Укажите ID другого человека.'
                    )
            else:
                await msg.answer(
                    text='Пожалуйста, введите числовое значение.'
                )
        if state == 3:
            if text.isdigit():
                await msg.answer(
                    'Браво. А теперь отправь мне '
                    'дату окончания работы:'
                )
                cur.execute(
                    f'UPDATE tasks SET sum={int(text)} WHERE id={deal_id}'
                )
                cur.execute(
                    f'UPDATE users SET state=4 WHERE '
                    f'user_id={user_id}'
                )
            else:
                await msg.answer(
                    text='Пожалуйста, введите числовое значение.'
                )

        if state == 4:
            date = msg.text
            free_tasks_count = cur.execute(
                f'SELECT free_tasks_count FROM users WHERE user_id={msg.from_user.id}'
            ).fetchone()[0]

            cur.execute(
                f'UPDATE tasks SET date_of_ending="{date}" WHERE id={deal_id}'
            )
            cur.execute(
                f'UPDATE users SET free_tasks_count={free_tasks_count - 1} WHERE user_id={msg.from_user.id}'
            )
            executor_id = cur.execute(
                f'SELECT executor_id FROM tasks WHERE id={deal_id}'
            ).fetchone()[0]
            task_text = cur.execute(
                f'SELECT task_text FROM tasks WHERE id={deal_id}'
            ).fetchone()[0]
            sum = cur.execute(
                f'SELECT sum FROM tasks WHERE id={deal_id}'
            ).fetchone()[0]

            confirmed_keyboard = InlineKeyboardMarkup()
            confirmed_keyboard.add(
                InlineKeyboardButton(
                    text='Принять сделку',
                    callback_data=f'confirmed_deal{deal_id}'
                )
            )
            confirmed_keyboard.add(
                InlineKeyboardButton(
                    text='Отказаться',
                    callback_data=f'not_confirmed_deal{deal_id}'
                )
            )
            await bot.send_message(
                chat_id=executor_id,
                text='✅ С вами создана сделка:\n\n'
                     f'**ID**: {deal_id}\n\n'
                     f'**Статус**: Не принята ❌\n\n'
                     f'**Описание**: {task_text}\n\n'
                     f'**Сроки**: {date}\n\n'
                     f'**Цена**: {sum}₽',
                reply_markup=confirmed_keyboard,
                parse_mode='markdown'
            )

            view_deal_keyboard = InlineKeyboardMarkup()
            view_deal_keyboard.add(
                InlineKeyboardButton(
                    text='Подробнее',
                    callback_data=f'view_deal{deal_id}')
            )

            await msg.answer(
                f'Сделка создана.\n'
                f'Условия сделки отправлены заказчику. Дождитесь '
                f'пока он примет их.\n\n',
                reply_markup=view_deal_keyboard
            )
            cur.execute(
                f'UPDATE tasks SET date_of_ending="{text}" WHERE id={deal_id}'
            )
            cur.execute(
                f'UPDATE users SET state=0 WHERE '
                f'user_id={user_id}'
            )

    con.commit()


async def callback_handler(callback_query: CallbackQuery):
    await callback_query.answer()
    text = callback_query.data
    user_id = callback_query.from_user.id

    if text == 'create_deal':
        free_tasks_count = cur.execute(
            f'SELECT free_tasks_count FROM users WHERE user_id={callback_query.from_user.id}'
        ).fetchone()[0]

        if free_tasks_count >= 1:
            await callback_query.message.edit_text(
                text='Отлично. Отправь мне условия сделки (текст ТЗ):'
            )
            cur.execute(
                f'INSERT OR IGNORE INTO tasks ('
                f'customer_id,'
                f'date_of_creation,'
                f'is_confirmed, balance'
                f') VALUES ('
                f'{user_id},'
                f'"{datetime.datetime.now().date()}",'
                f'0, 0'
                f');'
            )
            cur.execute(
                f'UPDATE users SET state=1, deal_id=0 WHERE '
                f'user_id={user_id}'
            )
        else:
            await callback_query.message.answer(
                text='Вы израсходовали все бесплатные сделки. Выберите тариф:',
                reply_markup=deals_keyboard
            )

    elif text == 'my_deals':
        deals = cur.execute(
            f'SELECT id FROM tasks WHERE customer_id={callback_query.from_user.id} OR '
            f'executor_id={callback_query.from_user.id}'
        ).fetchall()

        if deals:
            for deal in deals:
                view_deal_keyboard = InlineKeyboardMarkup()
                view_deal_keyboard.add(
                    InlineKeyboardButton(
                        text='Подробнее',
                        callback_data=f'view_deal{deal[0]}')
                )
                await callback_query.message.answer(
                    f'ID {deal[0]}',
                    reply_markup=view_deal_keyboard
                )
        else:
            await callback_query.message.answer(
                text='У вас ещё нет сделок',
                reply_markup=create_deal_keyboard
            )

    elif 'view_deal' in text:
        deal_id = int(text.split('view_deal')[1])

        date = cur.execute(
            f'SELECT date_of_ending FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]
        executor_id = cur.execute(
            f'SELECT executor_id FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]
        task_text = cur.execute(
            f'SELECT task_text FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]
        sum = cur.execute(
            f'SELECT sum FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]
        is_confirmed = cur.execute(
            f'SELECT is_confirmed FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]
        balance = cur.execute(
            f'SELECT balance FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]

        if executor_id == callback_query.from_user.id:
            keyboard = InlineKeyboardMarkup()
            if is_confirmed == 0:
                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton(
                        text='Принять сделку',
                        callback_data=f'confirmed_deal{deal_id}'
                    )
                )
                keyboard.add(
                    InlineKeyboardButton(
                        text='Отказаться',
                        callback_data=f'not_confirmed_deal{deal_id}'
                    )
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    text='Удалить',
                    callback_data=f'delete_deal{deal_id}'
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text='Оплатить',
                    callback_data=f'pay_deal{deal_id}'
                )
            )
            keyboard.add(
                InlineKeyboardButton(
                    text='Завершить',
                    callback_data=f'end_deal{deal_id}'
                )
            )

        await callback_query.message.edit_text(
            text=f'**ID**: {deal_id}\n\n'
                 f'**Статус**: `{"Не принята ❌" if is_confirmed == 0 else "Принята ✅"}`\n\n'
                 f'**Описание**: {task_text}\n\n'
                 f'**Сроки**: `{date}`\n\n'
                 f'**Цена**: `{sum}₽`\n\n'
                 f'**Внесено**: `{balance}₽`',
            parse_mode='markdown',
            reply_markup=keyboard
        )

    elif 'not_confirmed_deal' in text:
        deal_id = int(text.split('not_confirmed_deal')[1])

        deal_customer_id = cur.execute(
            f'SELECT customer_id FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]

        await bot.send_message(
            chat_id=deal_customer_id,
            text=f'**ID**: {deal_id}\n\n'
                 f'Пользователь отказал в сделке. Он сможет принять её из раздела "Мои сделки".',
            parse_mode='markdown'
        )
        await callback_query.message.edit_text(
            text=f'**ID**: {deal_id}\n\n'
                 f'Вы отказались выполнять сделку. Если передумаете - можете принять её из раздела "Мои сделки".',
            parse_mode='markdown'
        )

    elif 'confirmed_deal' in text:
        deal_id = int(text.split('confirmed_deal')[1])
        deal_customer_id = cur.execute(
            f'SELECT customer_id FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]

        view_deal_keyboard = InlineKeyboardMarkup()
        view_deal_keyboard.add(
            InlineKeyboardButton(
                text='Подробнее',
                callback_data=f'view_deal{deal_id}')
        )

        cur.execute(
            f'UPDATE tasks SET is_confirmed=1 WHERE id={deal_id}'
        )

        pay_deal_keyboard = InlineKeyboardMarkup()
        pay_deal_keyboard.add(
            InlineKeyboardButton(
                text='Оплатить сделку',
                callback_data=f'pay_deal{deal_id}'
            )
        )

        await callback_query.message.answer(
            text=f'**ID**: {deal_id}\n\n'
                 f'Вы приняли сделку. Ожидайте внесения суммы.\n\n'
                 f'Чтобы ещё раз посмотреть сделку, нажмите на "Подробнее"',
            parse_mode='markdown',
            reply_markup=view_deal_keyboard
        )

        await bot.send_message(
            chat_id=deal_customer_id,
            text=f'**ID**: {deal_id}\n\n'
                 f'Сделка принята исполнителем. Внесите сумму, указанную в сделке.\n\n'
                 f'Чтобы посмотреть сделку нажмите на "подробнее"',
            parse_mode='markdown',
            reply_markup=view_deal_keyboard
        )
        await bot.send_message(
            chat_id=deal_customer_id,
            text='Для оплаты нажмите на кнопку ниже.',
            parse_mode='markdown',
            reply_markup=pay_deal_keyboard
        )

    elif 'delete_deal' in text:
        deal_id = int(text.split('delete_deal')[1])
        is_confirmed = cur.execute(
            f'SELECT is_confirmed FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]
        if is_confirmed == 0:
            executor_id = cur.execute(
                f'SELECT executor_id FROM tasks WHERE id={deal_id}'
            ).fetchone()[0]
            cur.execute(
                f'DELETE FROM tasks WHERE id={deal_id}'
            )

            try:
                await bot.send_message(
                    chat_id=executor_id,
                    text=f'**ID**: {deal_id}\n\n'
                         f'Сделка была удалена.',
                    parse_mode='markdown'
                )
            except aiogram.utils.exceptions.ChatIdIsEmpty:
                await callback_query.message.answer(
                    text=f'**ID**: {deal_id}\n'
                         f'Мы не нашли исполнителя сделки.',
                    parse_mode='markdown'
                )

            await callback_query.message.edit_text(
                text=f'**ID**: {deal_id}\n\n'
                     f'Сделка была удалена.',
                parse_mode='markdown'
            )
        else:
            await callback_query.message.answer(
                text='Сделка принята исполнителем, вы не можете '
                     'удалить её. Но вы можете завершить сделку.\n'
                     'Чтобы сделка была завершена обе стороны должны согласиться '
                     'на завершение сделки.'
            )

    elif 'end_deal' in text:
        deal_id = int(text.split('end_deal')[1])
        executor_id, customer_id = cur.execute(
            f'SELECT executor_id, customer_id FROM tasks WHERE id={deal_id}'
        ).fetchone()

        if executor_id == callback_query.from_user.id:
            cur.execute(
                f'DELETE FROM tasks WHERE id={deal_id}'
            )
            await callback_query.message.edit_text(
                text=f'ID {deal_id}:\n\n'
                     'Сделка закрыта и удалена. '
                     'Деньги за заказ придут в течении 24х часов.\n\n'
                     'Если деньги не пришли, или возникли инные проблемы, обращайтесь в поддержку.',
                reply_markup=create_deal_keyboard
            )
            await bot.send_message(
                chat_id=customer_id,
                text=f'ID {deal_id}:\n\n'
                     f'Исполнитель подтвердил закрытие сделки.\n'
                     f'Возникли вопросы - нажимай на кнопку "помощь"',
                reply_markup=help_keyboard
            )
        else:
            end_deal_keyboard = InlineKeyboardMarkup()
            end_deal_keyboard.add(
                InlineKeyboardButton(
                    text='Завершить сделку',
                    callback_data=f'end_deal{deal_id}'
                )
            )

            await callback_query.message.edit_text(
                text=f'ID {deal_id}:\n\n'
                     'Сообщение о закрытии отправлено исполнителю сделки.\n'
                     'Сделка будет закрыта как только обе стороны согласятся.\n\n'
                     'Как только исполнитель согласится, вам придёт уведомление.',
                reply_markup=create_deal_keyboard
            )
            await bot.send_message(
                chat_id=executor_id,
                text=f'ID {deal_id}:\n\n'
                     f'Заказчик хочет завершить сделку.\n'
                     f'Вы согласны?',
                reply_markup=end_deal_keyboard
            )

    elif 'buy_deals' in text:
        deals_count = int(text.split('buy_deals')[1])
        buy_deals_keyboard = InlineKeyboardMarkup()
        buy_deals_keyboard.add(
            InlineKeyboardButton(
                url=qiwi.get_qiwi_payment_url(deals_count * 4),
                text='Оплатить'
            )
        )
        buy_deals_keyboard.add(
            InlineKeyboardButton(
                text='Проверить платёж',
                callback_data='check_payment'
            )
        )

        payment_code = qiwi.generate_payment_code(callback_query.from_user.id)

        cur.execute(
            'INSERT INTO payments ('
            'user_id, sum, payment_code, date, status, type'
            ') VALUES ('
            f'{callback_query.from_user.id},'
            f'{deals_count * 4},'
            f'{payment_code},'
            f'"{datetime.datetime.now().date()}",'
            f'0, "buy_deals"'
            f');'
        )

        await callback_query.message.edit_text(
            text=f'Покупка: `{deals_count} сделок`\n'
                 f'Цена: `{deals_count * 4}₽`\n'
                 f'Код: `{payment_code}`\n'
                 f'❗ Важно: укажите код в комментарие к платежу. Иначе оплата не пройдёт.',
            reply_markup=buy_deals_keyboard,
            parse_mode='markdown'
        )

    elif text == 'check_payment':
        payment_code, sum, payment_id, type = \
            cur.execute(f'SELECT payment_code, sum, id, type FROM payments WHERE user_id={user_id}').fetchall()[::-1][0]

        if type == 'buy_deals':
            def check_payment_global():
                for payment in qiwi.get_payment_history()['data']:
                    if str(payment_code) == str(payment['comment']) and payment['sum']['amount'] == sum:
                        return True
                return False

            if check_payment_global():
                await callback_query.message.edit_text(
                    text='Оплачено ✅\n\n'
                         'Приятного пользования!',
                    reply_markup=create_deal_keyboard
                )
                cur.execute(f'UPDATE users SET free_tasks_count={sum / 4} WHERE user_id={callback_query.from_user.id}')
                cur.execute(f'UPDATE payments SET payment_code="0" WHERE id={payment_id}')
            else:
                await callback_query.message.answer(
                    text='❌ Покупка не оплачена'
                )
        elif 'pay_deal' in type:
            deal_id = int(str(type.split('pay_deal')[1]))
            sum, executor_id = cur.execute(
                f'SELECT sum, executor_id FROM tasks WHERE id={deal_id}'
            ).fetchone()

            def check_payment_global():
                for payment in qiwi.get_payment_history()['data']:
                    if str(payment_code) == str(payment['comment']) and payment['sum']['amount'] == sum:
                        return True
                return False

            if check_payment_global():
                cur.execute(f'UPDATE tasks SET balance={sum} WHERE id={deal_id}')
                cur.execute(f'UPDATE payments SET payment_code="0" WHERE id={payment_id}')
                con.commit()

                await callback_query.message.edit_text(
                    text=f'ID {deal_id}:\n\n'
                         f'Сделка оплачена.\n'
                         'Исполнителю отправлен чек и информация об оплате.',
                    reply_markup=create_deal_keyboard
                )
                await callback_query.message.answer(
                    text=f'ЧЕК СДЕЛКА №{deal_id}\n\n'
                         f'📅 Дата оплаты: {datetime.datetime.now().date()}`\n'
                         f'🕛 Время оплаты: {datetime.datetime.now().time()}`\n'
                         f'👛 Сумма оплаты: {sum}₽`\n'
                         f'💻 Код платежа: {payment_code}`\n'
                         f'🔑 ID исполнителя: {executor_id}`\n'
                         f'🔑 ID заказчика: {callback_query.from_user.id}`',
                    parse_mode='markdown'
                )

                view_deal_keyboard = InlineKeyboardMarkup()
                view_deal_keyboard.add(
                    InlineKeyboardButton(
                        text='Подробнее',
                        callback_data=f'view_deal{deal_id}')
                )

                await bot.send_message(
                    chat_id=executor_id,
                    text=f'ID {deal_id}:\n\n'
                         f'Заказчик оплатил сделку. '
                         f'Можете приступать к работе.',
                    reply_markup=view_deal_keyboard
                )
                await bot.send_message(
                    chat_id=executor_id,
                    text=f'ЧЕК СДЕЛКА №{deal_id}\n\n'
                         f'📅 Дата оплаты: {datetime.datetime.now().date()}`\n'
                         f'🕛 Время оплаты: {datetime.datetime.now().time()}\n'
                         f'👛 Сумма оплаты: {sum}`₽\n'
                         f'💻 Код платежа: {payment_code}`\n'
                         f'🔑 ID исполнителя: {executor_id}`\n'
                         f'🔑 ID заказчика: {callback_query.from_user.id}`'
                )
            else:
                await callback_query.message.answer(
                    text='❌ Покупка не оплачена'
                )

    elif 'pay_deal' in text:
        deal_id = int(str(text.split('pay_deal')[1]))
        sum = cur.execute(
            f'SELECT sum FROM tasks WHERE id={deal_id}'
        ).fetchone()[0]

        buy_deals_keyboard = InlineKeyboardMarkup()
        buy_deals_keyboard.add(
            InlineKeyboardButton(
                url=qiwi.get_qiwi_payment_url(sum),
                text='Оплатить'
            )
        )
        buy_deals_keyboard.add(
            InlineKeyboardButton(
                text='Проверить платёж',
                callback_data='check_payment'
            )
        )

        payment_code = qiwi.generate_payment_code(callback_query.from_user.id)

        cur.execute(
            'INSERT INTO payments ('
            'user_id, sum, payment_code, date, status, type'
            ') VALUES ('
            f'{callback_query.from_user.id},'
            f'{sum},'
            f'{payment_code},'
            f'"{datetime.datetime.now().date()}",'
            f'0, "pay_deal{deal_id}"'
            f');'
        )

        await callback_query.message.edit_text(
            text=f'Оплата: `сделка №{deal_id}`\n'
                 f'Цена: `{sum}₽`\n'
                 f'Код: `{payment_code}`\n'
                 f'❗ Важно: укажите код в комментарие к платежу. Иначе оплата не пройдёт.',
            reply_markup=buy_deals_keyboard,
            parse_mode='markdown'
        )

    con.commit()
