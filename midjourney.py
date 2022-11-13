import replicate
from dotenv import load_dotenv
import os
import requests
from pathlib import Path

load_dotenv()

dir = os.getcwd()
os.environ["REPLICATE_API_TOKEN"] = str(os.environ["replicate_token"])

model = replicate.models.get("tstramer/midjourney-diffusion")
version = model.versions.get("6fbe956dba2f7b28f33ddf2b18fcc2d79d91a08b98f5948b0a63fe5925af505c")

def generate_mj(prompt, id):
    counter = 0
    files = []
    name = str(prompt.replace(" ", ""))
    try:
        for picture in range(1, 5):
            output = version.predict(prompt=prompt, width=1024, height=768)
            file = open(name + str(id) + str(counter) + ".png", "wb")
            dl_file = requests.get(output[0])
            file.write(dl_file.content)
            file.close()
            path = Path(dir, name + str(id) + str(counter)).with_suffix('.png')
            files.append(str(path))
            counter += 1
        return files
    except:
        return "failure"