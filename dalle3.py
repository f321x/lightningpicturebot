import openai
import os
from dotenv import load_dotenv
import base64
from openai import OpenAI
from pathlib import Path
import urllib.parse

load_dotenv()
client = OpenAI(api_key=os.getenv("openai_token"))
# client.api_key = os.getenv("openai_token")


def generate_and_download(prompt, id=None):
    try:
        prompt = prompt.replace(".", " ")
        prompt = prompt.replace(",", " ")
        prompt = prompt.replace("'", " ")
        prompt = prompt.replace("!", " ")
        prompt = prompt.replace("?", " ")
        prompt = prompt.replace("&", " ")
        prompt = prompt.replace(":", " ")
        prompt = prompt.replace("-", " ")
        prompt = prompt.replace("#", " ")
        prompt = prompt.replace("*", " ")
        prompt = prompt.replace("+", " ")

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            quality="hd",
            size="1024x1024",
            response_format='b64_json'
        )
        # print(response)
        files = []
        dir = os.getcwd()
        count = 0

        for image in response.data:
            decoded = base64.decodebytes(response.data[count].b64_json.encode("ascii"))
            name = prompt.replace(" ", "")
            if id is None:
                fh = open(name + "_" + str(count) + ".png", "wb")
                path = Path(dir, name + "_" + str(count)).with_suffix('.png')
            else:
                fh = open(name + "_" + str(count) + "_" + id + ".png", "wb")
                path = Path(dir, name + "_" + str(count) + "_" + id).with_suffix('.png')
            fh.write(decoded)
            fh.close()
            files.append(str(path))
            count += 1
        return files
    except openai.BadRequestError as e:
        print(e)
        print("dalle3 violation")
        return "violation"
    except:
        print("dalle3 error")
        return "failure"


# generate_and_download("test")
