# dalle2telegrambot
Telegram bot for Open AI Dalle 2 with Bitcoin Lightning payments

This is the first real thing i programmed, so please be careful using it and have a look at the code first.

Setup:

Optain Dalle 2 API Key:

    Go to https://labs.openai.com/
    Open Network Tab in Developer Tools (Browser)
    Type a prompt and press "Generate"
    Look for fetch to https://labs.openai.com/api/labs/tasks
    In the request header look for authorization then get the Bearer Token

Optain LNBits Key:
  Run your own LNBits instance or use a public available one like legend.lnbits.com
  Create a wallet and click on API Info on the right side, you need the Invoice key
 
Create Telegram Bot and get API Key:
  search the Internet for "create telegram bot botfather"

Put the API keys in the .env file

install python-telegram-bot v20 with "pip install python-telegram-bot --pre"

If you encounter any possible improvements, bugs etc... please tell me so i can learn
