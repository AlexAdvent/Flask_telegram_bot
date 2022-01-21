from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from chat_bot.database import db, bucket

# RULES
RULES = '''ITS AI Bot allows you to publish text, images and videos on your screen.

/Add_Screen - add a screen to your account
/Playlist - view your playlists and content
/Screens - view your added screens
/My_Account - view your account details

Note:- use 'text YourText' to create text widget with a space between them.
'''

welcome_text = '''Hi. I'm ITS AI Bot.
Turn any screen into digital signage capable of displaying texts, images & videos conveniently from your phone.🚀
Check it out at ITS.ai'''

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
itembtna = types.KeyboardButton('🤔 Help')
itembtnb = types.KeyboardButton('🔌 Add Screen')
itembtnc = types.KeyboardButton('👌 Playlist')
itembtnd = types.KeyboardButton('📺 Screens')
itembtne = types.KeyboardButton('🤝 Paid services')
itembtnf = types.KeyboardButton('💼 My Account')
itembtng = types.KeyboardButton('⚡ My Subscriptions')
itembtnh = types.KeyboardButton('🇸🇦 Language')
markup.row(itembtna, itembtnb)
markup.row(itembtnd, itembtnc, itembtnf)
markup.row(itembtnh)

markup_language = types.ReplyKeyboardMarkup(resize_keyboard=True)
itembtnx = types.KeyboardButton('English')
markup_language.row(itembtnx)


def checker(bot, message):
    doc_ref = db.collection(u'users').document(str(message.chat.id))
    data1 = doc_ref.get()
    data = doc_ref.get().to_dict()
    if not data1.exists:
        if message.text == "English":
            language = 'English'
            if language == 'English':
                bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
            doc_ref.set({
                u'chat_id': message.chat.id,
                u'first_name': None,
                u'email': None,
                u'phone_number': None,
                u'organization_name': None,
                u'language': language,
                u'subscription': {'free':
                    {
                        'screen': 1,
                        'expiryDate': datetime.now() + timedelta(days=30),
                        'startingDate': datetime.now(),
                        "type": 'monthly',
                        'storage': 20
                    }
                },
                u'screen': {},
                u'playlist': {},
                u'total_screen': 0,
                u'active_screen': 'all',
                u'activation': True,
                u'size': 0,
                u'activation_message': 0,
            })
            force_reply = types.ForceReply(selective=False)
            if language == 'English':
                bot.send_message(message.chat.id, 'Please enter your name', reply_markup=force_reply)
            return 0
        else:
            bot.send_message(message.chat.id, 'Choose a language', reply_markup=markup_language)
            return 0
        # force_reply = types.ForceReply(selective=False)
        # bot.send_message(message.chat.id, 'Please enter your name (English)', reply_markup=force_reply)
        # return
    elif data['first_name'] is None:
        force_reply = types.ForceReply(selective=False)
        if data['language'] == 'English':
            bot.send_message(message.chat.id, 'Please enter your name', reply_markup=force_reply)
        return 0
    elif data['phone_number'] is None:
        force_reply = types.ForceReply(selective=False)
        if data['language'] == 'English':
            bot.send_message(message.chat.id, 'Please enter your mobile number', reply_markup=force_reply)
        return 0

    elif data['email'] is None:
        force_reply = types.ForceReply(selective=False)
        if data['language'] == 'English':
            bot.send_message(message.chat.id, 'Please enter your email address', reply_markup=force_reply)
        return 0

    elif data['organization_name'] is None:
        force_reply = types.ForceReply(selective=False)
        if data['language'] == 'English':
            bot.send_message(message.chat.id, 'Please enter your organization name', reply_markup=force_reply)

        return 0
    elif not data['activation']:
        if data['activation_message'] == 0:
            doc_ref.update({'activation_message': 1})
        if data['language'] == 'English':
            message_array = ["We will contact you with the details you provided, thank you for your patience.",
                             "Thanks for your patience, we will be in touch soon."]

            bot.send_message(message.chat.id, message_array[data['activation_message']])
        return 0
    return data


def gen_markup(doc, file_id, display_type=None):
    print(file_id)
    alternate_option = ''
    if display_type == 'fullscreen':
        alternate_option = 'Deactivate fullscreen'
    elif display_type == 'framed':
        alternate_option = 'Activate fullscreen'
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    if display_type:
        if doc['language'] == 'English':
            markup.add(InlineKeyboardButton("Remove", callback_data=f'remove_media#{file_id}'),
                       InlineKeyboardButton(f"{alternate_option}",
                                            callback_data=f'change_display_type#{file_id}'))
    else:
        if doc['language'] == 'English':
            markup.add(InlineKeyboardButton("Delete", callback_data=f'remove_text#{file_id}'))
    return markup


def get_used_storage(doc):
    storage_used = 0
    for display in doc['playlist']:
        for file in doc['playlist'][display]:
            if doc['playlist'][display][file]['type'] != 'text':
                storage_used += doc['playlist'][display][file]['size']
    return storage_used


def get_total_screen(doc):
    total_sub = 0
    print(f'Document data: {doc}')
    ispaid = 0
    isfree = 0
    all_sub = doc["subscription"]
    for sub in doc['subscription']:
        print("sub", sub)
        if sub == 'paid':
            if doc['subscription'][sub]['expiryDate'] >= datetime.now(
                    doc['subscription'][sub]['expiryDate'].tzinfo):
                ispaid = all_sub[sub]['screen']
                # sub = ""
        elif sub == 'free':
            if doc['subscription'][sub]['expiryDate'] >= datetime.now(
                    doc['subscription'][sub]['expiryDate'].tzinfo):
                # sub = ""
                isfree = all_sub[sub]['screen']
        print(isfree, ispaid)
    if ispaid:
        return ispaid, ispaid
    elif isfree:
        return isfree, ispaid
    else:
        return 0, ispaid


def get_total_storage(doc):
    total_storage = 0
    print(f'Document data: {doc}')
    sub = doc["subscription"]
    # for i in sub:
    # if i == 'free':
    #     total_sub += 1

    # print(sub[i]['expiryDate'] >= datetime.now(sub[i]['expiryDate'].tzinfo))
    # print(sub[i]['expiryDate'] , datetime.now(sub[i]['expiryDate'].tzinfo))
    # if sub[i]['expiryDate'] >= datetime.now(sub[i]['expiryDate'].tzinfo):
    #     total_storage += sub[i]['storage']
    # print(i, total_sub)
    total_sub, ispaid = get_total_screen(doc)
    if total_sub:
        if ispaid:
            total_storage = sub['paid']['storage']
        else:
            total_storage = sub['free']['storage']
    else:
        total_storage = 0
    return total_storage


def gen_markup_s(doc, data):
    print(data)
    screen_type = doc['screen'][data]['type']
    screen_orientation = 'Vertical' if screen_type == 'landscape' else 'Horizontal'
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if doc['language'] == 'English':
        markup.add(InlineKeyboardButton("Select", callback_data=f'activate_screen#{data}'),
                   InlineKeyboardButton("Remove", callback_data=f'remove_screen#{data}'))
        markup.add(InlineKeyboardButton(screen_orientation, callback_data=f'rotate_screen#{data}'))
    return markup


def gen_markup_all(doc, data):
    print(data)
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if doc['language'] == 'English':
        markup.add(InlineKeyboardButton("Select", callback_data=f'activate_all_screen#all'))
    return markup


def language(bot, message):
    bot.send_message(message.chat.id, 'Choose a language', reply_markup=lang_markup(message))


def lang_markup(data):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("English/إنجليزي", callback_data='change_language#English'))
    return markup