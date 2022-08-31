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
    response = requests.get('https://192.168.0.72:5001/api/v1/payments' + payment_hash, headers=headers, verify=False)
    return response.json()['paid']

# def refund():
#   sth sth lnurlw
