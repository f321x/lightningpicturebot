# import replicate
# from dotenv import load_dotenv
# import os
# # import requests
# from pathlib import Path
# from urllib.request import urlretrieve


# load_dotenv()

# dir = os.getcwd()
# os.environ["REPLICATE_API_TOKEN"] = str(os.environ["replicate_token"])

# # model = replicate.models.get("tstramer/midjourney-diffusion")
# # version = model.versions.get("436b051ebd8f68d23e83d22de5e198e0995357afef113768c20f0b6fcef23c8b")

# def generate_mj(prompt, id):
#     counter = 0
#     headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"}

#     files = []
#     name = str(prompt.replace(" ", ""))
#     name = str(name.replace(".", ""))
#     name = str(name.replace(",", ""))
#     name = str(name.replace("!", ""))
#     name = str(name.replace("?", ""))
#     name = str(name.replace(":", ""))
#     # # try:
#     # outputs = replicate.run(
#     #             "tstramer/midjourney-diffusion:436b051ebd8f68d23e83d22de5e198e0995357afef113768c20f0b6fcef23c8b", input={"prompt": prompt, "num_outputs": 1})
#     # print(outputs)
#     outputs = ['https://replicate.delivery/pbxt/JiOj8MHkek21fkjrYgGsmwfhNJi29NF8vi73Khx6DVQvAsRkA/out-0.png', 'https://replicate.delivery/pbxt/9vmfgTNwtBxdVinIbhzbdrYTTat8WRkMPUw56cURNUSXf1ISA/out-0.png']
#     for picture in outputs:
#         print(picture)
#         file = open(name + str(id) + str(counter) + ".png", "wb")

#         urlretrieve(picture, name + str(id) + str(counter) + ".png")

#         path = Path(dir, name + str(id) + str(counter)).with_suffix('.png')
#         files.append(str(path))
#         counter += 1
#     print(files)
#     return files
#     # except:
#     #     return "failure"

# generate_mj("test", 123)
