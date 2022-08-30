# this bot uses the dezgo uncensored stable diffusion api (https://rapidapi.com/dezgo/api/dezgo/)
import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

url = "https://dezgo.p.rapidapi.com/text2image"

prompt = "None"

headers = {
    "content-type": "application/x-www-form-urlencoded",
    "X-RapidAPI-Key": os.environ['dezgo_sd_key'],
    "X-RapidAPI-Host": "dezgo.p.rapidapi.com"
}


def generate_sd_normal(prompt, chat_id):
    prompt = prompt.replace(' ', '%20')
    prompt = prompt.replace(',', '%2C')
    prompt = prompt.replace(';', '%3B')
    for guidance in range(5, 9):
        payload = "guidance=" + str(guidance) + "&steps=50&prompt=" + prompt + "&width" \
                                                                               "=512&height=512"
        response = requests.request("POST", url, data=payload, headers=headers)
        if response.status_code == 200:
            f = open('sd_picture_gd_' + str(guidance) + "_" + str(chat_id) + '.png', 'wb')
            f.write(response.content)
            f.close()
            time.sleep(1)
        else:
            return None

# def generate_sd_hd(prompt): (doesnt work, 504 gateway Time-out)
#    prompt = prompt.replace(' ', '%20')
#    prompt = prompt.replace(',', '%2C')
#    prompt = prompt.replace(';', '%3B')
#    payload = "guidance=7&steps=100&prompt=" + prompt + "&width=1024&height=1024"
#    response = requests.request("POST", url, data=payload, headers=headers, timeout=None)
#    print(response.content)
#    print(response.status_code)
#    f = open('sd_picture_hd.png', 'wb')
#    f.write(response.content)
#    f.close()
