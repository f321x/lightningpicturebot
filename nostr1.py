import ssl
import time
import json
from nostr.relay_manager import RelayManager
from nostr.key import generate_private_key, get_public_key
from nostr.filter import Filter, Filters
from nostr.event import Event, EventKind
from nostr.message_type import ClientMessageType


def gen_key():
    private_key = generate_private_key()
    print(private_key)
    return get_public_key(private_key)

def connect():
    relay_manager = RelayManager()
    relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager.add_relay("wss://relay.damus.io")
    relay_manager.open_connections({"cert_reqs": ssl.CERT_NONE})  # NOTE: This disables ssl certificate verification
    time.sleep(1.25)  # allow the connections to open

    while relay_manager.message_pool.has_notices():
        notice_msg = relay_manager.message_pool.get_notice()
        print(notice_msg.content)

    #relay_manager.close_connections()

def receive():
    filters = Filters([Filter(authors=["1d2b43bd1fcb6b7e70210ecd3e1e3da73f838a4e4a6cca67b9d7a35690337516"], kinds=[EventKind.TEXT_NOTE])])
    subscription_id = "a string to identify a subscription"
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters.to_json_array())

    relay_manager = RelayManager()
    relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager.add_relay("wss://relay.damus.io")
    relay_manager.add_subscription(subscription_id, filters)
    relay_manager.open_connections({"cert_reqs": ssl.CERT_NONE})  # NOTE: This disables ssl certificate verification
    time.sleep(1.25)  # allow the connections to open

    message = json.dumps(request)
    relay_manager.publish_message(message)
    time.sleep(1)  # allow the messages to send

    while relay_manager.message_pool.has_events():
        event_msg = relay_manager.message_pool.get_event()
        print(event_msg.event.content)

    #relay_manager.close_connections()

def send():
    relay_manager = RelayManager()
    relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager.add_relay("wss://relay.damus.io")
    relay_manager.open_connections({"cert_reqs": ssl.CERT_NONE})  # NOTE: This disables ssl certificate verification
    time.sleep(1.25)  # allow the connections to open

    private_key = "b7317a0aac1a21ecaee5d67ac127abdea6bc7c5aa86ab7132084b28c0983b43b"
    public_key = get_public_key(private_key)

    event = Event(public_key, "Hello Nostr")
    event.sign(private_key)

    message = json.dumps([ClientMessageType.EVENT, event.to_json_object()])
    relay_manager.publish_message(message)
    time.sleep(1)  # allow the messages to send

    relay_manager.close_connections()