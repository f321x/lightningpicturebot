import os
import ssl
import time
import json
import messages
import payment
from nostr.relay_manager import RelayManager
from nostr.key import generate_private_key, get_public_key
from nostr.filter import Filter, Filters
from nostr.event import Event, EventKind
from nostr.message_type import ClientMessageType
from dotenv import load_dotenv
from dalle2 import Dalle2
import logging

dalle = Dalle2(os.environ['openai_token'])

logging.basicConfig(
    filename="mylog.txt",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()
private_key = os.environ['nostr_pk']
public_key = get_public_key(private_key)
subscription_id = "hello relay"
filters = Filters([Filter(tags={"#e": [os.environ['nostr_chat_id']]}, limit=0)])
relay_manager = RelayManager()

def connect():
    relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager.add_relay("wss://relay.damus.io")
    relay_manager.add_subscription(subscription_id, filters)
    relay_manager.open_connections({"cert_reqs": ssl.CERT_NONE})  # NOTE: This disables ssl certificate verification
    time.sleep(1.25)  # allow the connections to open

def nostr_dalle():
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())
    message = json.dumps(request)
    relay_manager.publish_message(message)
    time.sleep(1)  # allow the messages to send
    user_state_nostr = {}
    current_prompt = ""
    while True:
        try:
            relay_manager.publish_message(message)
            event_msg = relay_manager.message_pool.get_event()
            if event_msg.event.content[0:3] == "/p ":
                current_prompt = event_msg.event.content[3:]
                user_state_nostr[current_prompt] = payment.getinvoice()
                time.sleep(1)
                event = Event(public_key, str(user_state_nostr[current_prompt]['payment_request']), kind=42,
                              tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                event.sign(private_key)
                message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                relay_manager.publish_message(message_2)
                time.sleep(1)  # allow the messages to send
                event = Event(public_key, "Send /g once you paid the invoice to start generating", kind=42,
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
            elif event_msg.event.content == "/g":
                time.sleep(1)
                if payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']):
                    dalle_generate(current_prompt)
                elif payment.checkinvoice(user_state_nostr[current_prompt]['payment_hash']) != True:
                    event = Event(public_key, "You havent paid yet, send /g again once you paid or give a new prompt with /p", kind=42,
                                  tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
                    event.sign(private_key)
                    message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
                    relay_manager.publish_message(message_2)
                    time.sleep(1)  # allow the messages to send
            time.sleep(1)
        except:
            connect()

def dalle_generate(prompt):
    generations = dalle.generate(str(prompt))
    if generations == "violation":
        logging.info("nostr dalle violation: " + prompt)
        event = Event(public_key, "Your prompt violated the OpenAI terms so it got blocked by them. Try to avoid controversial stuff or use Stable Diffusion on my TG Bot t.me/dalle2lightningbot", kind=42,
                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
        event.sign(private_key)
        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
        relay_manager.publish_message(message_2)
        time.sleep(1)  # allow the messages to send
    elif generations == "failure":
        logging.error("dalle error nostr: " + prompt)
        event = Event(public_key,
                      "Whoops, this failed. Sometimes the Dalle API is unreliable, send an invoice and @f321x will try to refund you. You can try again later.",
                      kind=42,
                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
        event.sign(private_key)
        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
        relay_manager.publish_message(message_2)
        time.sleep(1)  # allow the messages to send
    else:
        for n in generations:
            event = Event(public_key, n['generation']['image_path'], kind=42,
                          tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
            event.sign(private_key)
            message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
            relay_manager.publish_message(message_2)
            time.sleep(1)  # allow the messages to send
        event = Event(public_key, "Download the pictures you like, the links work only a short time.", kind=42,
                      tags=[["e", os.environ['nostr_chat_id']]], created_at=int(time.time()))
        event.sign(private_key)
        message_2 = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
        relay_manager.publish_message(message_2)
        time.sleep(1)  # allow the messages to send


