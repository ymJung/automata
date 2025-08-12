import asyncio
import telegram

class TelegramBot:
    def __init__(self, token, chat_id):
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id

    def send_message(self, message):
        """동기 방식으로 메시지를 전송합니다."""
        try:
            asyncio.run(self._send_message_async(message))
        except Exception as e:
            print(f"텔레그램 메시지 전송 실패: {e}")

    async def _send_message_async(self, message):
        """비동기 방식으로 메시지를 전송합니다."""
        await self.bot.send_message(chat_id=self.chat_id, text=message)

if __name__ == '__main__':
    # For testing purposes
    # You need to replace 'YOUR_TELEGRAM_BOT_TOKEN' and 'YOUR_CHAT_ID' with your actual token and chat ID.
    # You can get the chat ID by sending a message to your bot and then visiting https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
    bot = TelegramBot(token='YOUR_TELEGRAM_BOT_TOKEN', chat_id='YOUR_CHAT_ID')
    bot.send_message("Hello, this is a test message from your bot!")
