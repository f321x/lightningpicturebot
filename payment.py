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

data = '{"out": false, "amount":993, "memo":"lightningpicturebot", "unit":"sat"}'


def getinvoice():
    response = requests.post('https://192.168.0.72:5001/api/v1/payments', headers=headers, data=data, verify=False)
    return response.json()


def checkinvoice(payment_hash):
    response = requests.get('https://192.168.0.72:5001/api/v1/payments/' + payment_hash, headers=headers, verify=False)
    return response.json()['paid']


def refund(invoice):
    if invoice[4:7] == '10u' or invoice[14:17] == '10u':
        data = '{"out": true, "bolt11": "' + invoice + '"}'
        response = requests.post('https://192.168.0.72:5001/api/v1/payments', headers=headers_refund, data=data, verify=False)
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