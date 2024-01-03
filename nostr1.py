# needs rclone set up with dropbox, running
import os
import time
import messages
import payment
from nostr.relay_manager import RelayManager
from nostr.key import PrivateKey
from nostr.filter import Filter, Filters
import sys
from nostr.event import Event, EventKind
from dotenv import load_dotenv
import dalle2
import midjourney
import logging
from rclone.rclone import Rclone
import stablediffusion
import re
import traceback
import uuid

rc = Rclone()

logging.basicConfig(
    filename="nostrlog.txt",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()


prompt_pattern = re.compile(r"/p")
start_pattern = re.compile(r"/start")
dalle_pattern = re.compile(r"/gd")
sd_pattern = re.compile(r"/gsd")
mj_pattern = re.compile(r"/gmj")


def prompt_finder(message):
    if prompt_pattern.search(message):
        pattern = prompt_pattern.search(message)
        return ["prompt", message[pattern.span()[1] + 1:]]
    elif start_pattern.search(message):
        return ["start"]
    elif dalle_pattern.search(message):
        pattern = dalle_pattern.search(message)
        return ["gd", message[pattern.span()[1] + 1:]]
    elif sd_pattern.search(message):
        pattern = sd_pattern.search(message)
        return ["gsd", message[pattern.span()[1] + 1:]]
    elif mj_pattern.search(message):
        pattern = mj_pattern.search(message)
        return ["gmj", message[pattern.span()[1] + 1:]]
    else:
        return [""]


def get_event_reference(event_tags, user_dict):
    for tag in event_tags:
        if tag[0] == "e" and tag[1] in user_dict.keys():
            return tag[1]
        else:
            pass
    return None

private_key = PrivateKey().from_nsec(os.environ['nostr_pk'])
public_key = private_key.public_key.hex()
subscription_id = str(int(time.time()))
filters_pm = Filter(limit=1, kinds=[EventKind.ENCRYPTED_DIRECT_MESSAGE], pubkey_refs=[public_key],
                    since=int(time.time()))
filters_gc = Filter(limit=1, kinds=[EventKind.TEXT_NOTE], pubkey_refs=[public_key], since=int(time.time()))
filters = Filters([filters_pm, filters_gc])
relay_manager = RelayManager()

def connect():
    try:
        relay_manager.add_relay("wss://nostr-pub.wellorder.net")
        # relay_manager.add_relay("wss://nostr.fmt.wiz.biz")
        # relay_manager.add_relay("wss://brb.io")
        relay_manager.add_relay("wss://relay.damus.io")
        #relay_manager.add_relay("wss://nostr.coollamer.com")
        #relay_manager.add_relay("wss://nostr.snblago.com")
        #relay_manager.add_relay("wss://relay.orangepill.dev")
        #relay_manager.add_relay("wss://eden.nostr.land")
        #relay_manager.add_relay("wss://nostream.nostrly.io")
        #relay_manager.add_relay("wss://nostr.vulpem.com")
        relay_manager.add_relay("wss://nostr.einundzwanzig.space")
        #relay_manager.add_relay("wss://relay.snort.social")
        relay_manager.add_subscription_on_all_relays(subscription_id, filters)
        time.sleep(1.25)
    except:
        return "Connection Error!"


user_state_nostr = {}


def nostr_bot():
    global user_state_nostr
    while True:
        time.sleep(0.5)
        try:
            event_msg = relay_manager.message_pool.get_event()  # listening for events
            if event_msg.event.kind == 1:
                prompt = prompt_finder(event_msg.event.content)  # searching for "/" in the event
                if prompt[0] == "prompt" and prompt[1] != "":  # if prompt contains "/p"
                    user_state_nostr[event_msg.event.id] = payment.getinvoice(), str(prompt[1])
                    answer = str(user_state_nostr[event_msg.event.id][0]['payment_request']) + " " + \
                             "Answer with /gsd for Stable Diffusion, /gd for DALLE2 or /gmj for a Midjourney AI model."
                    event = Event(public_key=public_key,
                                  content=answer,
                                  kind=1,
                                  tags=[["e", event_msg.event.id, "wss://relay.orangepill.dev", "root"],
                                        ["p", event_msg.event.public_key]],
                                  created_at=int(time.time()) + 5)
                    private_key.sign_event(event)
                    relay_manager.publish_event(event)
                    time.sleep(1)  # allow the messages to send
                elif prompt[0] == "start":
                    event = Event(public_key=public_key,
                                  content=messages.start_nostr,
                                  kind=1,
                                  tags=[["e", event_msg.event.id, "wss://relay.orangepill.dev", "root"],
                                        ["p", event_msg.event.public_key]],
                                  created_at=int(time.time()) + 5)
                    private_key.sign_event(event)
                    relay_manager.publish_event(event)
                    time.sleep(1)  # allow the messages to send
                elif prompt[0] == "gd" or prompt[0] == "gsd" or prompt[0] == "gmj":
                    root_id = get_event_reference(event_msg.event.tags, user_state_nostr)
                    if root_id and payment.checkinvoice(user_state_nostr[root_id][0]['payment_hash']):
                        event = Event(public_key=public_key,
                                      content="Generating images, this can take a minute...",
                                      kind=1,
                                      tags=[["e", event_msg.event.id, "wss://relay.orangepill.dev", "reply"],
                                            ["p", event_msg.event.public_key]],
                                      created_at=int(time.time()) + 5)
                        private_key.sign_event(event)
                        relay_manager.publish_event(event)
                        if prompt[0] == "gd":
                            dalle_generate(user_state_nostr[root_id][1], 1, event.id, event_msg.event.public_key)
                        elif prompt[0] == "gsd":
                            sd_generate(user_state_nostr[root_id][1], 1, event.id, event_msg.event.public_key)
                        elif prompt[0] == "gmj":
                            nostr_midjourney(user_state_nostr[root_id][1], 1, event.id, event_msg.event.public_key)
                    elif root_id and payment.checkinvoice(user_state_nostr[root_id][0]['payment_hash']) is not True:
                        event = Event(public_key=public_key,
                                      content="You haven't paid yet, send /gd, /gsd or /gmj again once you paid or "
                                              "give a new prompt with /p",
                                      kind=1,
                                      tags=[["e", event_msg.event.id, "wss://relay.orangepill.dev", "reply"],
                                            ["p", event_msg.event.public_key]],
                                      created_at=int(time.time()) + 5)
                        user_state_nostr[event.id] = user_state_nostr[root_id]
                        user_state_nostr.pop(root_id)
                        private_key.sign_event(event)
                        relay_manager.publish_event(event)
                        time.sleep(1)
                time.sleep(1)
            elif event_msg.event.kind == 4:
                user_pk = event_msg.event.public_key
                content = private_key.decrypt_message(event_msg.event.content, user_pk)
                if content[0:3] == "/p ":
                    user_state_nostr[user_pk] = payment.getinvoice(), content[3:]
                    event = Event(public_key=public_key,
                                  content=private_key.encrypt_message(
                                      str(user_state_nostr[user_pk][0]['payment_request']) + " " +
                                      "Answer with /gsd for Stable Diffusion, /gd for DALLE2 or "
                                      "/gmj for a Midjourney AI model.", user_pk),
                                  kind=4,
                                  tags=[["p", user_pk]],
                                  created_at=int(time.time()) + 5)
                    private_key.sign_event(event)
                    relay_manager.publish_event(event)
                    time.sleep(1)
                elif content == "/start":
                    time.sleep(1)
                    event = Event(public_key=public_key,
                                  content=private_key.encrypt_message(messages.start_nostr, user_pk),
                                  kind=4,
                                  tags=[["p", user_pk]],
                                  created_at=int(time.time()) + 5)
                    private_key.sign_event(event)
                    relay_manager.publish_event(event)
                    time.sleep(1)
                elif content[0:8] == "/refund ":
                    event = None
                    try:
                        if user_state_nostr[event_msg.event.public_key] == "refund_true":
                            refund = payment.refund(content[8:])
                            if refund == "success":
                                event = Event(public_key=public_key,
                                              content=private_key.encrypt_message("Refund successful!", user_pk),
                                              kind=4,
                                              tags=[["p", user_pk]],
                                              created_at=int(time.time()) + 5)
                                user_state_nostr.pop(user_pk)
                            elif refund == "wrong":
                                event = Event(public_key=public_key,
                                              content=private_key.encrypt_message(
                                                  "Your invoice is invalid, please try again with a "
                                                  "1000 Satoshi invoice. Use the format /refund "
                                                  "bolt11Invoice", user_pk),
                                              kind=4,
                                              tags=[["p", user_pk]],
                                              created_at=int(time.time()) + 5)
                            elif refund == "error":
                                event = Event(public_key=public_key,
                                              content=private_key.encrypt_message(
                                                  "Refunding failed, please contact "
                                                  "@npub1z9n5ktfjrlpyywds9t7ljekr9cm9jjnzs27h702te5fy8p2c4dgs5zvycf",
                                                  user_pk),
                                              kind=4,
                                              tags=[["p", user_pk]],
                                              created_at=int(time.time()) + 5)
                                user_state_nostr.pop(user_pk)
                            private_key.sign_event(event)
                            relay_manager.publish_event(event)
                            time.sleep(1)
                        else:
                            raise KeyError
                    except KeyError:
                        logging.error("Bad refund attempt, user not in refund db")
                        event = Event(public_key=public_key,
                                      content=private_key.encrypt_message(
                                          "You are not supposed to get a refund! (or this is a bug)",
                                          user_pk),
                                      kind=4,
                                      tags=[["p", user_pk]],
                                      created_at=int(time.time()) + 5)
                        private_key.sign_event(event)
                        relay_manager.publish_event(event)
                        time.sleep(1)
                elif content == "/gd" or content == "/gsd" or content == "/gmj":
                    if user_pk in user_state_nostr.keys():
                        if payment.checkinvoice(user_state_nostr[user_pk][0]['payment_hash']):
                            event = Event(public_key=public_key,
                                          content=private_key.encrypt_message(
                                              "Generating images, this can take a minute...", user_pk),
                                          kind=4,
                                          tags=[["p", user_pk]],
                                          created_at=int(time.time()) + 5)
                            private_key.sign_event(event)
                            relay_manager.publish_event(event)
                            time.sleep(1)  # allow the messages to send
                            if content == "/gd":
                                dalle_generate(user_state_nostr[user_pk][1], 4, None, user_pk)
                            elif content == "/gsd":
                                sd_generate(user_state_nostr[user_pk][1], 4, None, user_pk)
                            elif content == "/gmj":
                                nostr_midjourney(user_state_nostr[user_pk][1], 4, None, user_pk)
                        elif payment.checkinvoice(user_state_nostr[user_pk][0]['payment_hash']) is not True:
                            event = Event(public_key=public_key,
                                          content=private_key.encrypt_message(
                                              "You haven't paid yet, send /gd, /gsd or /gmj again once you paid or give a "
                                              "new prompt with /p",
                                              user_pk),
                                          kind=4,
                                          tags=[["p", user_pk]],
                                          created_at=int(time.time()) + 5)
                            private_key.sign_event(event)
                            relay_manager.publish_event(event)
                            time.sleep(1)  # allow the messages to send
                time.sleep(1)
        except KeyboardInterrupt:
            sys.exit()
        except:
            traceback.print_exc()
            logging.error("main task exception")
            # connect()


def dalle_generate(prompt, event_kind, event_id, answer_pubkey):
    global user_state_nostr
    picture_identifier = str(uuid.uuid4())
    generations = dalle2.generate_and_download(str(prompt), picture_identifier)
    start_event_id = event_id
    event = None
    if generations == "violation":
        logging.info("nostr dalle violation: " + prompt)
        if event_kind == 1:
            event = Event(public_key=public_key,
                          content="Your prompt violated the OpenAI terms so it got blocked by them. Try to avoid "
                                  "controversial stuff or use Stable Diffusion with /gsd",
                          kind=1,
                          tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                ["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            user_state_nostr.pop(event_id)
        elif event_kind == 4:
            event = Event(public_key=public_key,
                          content=private_key.encrypt_message(
                              "Your prompt violated the OpenAI terms so it got blocked by them. Try to avoid "
                              "controversial stuff or use Stable Diffusion with /gsd",
                              answer_pubkey),
                          kind=4,
                          tags=[["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            user_state_nostr.pop(answer_pubkey)
        private_key.sign_event(event)
        relay_manager.publish_event(event)
        time.sleep(1)
    elif generations == "failure":
        logging.error("dalle error nostr: " + prompt)
        if event_kind == 1:
            event = Event(public_key=public_key,
                          content="Whoops, this failed. Sometimes the OpenAI API is unreliable, send /refund "
                                  "YOUR1000SATINVOICE to the bot as DM and you will get a refund. Please notify "
                                  "@npub1z9n5ktfjrlpyywds9t7ljekr9cm9jjnzs27h702te5fy8p2c4dgs5zvycf "
                                  "if you encounter problems so they will get fixed.",
                          kind=1,
                          tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                ["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            user_state_nostr.pop(event_id)
            user_state_nostr[answer_pubkey] = "refund_true"
        elif event_kind == 4:
            event = Event(public_key=public_key,
                          content=private_key.encrypt_message(
                              "Whoops, this failed. Sometimes the OpenAI API is unreliable, send /refund "
                              "YOUR1000SATINVOICE to the bot as DM and you will get a refund. Please notify "
                              "@npub1z9n5ktfjrlpyywds9t7ljekr9cm9jjnzs27h702te5fy8p2c4dgs5zvycf "
                              "if you encounter problems so they will get fixed.",
                              answer_pubkey),
                          kind=4,
                          tags=[["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            user_state_nostr[answer_pubkey] = "refund_true"
        private_key.sign_event(event)
        relay_manager.publish_event(event)
        time.sleep(1)
    else:
        for n in generations:
            rc.copy(n, 'dropbox:lpb')
            os.remove(n)
            m = n.replace(os.getcwd() + "/", "")
            link = list(rc.link('dropbox:lpb/' + m))
            link[-2] = '1'
            if event_kind == 1:
                event = Event(public_key=public_key,
                              content=''.join(link) + " " + prompt + ", DALLE2",
                              kind=1,
                              tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                    ["p", answer_pubkey]],
                              created_at=int(time.time()) + 5)
                event_id = event.id
            elif event_kind == 4:
                event = Event(public_key=public_key,
                              content=private_key.encrypt_message(''.join(link) + " " + prompt + ", DALLE2",
                                                                  answer_pubkey),
                              kind=4,
                              tags=[["p", answer_pubkey]], created_at=int(time.time()) + 5)
            private_key.sign_event(event)
            relay_manager.publish_event(event)
            time.sleep(1)
        try:
            if event_kind == 1:
                user_state_nostr.pop(start_event_id)
            elif event_kind == 4:
                user_state_nostr.pop(answer_pubkey)
        except KeyError:
            pass
        rc.execute('delete --min-age 360d dropbox:lpb')
        time.sleep(1)


def sd_generate(prompt, event_kind, event_id, answer_pubkey):
    global user_state_nostr
    picture_identifier = str(uuid.uuid4())
    dict_event_key = event_id
    event = None
    if stablediffusion.find_seed(prompt) == "seed_too_long":
        if event_kind == 1:
            event = Event(public_key=public_key,
                          content="Seed too long, use max. 9 digits, generating without seed now...",
                          kind=1,
                          tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                ["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            event_id = event.id
        elif event_kind == 4:
            event = Event(public_key=public_key,
                          content=private_key.encrypt_message(
                              "Seed too long, use max. 9 digits, generating without seed now.", answer_pubkey),
                          kind=4,
                          tags=[["p", answer_pubkey]], created_at=int(time.time()) + 5)
        private_key.sign_event(event)
        relay_manager.publish_event(event)
        time.sleep(1)
    elif stablediffusion.find_seed(prompt) == "seed_no_int":
        if event_kind == 1:
            event = Event(public_key=public_key,
                          content="Seed not an integer (number), generating without seed now.",
                          kind=1,
                          tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                ["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            event_id = event.id
        elif event_kind == 4:
            event = Event(public_key=public_key,
                          content=private_key.encrypt_message(
                              "Seed not an integer (number), generating without seed now.",
                              answer_pubkey),
                          kind=4,
                          tags=[["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
        private_key.sign_event(event)
        relay_manager.publish_event(event)
        time.sleep(1)
    try:
        stablediffusion.generate_sd_normal(prompt, picture_identifier)
        for guidance in range(7, 11):
            rc.copy('sd_picture_gd_' + str(guidance) + "_" + picture_identifier + '.png', 'dropbox:lpb')
            os.remove('sd_picture_gd_' + str(guidance) + "_" + picture_identifier + '.png')
            link = list(
                rc.link('dropbox:lpb/' + 'sd_picture_gd_' + str(guidance) + "_" + picture_identifier + '.png'))
            link[-2] = '1'
            if event_kind == 1:
                event = Event(public_key=public_key,
                              content=''.join(link) + " " + prompt + ", Stable Diffusion",
                              kind=1,
                              tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                    ["p", answer_pubkey]],
                              created_at=int(time.time()) + 5)
                event_id = event.id
            elif event_kind == 4:
                event = Event(public_key=public_key,
                              content=private_key.encrypt_message(''.join(link) + " " + prompt +
                                                                  ", Stable Diffusion", answer_pubkey),
                              kind=4,
                              tags=[["p", answer_pubkey]],
                              created_at=int(time.time()) + 5)
            private_key.sign_event(event)
            relay_manager.publish_event(event)
            time.sleep(1)
        logging.info('nostr sd: ' + prompt)
        rc.execute('delete --min-age 90d dropbox:lpb')
    except:
        logging.error("nostr sd error: " + prompt)
        if event_kind == 1:
            event = Event(public_key=public_key,
                          content="Whoops, this failed. Sometimes the AI API is unreliable, send /refund "
                                  "YOUR1000SATINVOICE to the bot as DM and you will get a refund. Please notify "
                                  "@npub1z9n5ktfjrlpyywds9t7ljekr9cm9jjnzs27h702te5fy8p2c4dgs5zvycf "
                                  "if you encounter problems so they will get fixed.",
                          kind=1,
                          tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                ["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            user_state_nostr.pop(dict_event_key)
            user_state_nostr[answer_pubkey] = "refund_true"
        elif event_kind == 4:
            event = Event(public_key=public_key,
                          content=private_key.encrypt_message("Whoops, this failed. Sometimes the AI API is "
                                                              "unreliable, send /refund"
                                                              "YOUR1000SATINVOICE to the bot as DM and you will get a "
                                                              "refund. Please notify"
                                                              "@npub1z9n5ktfjrlpyywds9t7ljekr9cm9jjnzs27h702te5fy8p2c4dgs5zvycf"
                                                              "if you encounter problems so they will get fixed.",
                                                              answer_pubkey),
                          kind=4,
                          tags=[["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            user_state_nostr[answer_pubkey] = "refund_true"
        private_key.sign_event(event)
        relay_manager.publish_event(event)
        time.sleep(10)
    try:
        if event_kind == 1:
            user_state_nostr.pop(dict_event_key)
        elif event_kind == 4:
            if user_state_nostr[answer_pubkey] != "refund_true":
                user_state_nostr.pop(answer_pubkey)
    except KeyError:
        pass


def nostr_midjourney(prompt, event_kind, event_id, answer_pubkey):
    global user_state_nostr
    user_state_id = event_id
    picture_identifier = str(uuid.uuid4())
    images = midjourney.generate_mj(prompt, picture_identifier)
    event = None
    if images == "failure":
        logging.error("mj error nostr: " + prompt)
        if event_kind == 1:
            event = Event(public_key=public_key,
                          content="Whoops, this failed. Sometimes the OpenAI API is unreliable, send /refund "
                                  "YOUR1000SATINVOICE to the bot as DM and you will get a refund. Please notify "
                                  "@npub1z9n5ktfjrlpyywds9t7ljekr9cm9jjnzs27h702te5fy8p2c4dgs5zvycf "
                                  "if you encounter problems so they will get fixed.",
                          kind=1,
                          tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                ["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            user_state_nostr.pop(event_id)
            user_state_nostr[answer_pubkey] = "refund_true"
        elif event_kind == 4:
            event = Event(public_key=public_key,
                          content=private_key.encrypt_message(
                              "Whoops, this failed. Sometimes the OpenAI API is unreliable, send /refund "
                              "YOUR1000SATINVOICE to the bot as DM and you will get a refund. Please notify "
                              "@npub1z9n5ktfjrlpyywds9t7ljekr9cm9jjnzs27h702te5fy8p2c4dgs5zvycf "
                              "if you encounter problems so they will get fixed.", answer_pubkey),
                          kind=4,
                          tags=[["p", answer_pubkey]],
                          created_at=int(time.time()) + 5)
            user_state_nostr[answer_pubkey] = "refund_true"
        private_key.sign_event(event)
        relay_manager.publish_event(event)
        time.sleep(1)
    else:
        for file in images:
            rc.copy(file, 'dropbox:lpb')
            os.remove(file)
            m = file.replace(os.getcwd() + "/", "")
            link = list(rc.link('dropbox:lpb/' + m))
            link[-2] = '1'
            if event_kind == 1:
                event = Event(public_key=public_key,
                              content=''.join(link) + " " + prompt + ", Midjourney model",
                              kind=1,
                              tags=[["e", event_id, "wss://relay.orangepill.dev", "reply"],
                                    ["p", answer_pubkey]],
                              created_at=int(time.time()) + 5)
            elif event_kind == 4:
                event = Event(public_key=public_key,
                              content=private_key.encrypt_message(''.join(link) + " " + prompt + ", Midjourney model",
                                                                  answer_pubkey),
                              kind=4,
                              tags=[["p", answer_pubkey]],
                              created_at=int(time.time()) + 5)
                event_id = event.id
            private_key.sign_event(event)
            relay_manager.publish_event(event)
            time.sleep(1)
        rc.execute('delete --min-age 360d dropbox:lpb')
    try:
        if event_kind == 1:
            user_state_nostr.pop(user_state_id)
        elif event_kind == 4:
            if user_state_nostr[answer_pubkey] != "refund_true":
                user_state_nostr.pop(answer_pubkey)
    except KeyError:
        pass


connect()
nostr_bot()
