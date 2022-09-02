import os
import requests
from dotenv import load_dotenv

load_dotenv()

headers = {
    'X-Api-Key': os.environ['lnbits_invoice_key'],
    'Content-type': 'application/json',
}

data = '{"out": false, "amount":1000, "memo":"lightningpicturebot", "unit":"sat"}'


def getinvoice():
    response = requests.post('https://192.168.0.72:5001/api/v1/payments', headers=headers, data=data, verify=False)
    return response.json()


def checkinvoice(payment_hash):
    response = requests.get('https://192.168.0.72:5001/api/v1/payments/' + payment_hash, headers=headers, verify=False)
    return response.json()['paid']

#def refund():
#    data = '{"data": "bolt11, lnbc10u1p33yg3jsp5wt3w0n2nwpmxd274h343ut85y2lnm95rmf5ccddzaraejpy53axspp5ee3snxevh7wdury74jtm5rv0lvh9axjna6ypa82n3we43jmdgd8qdq8w3jhxaqxqyjw5qcqpjrzjqf5qjhn372nhax3p4hwr5gk5ey89xx9vp64sqjdeqcxjft4yw26myzmkqcqq0ncqqqqqqq05qqqqqpgq9q9qyysgqrsh5r6njxgfkw07c8r2z0smtc39xr43yt6pqs86fm28zkrmd90l4jnmav56x55v2t7v5kszxjaw000hlj7su70g4t7ne58cyfgju3gcqqsmmu4"}'
#    response = requests.post('https://192.168.0.72:5001/api/v1/payments/decode', headers=headers, data=data, verify=False)
#    print(response.json())
#refund()

