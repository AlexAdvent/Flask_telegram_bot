import random
import re
import os

import requests
from firebase_admin import firestore
from google.cloud.firestore_v1 import Increment
from telebot import TeleBot
from chat_bot.telegram_bot.utility import RULES, welcome_text, markup, markup_language, checker, gen_markup, get_used_storage, get_total_storage, get_total_screen, gen_markup_s, gen_markup_all, language, lang_markup
from chat_bot.database import db, bucket

API_TOKEN = os.environ['API_TOKEN_BOT']
bot = TeleBot(API_TOKEN)


@bot.message_handler(commands=['Add_Screen'])
def pair(message):
    doc = checker(bot, message)
    if doc:
        if doc['language'] == 'English':
            bot.send_message(message.chat.id,
                             "Please enter the 5 digit code and name with space between them. \nExample:- 11119 office",
                             reply_markup=markup)


# Handles 'start' command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    doc = checker(bot, message)
    if doc:
        if doc['language'] == 'English':
            bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


def check_screen(message, doc):
    total_screen, ispaid = get_total_screen(doc)
    if total_screen >= doc['total_screen']:
        return 1
    else:
        bot.send_message(message.chat.id,
                         f"Your active screen {doc['total_screen']} is more than subscription screen {total_screen}.\nplease upgrade your subscription or remove screen")


# Handle '/help' command
@bot.message_handler(commands=['help'])
def send_help(message):
    print("message", message)
    doc = checker(bot, message)
    if doc:
        if doc['language'] == 'English':
            bot.send_message(message.chat.id, RULES, reply_markup=markup)


@bot.message_handler(commands=['Playlist'])
def send_image(message):
    doc = checker(bot, message)
    if doc:
        # print(f'Document data: {doc.to_dict()}')
        # doc = doc_ref.get().to_dict()
        playlist = doc["playlist"]
        data = str(doc['active_screen'])
        screen_name = doc["screen"][data]["name"] if not data == 'all' else 'all'
        if doc['language'] == 'English':
            bot.send_message(message.chat.id, f'Playlist for the selected screen : {screen_name}', reply_markup=markup)
        if data not in playlist or len(playlist[data]) == 0:
            if doc['language'] == 'English':
                bot.send_message(message.chat.id, 'The playlist is empty 🙌️', reply_markup=markup)
        else:
            if doc['language'] == 'English':
                bot.send_message(message.chat.id, '------ Start of Playlist ------')
            for file_info in playlist[data]:
                file_id = playlist[data][str(file_info)]["file_id"]
                print(file_info)
                if playlist[data][str(file_info)]["type"] == "photo":
                    display_type = playlist[data][str(file_info)]["display_type"]
                    bot.send_photo(message.chat.id, file_id,
                                   reply_markup=gen_markup(doc, f"{data}#{str(file_info)}.jpg",
                                                           display_type=display_type))
                elif playlist[data][str(file_info)]["type"] == "video":
                    display_type = playlist[data][str(file_info)]["display_type"]
                    bot.send_video(message.chat.id, file_id,
                                   reply_markup=gen_markup(doc, f"{data}#{str(file_info)}.mp4",
                                                           display_type=display_type))
                elif playlist[data][str(file_info)]["type"] == "animation":
                    display_type = playlist[data][str(file_info)]["display_type"]
                    bot.send_animation(message.chat.id, file_id,
                                       reply_markup=gen_markup(doc, f"{data}#{str(file_info)}.gif",
                                                               display_type=display_type))
                elif playlist[data][str(file_info)]["type"] == "text":
                    bot.send_message(message.chat.id, playlist[data][str(file_info)]["public_url"],
                                     reply_markup=gen_markup(doc, f"{data}#{str(file_info)}"))
            if doc['language'] == 'English':
                bot.send_message(message.chat.id, '------ End of Playlist ------', reply_markup=markup)
        # else:
        #     print(u'No such document!')
        #     bot.send_message(message.chat.id, ' Error retrieving Document')


# For delete button in playlist



# send to new file


# For deleting file from playlist
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print("call", call)
    text = call.data.split("#")[0]
    data = call.data.split("#")[1]
    if text == 'remove_screen':
        doc_ref = db.collection(u'users').document(str(call.from_user.id))
        doc = doc_ref.get().to_dict()
        if data in doc['screen']:
            try:
                for i in doc['playlist']:
                    if i == data:
                        # blob = bucket.blob(f'{call.from_user.id}/{str(i)}/')
                        # blob.delete()
                        bucket.delete_blobs(blobs=list(bucket.list_blobs(prefix=f'{call.from_user.id}/{str(i)}/')))
                        doc_ref.update({
                            f'playlist.{data}': firestore.DELETE_FIELD
                        })

                if doc['active_screen'] == str(data):
                    doc_ref.update({'active_screen': 'all'})

                doc_ref.update({
                    u'screen.' + str(data): firestore.DELETE_FIELD
                })
                doc_ref = db.collection(u'pin').document(str(data))
                doc_ref.update({'username': None})
                doc_ref = db.collection(u'users').document(str(call.from_user.id))
                total_screen = doc_ref.get().to_dict()['total_screen'] - 1
                doc_ref.update({'total_screen': total_screen})
                if doc['language'] == 'English':
                    bot.send_message(call.from_user.id, 'Removed successfully', reply_markup=markup)
            except Exception as e:
                print(e)
                if doc['language'] == 'English':
                    bot.send_message(call.from_user.id, "Couldn't remove, please try again", reply_markup=markup)

        else:
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, 'Not paired with this screen', reply_markup=markup)
    # Activate Screen
    elif text == 'activate_screen':
        doc_ref = db.collection(u'pin').document(str(data))
        doc = doc_ref.get().to_dict()
        print(doc['username'], call.from_user.id)
        if doc['username'] == str(call.from_user.id):
            doc_ref = db.collection(u'users').document(str(call.from_user.id))
            doc = doc_ref.get().to_dict()
            doc_ref.update({'active_screen': data})
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, 'Selected successfully', reply_markup=markup)
        else:
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, 'Not paired with this screen', reply_markup=markup)

    elif text == 'rotate_screen':
        doc_ref = db.collection(u'pin').document(str(data))
        doc = doc_ref.get().to_dict()
        if doc['username'] == str(call.from_user.id):
            doc_ref = db.collection(u'users').document(str(call.from_user.id))
            doc = doc_ref.get().to_dict()
            rotated_screen = 'portrait' if doc['screen'][data]['type'] == 'landscape' else 'landscape'
            doc_ref.update({'screen.' + data + '.type': rotated_screen})
            screen_type = 'vertical' if rotated_screen == 'portrait' else 'horizontal'
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, f'Screen rotated to {screen_type}', reply_markup=markup)
        else:
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, 'Not paired with this screen', reply_markup=markup)

    elif text == 'change_display_type':
        # doc_ref = db.collection(u'pin').document(str(data))
        # doc = doc_ref.get().to_dict()
        # if doc['username'] == str(call.from_user.id):
        doc_ref = db.collection(u'users').document(str(call.from_user.id))
        doc = doc_ref.get().to_dict()
        file = call.data.split("#")[2]
        print(data, 'data', doc, 'text', text)
        display_type = 'fullscreen' if doc['playlist'][data][file.split(".")[0]][
                                           'display_type'] == 'framed' else 'framed'
        doc_ref.update({f'playlist.{data}.{file.split(".")[0]}.display_type': display_type})
        if display_type == 'fullscreen':
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, f'Media changed to {display_type}', reply_markup=markup)
        elif display_type == 'framed':
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, f'Media ended from fullscreen', reply_markup=markup)
    # else:
    #     bot.send_message(call.from_user.id, 'Not paired with this screen')

    elif text == 'activate_all_screen':
        doc_ref = db.collection(u'users').document(str(call.from_user.id))
        doc = doc_ref.get().to_dict()
        doc_ref.update({'active_screen': data})
        if doc['language'] == 'English':
            bot.send_message(call.from_user.id, 'Selected successfully', reply_markup=markup)

    # Delete in Playlist text
    elif text == 'remove_text':
        print("In text")
        pin = call.data.split("#")[1]
        file = call.data.split("#")[2]
        print(pin, file)
        doc_ref = db.collection(u'users').document(str(call.from_user.id))
        doc = doc_ref.get().to_dict()
        try:
            if file in doc['playlist'][pin]:
                doc_ref.update({
                    f'playlist.{str(pin)}.' + str(file): firestore.DELETE_FIELD
                })
                if doc['language'] == 'English':
                    bot.send_message(call.from_user.id, 'Removed successfully', reply_markup=markup)
            else:
                if doc['language'] == 'English':
                    bot.send_message(call.from_user.id, 'Does not exist', reply_markup=markup)
        except:
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, 'Deletion unsuccessful, please try again', reply_markup=markup)
    # Delete button in playlist
    elif text == 'remove_media':
        print(call)
        doc_ref = db.collection(u'users').document(str(call.from_user.id))
        doc = doc_ref.get().to_dict()
        pin = call.data.split("#")[1]
        file = call.data.split("#")[2]
        # file_size = doc['playlist'][pin][file.split(".")[0]]['size']
        # print(file_size)
        if file.split(".")[0] in doc['playlist'][pin]:
            blob = bucket.blob(f'{call.from_user.id}/{pin}/{file}')
            blob.delete()

            # if blob.exists:
            #     bot.send_message(call.from_user.id, 'Deletion failed, please try again')
            # else:
            # doc_ref.update({f'playlist.{sc_pin}.' + str(file_unique_id): {

            try:
                # print(doc['size'] - file_size)
                # doc_ref.update({f'size': doc['size'] - file_size})
                doc_ref.update({
                    f'playlist.{pin}.' + str(file.split(".")[0]): firestore.DELETE_FIELD

                })
                if doc['language'] == 'English':
                    bot.send_message(call.from_user.id, 'Removed successfully', reply_markup=markup)
            except:
                if doc['language'] == 'English':
                    bot.send_message(call.from_user.id, 'Deletion unsuccessful, please try again')
        else:
            if doc['language'] == 'English':
                bot.send_message(call.from_user.id, 'Does not exist', reply_markup=markup)

    elif text == 'change_language':
        doc_ref = db.collection(u'users').document(str(call.from_user.id))
        try:
            doc_ref.update({'language': data})
            if data == 'English':
                bot.send_message(call.from_user.id, f'Language changed to {data}', reply_markup=markup)
        except:
            bot.send_message(call.from_user.id, 'Unexpected error occurred, please try again')

        # bot.edit_message_media(media=call.message.json.photo[0].file_id, chat_id=call.from_user.id, message_id=call.message.message_id)
    bot.edit_message_reply_markup(call.from_user.id, call.message.message_id)
    return


# Handles all files
@bot.message_handler(content_types=['video', 'photo', 'animation'])
def handle_docs(message):
    active_screen = None
    data = checker(bot, message)
    if data:
        if check_screen(message, data):
            active_screen = data['active_screen']
            print(active_screen)
            print("message", message)
            if message.content_type == 'video':
                file = message.video.file_id
                extension = "mp4"
                print(message.json[message.content_type]['file_size'])
                file_size = message.json[message.content_type]['file_size']
            elif message.content_type == 'photo':
                file = message.photo[-1].file_id
                extension = "jpg"
                print(message.json[message.content_type][-1]['file_size'])
                file_size = message.json[message.content_type][-1]['file_size']
            elif message.content_type == 'animation':
                file = message.animation.file_id
                extension = "gif"
                print(message.json[message.content_type]['file_size'])
                file_size = message.json[message.content_type]['file_size']
            else:
                bot.send_message(message.chat.id, RULES)
            file_info = bot.get_file(file)
            print("file_info", file_info)
            print(file_info.file_path)
            file_url = 'https://api.telegram.org/file/bot{0}/{1}'.format(API_TOKEN, file_info.file_path)
            file_data = requests.get(file_url).content
            # extension = file_info.file_path.split(".")[-1]
            file_unique_id = file_info.file_unique_id + str(random.randint(11111, 99999))
            file_unique_id = file_unique_id.replace('-', '5')
            print(file_unique_id)
            # print(message.json[message.content_type][-1]['file_size'])
            # file_size = round(message.json[message.content_type][-1]['file_size']/1048576, 2)
            total_size = file_size + get_used_storage(data)
            doc_ref = db.collection(u'users').document(str(message.chat.id))
            doc = doc_ref.get().to_dict()
            db_storage = get_total_storage(doc)
            if db_storage * 1024 * 1024 > total_size:
                print(file_size)
                blob = bucket.blob(f'{message.chat.id}/{active_screen}/{file_unique_id}.{extension}')
                blob.upload_from_string(
                    file_data,
                    content_type=f'{message.content_type}/{extension}'
                )
                print(blob.exists())
                if blob.exists():
                    # doc_ref = db.collection(u'users').document(str(message.chat.id))

                    # doc_ref.update({u'playlist.' + str(file_unique_id): {
                    #     'file_id': file_info.file_id, 'file_unique_id': file_unique_id, "type": f'{message.content_type}'}})

                    print(blob.public_url)
                    public_url = blob.public_url
                    # public_url = blob.generate_signed_url(expiration=endDate)
                    doc_ref = db.collection(u'users').document(str(message.chat.id))
                    try:
                        # doc_ref.update({'size': total_size})
                        doc_ref.update({f'playlist.{active_screen}.' + str(file_unique_id): {
                            'public_url': public_url,
                            'file_id': file_info.file_id,
                            'file_unique_id': file_unique_id,
                            "type": f'{message.content_type}',
                            'size': file_size,
                            'display_type': 'fullscreen'
                        }})
                        screen = 'all' if active_screen == 'all' else doc['screen'][active_screen]['name']
                        if data['language'] == 'English':
                            bot.send_message(message.chat.id,
                                             f'Your {message.content_type} has been published to {screen} !✨',
                                             reply_markup=markup)


                    except Exception as e:
                        print(e)
                        blob.delete()
                        if data['language'] == 'English':
                            bot.send_message(message.chat.id, 'Upload was unsuccessful, please try again')

                else:
                    if data['language'] == 'English':
                        bot.send_message(message.chat.id, 'Upload was unsuccessful, please try again')
            else:
                if data['language'] == 'English':
                    bot.send_message(message.chat.id, 'The assigned storage limit has been reached')





# @bot.message_handler(commands=['My_Subscription'])
# def my_sub(message):
#     data = checker(bot, message)
#     if data:
#         print('message1', message)
#         total_sub, ispaid = get_total_screen(data)
#         if total_sub:
#             if ispaid:
#                 if data['language'] == 'English':
#                     bot.send_message(message.chat.id,
#                                      f"You have currently subscribed to {total_sub} screens till {data['subscription']['paid']['expiryDate'].strftime('%d/%m/%y')}",
#                                      reply_markup=markup)
#
#             else:
#                 if data['language'] == 'English':
#                     bot.send_message(message.chat.id,
#                                      f"You have currently subscribed to {total_sub} free screen till {data['subscription']['free']['expiryDate'].strftime('%d/%m/%y')}",
#                                      reply_markup=markup)
#         else:
#             if data['language'] == 'English':
#                 bot.send_message(message.chat.id, f'You are not subscribe to any subscription',
#                                  reply_markup=markup)





# def get_total_screen(message, doc):
#     total_sub = 0
#     print(f'Document data: {doc}')
#     sub = doc["subscription"]
#     for i in sub:
#         # if i == 'free':
#         #     total_sub += 1
#
#         # print(sub[i]['expiryDate'] >= datetime.now(sub[i]['expiryDate'].tzinfo))
#         # print(sub[i]['expiryDate'] , datetime.now(sub[i]['expiryDate'].tzinfo))
#         if sub[i]['expiryDate'] >= datetime.now(sub[i]['expiryDate'].tzinfo) and sub[i]['startDate'] <= datetime.now(sub[i]['startDate'].tzinfo):
#             total_sub1 = sub[i]['screen']
#             total_sub += total_sub1
#             # print(i, total_sub)
#     return total_sub





@bot.message_handler(commands=['Screens'])
def active_screens(message):
    doc = checker(bot, message)
    if doc:
        print(f'Document data: {doc}')
        screen = doc["screen"]
        print(screen)
        if len(screen) == 0:
            if doc['language'] == 'English':
                bot.send_message(message.chat.id,
                                 'You are not paired with any screens, please add a screen (/Add_Screen)',
                                 reply_markup=markup)
        else:
            for i in screen:
                print(i)
                screen_type = screen[i]["type"]
                screen_orientation = 'Horizontal' if screen_type == 'landscape' else 'Vertical'
                # if playlist[str(file_info)]["type"] == "photo":
                if doc['language'] == 'English':
                    bot.send_message(message.chat.id, f'{screen[i]["name"]} - {screen_orientation}',
                                     reply_markup=gen_markup_s(doc, str(i)))
            if doc['language'] == 'English':
                bot.send_message(message.chat.id, '''
~~~~~~~~~~~~~~~~~~~~~
                Select All
~~~~~~~~~~~~~~~~~~~~~
                    ''', reply_markup=gen_markup_all(doc, 'all'))


@bot.message_handler(commands=['My_Account'])
def my_acc(message):
    doc = checker(bot, message)
    if doc:
        print(f'Document data: {doc}')
        name = doc["first_name"]
        active_screen = doc["total_screen"]
        sub, ispaid = get_total_screen(doc)
        screen = 'all' if doc['active_screen'] == 'all' else doc['screen'][doc['active_screen']]['name']
        expiredate = doc['subscription']['paid']['expiryDate'].strftime('%d/%m/%y') if ispaid else \
            doc['subscription']['free']['expiryDate'].strftime('%d/%m/%y')
        if doc['language'] == 'English':
            details = f'''{name},
=> You have currently subscribed to [{sub}] number of screens until {expiredate}.

=> You currently have [{active_screen}] active screens.

=> Your current selected screen is {screen}.
            '''
            bot.send_message(message.chat.id, details, reply_markup=markup)





@bot.message_handler(func=lambda message: True)
def echo_message(message):
    print(message.json)
    print(type(message))
    if message.reply_to_message is not None:
        if message.reply_to_message.json['text'] == 'Please enter your name':
            name = message.text
            print(name)
            doc_ref = db.collection(u'users').document(str(message.chat.id))
            doc_ref.update({u'first_name': name})
            checker(bot, message)
            # force_reply = types.ForceReply(selective=False)
            # bot.send_message(message.chat.id, 'PLease enter your phone number', reply_markup=force_reply)

        elif message.reply_to_message.json['text'] == 'Please enter your mobile number':
            ph_no = message.text
            regex = r'\b[0-9]{10}\b'
            if re.fullmatch(regex, ph_no):
                print(ph_no)
                doc_ref = db.collection(u'users').document(str(message.chat.id))
                doc_ref.update({u'phone_number': ph_no})
                checker(bot, message)
                # force_reply = types.ForceReply(selective=False)
                # bot.send_message(message.chat.id, 'PLease enter your email', reply_markup=force_reply)
            else:
                if message.reply_to_message.json['text'] == 'Please enter your mobile number':
                    bot.send_message(message.chat.id, 'Not a valid mobile number.')
                checker(bot, message)


        elif message.reply_to_message.json['text'] == 'Please enter your email address':
            email = message.text
            regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if re.fullmatch(regex, email):
                print(email)
                doc_ref = db.collection(u'users').document(str(message.chat.id))
                doc_ref.update({u'email': email})
                checker(bot, message)
            else:
                if message.reply_to_message.json['text'] == 'Please enter your email address':
                    bot.send_message(message.chat.id, 'Not a valid email address.')
                checker(bot, message)
            # send_help(message)

        elif message.reply_to_message.json['text'] == 'Please enter your organization name':
            organization_name = message.text
            print(organization_name)
            doc_ref = db.collection(u'users').document(str(message.chat.id))

            doc_ref.update({u'organization_name': organization_name, 'activation': False})
            # checker(bot, message)
            subject = 'New user registration ITSAIBot'
            data = doc_ref.get().to_dict()
            details = f'''
                    Name : {data['first_name']}
                    Account : {message.chat.id}
                    Mobile No. : {data['phone_number']}
                    Email : {data['email']}
                    Organization : {data['organization_name']}'''
            # content = 'Subject: {}\n\n{}'.format(subject, details)

            if message.reply_to_message.json['text'] == 'Please enter your organization name':
                bot.send_message(message.chat.id,
                                 "Thank you, we'll be in touch within three business day to walk you through how to use the IT'S AI app.")
            # send_email(details, subject)

    else:
        doc_users = checker(bot, message)
        if doc_users:
            if message.text == '🤔 Help':
                send_help(message)
            elif message.text == '👌 Playlist':
                send_image(message)
            elif message.text == '📺 Screens':
                active_screens(message)
            # elif message.text == '🤝 Subscriptions' or message.text == '🤝  الاشتراكات':
            #     paid_services(message)
            elif message.text == '💼 My Account':
                my_acc(message)
            # elif message.text == '⚡ My Subscriptions' or message.text == '⚡️اشتراكاتي':
            #     my_sub(message)
            elif message.text == '🔌 Add Screen':
                pair(message)
            elif message.text == '🇸🇦 Language':
                language(bot, message)
            elif message.text == 'Start':
                send_welcome(message)



            elif message.text.split(' ')[0].isdigit() and len(
                    message.text.split(' ')[0]) == 5 and len(message.text.split(' ')) > 1:
                pin = str(message.text.split(' ')[0])
                doc_ref = db.collection(u'pin').document(pin)
                doc = doc_ref.get().to_dict()
                print(doc)
                if doc_ref.get().to_dict() == None:
                    if doc_users['language'] == 'English':
                        bot.send_message(message.chat.id, 'Please enter a valid pin')

                elif doc['username'] == None:
                    total_screen, ispaid = get_total_screen(doc_users)
                    if total_screen > doc_users['total_screen']:
                        doc_ref.update({'username': str(message.chat.id)})
                        doc_ref = db.collection(u'users').document(str(message.chat.id))
                        doc_ref.update({
                            u'screen.' + pin: {
                                'pin': pin,
                                'name': message.text.split(' ', 1)[1],
                                'type': 'landscape'
                            }})
                        # doc_ref.set({'pin': 11111})
                        doc_ref.update({u'total_screen': Increment(1)})
                        if doc_users['language'] == 'English':
                            bot.send_message(message.chat.id, 'Screen added successfully', reply_markup=markup)
                        if doc_users['language'] == 'English':
                            bot.send_message(message.chat.id,
                                             "Screen limit reached, please remove a screen or purchase subscription.",
                                             reply_markup=markup)
                elif doc_ref.get().to_dict()['username']:
                    if doc_users['language'] == 'English':
                        bot.send_message(message.chat.id, 'Code already in use.', reply_markup=markup)
            elif message.text.split(' ')[0] == "text" and len(message.text.split(' ')) > 1:
                if check_screen(message, doc_users):
                    active_screen = doc_users['active_screen']
                    send_screen = doc_users["screen"][active_screen]["name"] if active_screen != 'all' else 'all'
                    doc_ref = db.collection(u'users').document(str(message.chat.id))
                    try:
                        doc_ref.update({f'playlist.{active_screen}.' + str(message.message_id): {
                            'public_url': message.text.split(' ', 1)[-1],
                            'file_id': str(message.message_id),
                            'file_unique_id': str(message.message_id),
                            "type": f'{message.content_type}'
                        }})
                        if doc_users['language'] == 'English':
                            bot.send_message(message.chat.id,
                                             f'Your {message.content_type} has been published to {send_screen}!✨',
                                             reply_markup=markup)

                    except:
                        if doc_users['language'] == 'English':
                            bot.send_message(message.chat.id, 'Upload was unsuccessful, please try again')
            else:
                send_help(message)


