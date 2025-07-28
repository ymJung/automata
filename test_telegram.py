import configparser
import asyncio
import telegram

async def send_daily_message(): #실행시킬 함수명 임의지정
    config = configparser.ConfigParser()
    config.read('config.cfg')
    
    token = config['telegram']['TOKEN']
    chat_id = config['telegram']['CHAT_ID']
    bot = telegram.Bot(token = token)

    message = "hello"
    await bot.send_message(chat_id,message)

async def main():
    await send_daily_message()
    

if __name__ == "__main__":
    asyncio.run(main())