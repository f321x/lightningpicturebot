# this bot uses the dezgo uncensored stable diffusion api (https://rapidapi.com/dezgo/api/dezgo/)
import os
import requests
from dotenv import load_dotenv
import time
import urllib.parse

load_dotenv()

url = "https://dezgo.p.rapidapi.com/text2image"

prompt = "None"

headers = {
    "content-type": "application/x-www-form-urlencoded",
    "X-RapidAPI-Key": os.environ['dezgo_sd_key'],
    "X-RapidAPI-Host": "dezgo.p.rapidapi.com"
}

def find_seed(prompt):
    for n in prompt:
        if n == "/":
            if prompt[prompt.index("/")+1:].isdigit():
                if int(prompt[prompt.index("/")+1:]) < 2147483648:
                    return "&seed=" + prompt[prompt.index("/")+1:]
                else:
                    return "seed_too_long"
            else:
                return "seed_no_int"
        else:
            pass
    return ""

def seed_remover(prompt):
    for n in prompt:
        if n == "/":
            return prompt[:prompt.index("/")]
        else:
            pass
    return prompt

def generate_sd_normal(prompt, chat_id):
    seed = find_seed(prompt)
    if seed == "seed_too_long":
        seed = ""
    elif seed == "seed_no_int":
        seed = ""
    prompt = seed_remover(prompt)
    prompt = urllib.parse.quote(prompt)
    for guidance in range(7, 11):
        payload = "guidance=" + str(guidance) + "&steps=50&prompt=" + prompt + "&width=512&height=512" + seed
        response = requests.request("POST", url, data=payload, headers=headers)
        if response.status_code == 200:
            f = open('sd_picture_gd_' + str(guidance) + "_" + str(chat_id) + '.png', 'wb')
            f.write(response.content)
            f.close()
            time.sleep(1)
        else:
            return None
