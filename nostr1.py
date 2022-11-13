#needs rclone set up with dropbox, running
import os
import ssl
import time
import json
import messages
import nostr
import payment
from nostr.relay_manager import RelayManager
from nostr.key import generate_private_key, get_public_key, decrypt_message, compute_shared_secret, encrypt_message
from nostr.filter import Filter, Filters
from nostr.event import Event, EventKind
from nostr.message_type import ClientMessageType
from dotenv import load_dotenv
import dalle2
import midjourney
import logging
from rclone.rclone import Rclone
import stablediffusion

rc = Rclone()

logging.basicConfig(
    filename="mylog.txt",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()
private_key = os.environ['nostr_pk']
public_key = get_public_key(private_key)
subscription_id = str(int(time.time()))
filters_pm = Filter(limit=0, kinds=[4], tags={'#p': [public_key]})
filters_gc = Filter(limit=0, kinds=[42], tags={"#e": [os.environ['nostr_chat_id']]})
filters = Filters([filters_pm, filters_gc])
relay_manager = RelayManager()

def connect():
    count = 0
    try:
        relay_manager.add_relay("wss://nostr-pub.wellorder.net")
        relay_manager.add_relay("wss://relay.damus.io")
        relay_manager.add_subscription(subscription_id, filters)
        relay_manager.open_connections({"cert_reqs": ssl.CERT_NONE})
        time.sleep(1.25)
    except:
        time.sleep(5)
        count += 1
        print("connecting failed " + str(count) + " times!")
        connect()
def nostr_dalle():
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())
    message = json.dumps(request)
    user_state_nostr = {}
    current_prompt = ""
    while True:
        try:
            relay_manager.publish_message(message)
            time.sleep(1.25)
            event_msg = relay_manager.message_pool.get_event()
            if event_msg.event.kind == 42:
                if event_msg.event.content[0:3] == "/p ":
                    connect()
                    current_prompt = event_msg.event.content[3:]
                    user_state_nostr[current_prompt] = payment.getinvoice()
                    event = Event(public_key, str("https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" +
                                                  user_state_nostr[current_prompt]['payment_request'] + "&format=.png" +
                                                  " " +
                                                  str(user_state_nostr[current_prompt]['payment_request'])), kind=42,
                                  tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(2)  # allow the messages to send
                    event = Event(public_key, "Send /gd (DALLE2) or /gsd (Stable Diffusion) or /gmj (Midjourney like, experimental) once you paid the invoice to start generating", kind=42,
                                  tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(1)  # allow the messages to send
                elif event_msg.event.content == "/start":
                    time.sleep(1)
                    event = Event(public_key, messages.start_nostr, kind=42,
                                  tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(1)  # allow the messages to send
                elif event_msg.event.content == "/gd":
                    if payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']):
                        event = Event(public_key,
                                      "Generating images, this can take a minute...",
                                      kind=42,
                                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                        dalle_generate(current_prompt, 42, None)
                        current_prompt = ""
                    elif payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']) != True:
                        event = Event(public_key, "You havent paid yet, send /gd again once you paid or give a new prompt with /p", kind=42,
                                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                elif event_msg.event.content == "/gsd":
                    if payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']):
                        event = Event(public_key,
                                      "Generating images, this can take a minute...",
                                      kind=42,
                                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                        sd_generate(current_prompt, 42, None)
                        current_prompt = ""
                    elif payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']) != True:
                        event = Event(public_key,
                                      "You havent paid yet, send /gsd again once you paid or give a new prompt with /p",
                                      kind=42,
                                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                elif event_msg.event.content == "/gmj":
                    if payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']):
                        event = Event(public_key,
                                      "Generating images, this can take a minute...  Pictures are black if the AI interprets them as NSFW",
                                      kind=42,
                                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                        nostr_midjourney(current_prompt, 42, None)
                        current_prompt = ""
                    elif payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']) != True:
                        event = Event(public_key,
                                      "You havent paid yet, send /gmj again once you paid or give a new prompt with /p",
                                      kind=42,
                                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                time.sleep(1)
            elif event_msg.event.kind == 4:
                user_pk = event_msg.event.public_key
                ss = compute_shared_secret(private_key, user_pk)
                content = decrypt_message(event_msg.event.content, ss)
                if content[0:3] == "/p ":
                    connect()
                    current_prompt = content[3:]
                    user_state_nostr[current_prompt] = payment.getinvoice()
                    event = Event(public_key, encrypt_message(str("https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" +
                                                                  user_state_nostr[current_prompt]['payment_request'] + "&format=.png") + " " +
                                                              str(user_state_nostr[current_prompt]['payment_request']), ss), kind=4,
                                  tags=[["p", user_pk]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(2)  # allow the messages to send
                    event = Event(public_key, encrypt_message("Send /gd (DALLE2) or /gsd (Stable Diffusion) or /gmj (Midjourney like, experimental) once you paid the invoice to start generating", ss), kind=4,
                                  tags=[["p", user_pk]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(1)  # allow the messages to send
                elif content == "/start":
                    time.sleep(1)
                    event = Event(public_key, encrypt_message(messages.start_nostr, ss), kind=4,
                                  tags=[["p", user_pk]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(1)  # allow the messages to send
                elif content == "/gd":
                    if payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']):
                        event = Event(public_key, encrypt_message(
                            "Generating images, this can take a minute...",
                            ss), kind=4,
                                      tags=[["p", user_pk]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                        dalle_generate(current_prompt, 4, user_pk)
                        current_prompt = ""
                    elif payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']) != True:
                        event = Event(public_key, encrypt_message("You havent paid yet, send /gd again once you paid or give a new prompt with /p", ss), kind=4,
                                      tags=[["p", user_pk]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                elif content == "/gsd":
                    if payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']):
                        event = Event(public_key, encrypt_message(
                            "Generating images, this can take a minute...",
                            ss), kind=4,
                                      tags=[["p", user_pk]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                        sd_generate(current_prompt, 4, user_pk)
                        current_prompt = ""
                    elif payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']) != True:
                        event = Event(public_key,
                                      encrypt_message("You havent paid yet, send /gsd again once you paid or give a new prompt with /p", ss),
                                      kind=4,
                                      tags=[["p", user_pk]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                elif content == "/gmj":
                    if payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']):
                        event = Event(public_key, encrypt_message(
                            "Generating images, this can take a minute...  If images appear black the AI interpreted them as NSFW",
                            ss), kind=4,
                                      tags=[["p", user_pk]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                        nostr_midjourney(current_prompt, 4, user_pk)
                        current_prompt = ""
                    elif payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']) != True:
                        event = Event(public_key,
                                      encrypt_message("You havent paid yet, send /gmj again once you paid or give a new prompt with /p", ss),
                                      kind=4,
                                      tags=[["p", user_pk]], created_at=int(time.time()))
                        event.sign(private_key)
                        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                        relay_manager.publish_message(message_2)
                        time.sleep(1)  # allow the messages to send
                time.sleep(1)
        except:
            connect()


def nostr_midjourney(prompt, message_type, user_pubk):
    id = str(int(time.time()))
    images = midjourney.generate_mj(prompt, id)
    if message_type == 42:
        if images == "failure":
            logging.error("mj error nostr: " + prompt)
            event = Event(public_key, "Whoops, this failed. Sometimes the API is unreliable, send an invoice and "
                                      "@f321x will try to refund you. You can try again later.", kind=42,
                          tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
            event.sign(private_key)
            message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
            relay_manager.publish_message(message_2)
            time.sleep(1.25)  # allow the messages to send
        else:
            connect()
            for file in images:
                rc.copy(file, 'dropbox:lpb')
                os.remove(file)
                m = file.replace(os.getcwd() + "/", "")
                link = list(rc.link('dropbox:lpb/' + m))
                link[-2] = '1'
                event = Event(public_key, ''.join(link) + " " + prompt + ", Midjourney model", kind=42,
                              tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1.25)  # allow the messages to send
            rc.execute('delete --min-age 360d dropbox:lpb')
            time.sleep(1)  # allow the messages to send
    elif message_type == 4:
        ss = compute_shared_secret(private_key, user_pubk)
        if images == "failure":
            logging.error("MJ error nostr: " + prompt)
            event = Event(public_key, encrypt_message(
                "Whoops, this failed. Sometimes the API is unreliable, send an invoice and "
                "@f321x will try to refund you. You can try again later.", ss), kind=4,
                          tags=[["p", user_pubk]], created_at=int(time.time()))
            event.sign(private_key)
            message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
            relay_manager.publish_message(message_2)
            time.sleep(1.25)  # allow the messages to send
        else:
            connect()
            for image in images:
                rc.copy(image, 'dropbox:lpb')
                os.remove(image)
                m = image.replace(os.getcwd() + "/", "")
                link = list(rc.link('dropbox:lpb/' + m))
                link[-2] = '1'
                event = Event(public_key, encrypt_message(''.join(link) + " " + prompt + ", Midjourney model", ss), kind=4,
                              tags=[["p", user_pubk]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1.25)  # allow the messages to send
        rc.execute('delete --min-age 360d dropbox:lpb')
        time.sleep(1)  # allow the messages to send

def dalle_generate(prompt, type, user_pk):
    id = str(int(time.time()))
    generations = dalle2.generate_and_download(str(prompt), id)
    if type == 42:
        if generations == "violation":
            logging.info("nostr dalle violation: " + prompt)
            event = Event(public_key, "Your prompt violated the OpenAI terms so it got blocked by them. Try to avoid controversial stuff or use Stable Diffusion with /gsd", kind=42,
                          tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
            event.sign(private_key)
            message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
            relay_manager.publish_message(message_2)
            time.sleep(1.25)  # allow the messages to send
        elif generations == "failure":
            logging.error("dalle error nostr: " + prompt)
            event = Event(public_key, "Whoops, this failed. Sometimes the Dalle API is unreliable, send an invoice and "
                                      "@f321x will try to refund you. You can try again later.", kind=42, tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
            event.sign(private_key)
            message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
            relay_manager.publish_message(message_2)
            time.sleep(1.25)  # allow the messages to send
        else:
            connect()
            for n in generations:
                rc.copy(n, 'dropbox:lpb')
                os.remove(n)
                m = n.replace(os.getcwd() + "/", "")
                link = list(rc.link('dropbox:lpb/' + m))
                link[-2] = '1'
                event = Event(public_key, ''.join(link) + " " + prompt + ", DALLE2", kind=42,
                              tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1.25)  # allow the messages to send
            rc.execute('delete --min-age 360d dropbox:lpb')
            time.sleep(1)  # allow the messages to send
    elif type == 4:
        ss = compute_shared_secret(private_key, user_pk)
        if generations == "violation":
            logging.info("nostr dalle violation: " + prompt)
            event = Event(public_key,
                          encrypt_message("Your prompt violated the OpenAI terms so it got blocked by them. Try to avoid controversial stuff or use Stable Diffusion with /gsd", ss),
                          kind=4,
                          tags=[["p", user_pk]], created_at=int(time.time()))
            event.sign(private_key)
            message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
            relay_manager.publish_message(message_2)
            time.sleep(1.25)  # allow the messages to send
        elif generations == "failure":
            logging.error("dalle error nostr: " + prompt)
            event = Event(public_key, encrypt_message("Whoops, this failed. Sometimes the Dalle API is unreliable, send an invoice and "
                                      "@f321x will try to refund you. You can try again later.", ss), kind=4,
                          tags=[["p", user_pk]], created_at=int(time.time()))
            event.sign(private_key)
            message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
            relay_manager.publish_message(message_2)
            time.sleep(1.25)  # allow the messages to send
        else:
            connect()
            for n in generations:
                rc.copy(n, 'dropbox:lpb')
                os.remove(n)
                m = n.replace(os.getcwd() + "/", "")
                link = list(rc.link('dropbox:lpb/' + m))
                link[-2] = '1'
                event = Event(public_key, encrypt_message(''.join(link) + " " + prompt + ", DALLE2", ss), kind=4,
                              tags=[["p", user_pk]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1.25)  # allow the messages to send
            rc.execute('delete --min-age 360d dropbox:lpb')
            time.sleep(1)  # allow the messages to send

def sd_generate(prompt, type, user_pk):
    id = str(int(time.time()))
    connect()
    if type == 42:
        for generating in range(2):
            if stablediffusion.find_seed(prompt) == "seed_too_long":
                event = Event(public_key, "Seed too long, use max. 9 digits, generating without seed now.", kind=42,
                              tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1)
            elif stablediffusion.find_seed(prompt) == "seed_no_int":
                event = Event(public_key, "Seed not an integer (number), generating without seed now.", kind=42,
                              tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1)
            try:
                stablediffusion.generate_sd_normal(prompt, id)
                for guidance in range(7, 11):
                    rc.copy('sd_picture_gd_' + str(guidance) + "_" + id + '.png', 'dropbox:lpb')
                    time.sleep(1)
                    os.remove('sd_picture_gd_' + str(guidance) + "_" + id + '.png')
                    link = list(rc.link('dropbox:lpb/' + 'sd_picture_gd_' + str(guidance) + "_" + id + '.png'))
                    link[-2] = '1'
                    event = Event(public_key, ''.join(link) + " " + prompt + ", Stable Diffusion", kind=42,
                                  tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                logging.info('nostr sd: ' + prompt)
                rc.execute('delete --min-age 90d dropbox:lpb')
                break
            except:
                if generating == 0:
                    logging.error("nostr sd error: " + prompt)
                    event = Event(public_key, "Failed, trying again. If it doesn't give you pictures in a minute click "
                                              "/problem", kind=42, tags=[["e", os.environ['nostr_chat_id']]],
                                  created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(15)
                elif generating == 1:
                    logging.error("nostr sd error: " + prompt)
                    event = Event(public_key, "Failed, trying again. If it doesn't give you pictures in a minute click "
                                              "/problem", kind=42, tags=[["e", os.environ['nostr_chat_id']]],
                                  created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(15)
    elif type == 4:
        ss = compute_shared_secret(private_key, user_pk)
        for generating in range(2):
            if stablediffusion.find_seed(prompt) == "seed_too_long":
                event = Event(public_key, encrypt_message("Seed too long, use max. 9 digits, generating without seed now.", ss), kind=4,
                              tags=[["p", user_pk]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1)
            elif stablediffusion.find_seed(prompt) == "seed_no_int":
                event = Event(public_key, encrypt_message("Seed not an integer (number), generating without seed now.", ss), kind=4,
                              tags=[["p", public_key]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1)
            try:
                stablediffusion.generate_sd_normal(prompt, id)
                for guidance in range(7, 11):
                    rc.copy('sd_picture_gd_' + str(guidance) + "_" + id + '.png', 'dropbox:lpb')
                    os.remove('sd_picture_gd_' + str(guidance) + "_" + id + '.png')
                    link = list(rc.link('dropbox:lpb/' + 'sd_picture_gd_' + str(guidance) + "_" + id + '.png'))
                    link[-2] = '1'
                    event = Event(public_key, encrypt_message(''.join(link) + " " + prompt + ", Stable Diffusion", ss), kind=4,
                                  tags=[["p", user_pk]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(1)
                logging.info('nostr sd: ' + prompt)
                rc.execute('delete --min-age 90d dropbox:lpb')
                break
            except:
                if generating == 0:
                    logging.error("nostr sd error: " + prompt)
                    event = Event(public_key, encrypt_message("Failed, trying again. If it doesn't give you pictures in a minute click "
                                              "/problem", ss), kind=4, tags=[["p", user_pk]],
                                  created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(15)
                elif generating == 1:
                    logging.error("nostr sd error: " + prompt)
                    event = Event(public_key, encrypt_message("Failed, trying again. If it doesn't give you pictures in a minute click "
                                              "/problem", ss), kind=4, tags=[["p", user_pk]],
                                  created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(15)


connect()
nostr_dalle()

