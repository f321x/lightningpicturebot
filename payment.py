import os
import requests
from dotenv import load_dotenv


load_dotenv()

headers = {
    'X-Api-Key': os.environ['lnbits_invoice_key'],
    'Content-type': 'application/json',
}

headers_refund = {
    'X-Api-Key': os.environ['lnbits_refund_key'],
    'Content-type': 'application/json',
}

data = '{"out": false, "amount":1000, "memo":"lightningpicturebot", "unit":"sat"}'


def getinvoice():
    response = requests.post('https://legend.lnbits.com/api/v1/payments', headers=headers, data=data)
    return response.json()


def checkinvoice(payment_hash):
    response = requests.get('https://legend.lnbits.com/api/v1/payments/' + payment_hash, headers=headers)
    return response.json()['paid']


def refund(invoice):
    if invoice[4:7] == '10u' or invoice[14:17] == '10u':
        data = '{"out": true, "bolt11": "' + invoice + '"}'
        response = requests.post('https://legend.lnbits.com/api/v1/payments', headers=headers_refund, data=data)
        if response.status_code == 201:
            return "success"
        else:
            return "error"
    else:
        return "wrong"

def cloak_invoice(invoice):
    cloaked_invoice = requests.post('https://lnproxy.org/api/' + str(invoice))
    if cloaked_invoice.status_code == 200:
        return cloaked_invoice.text
    else:
        print(cloaked_invoice.status_code)
        return invoice