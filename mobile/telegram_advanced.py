import asyncio

class TelegramBotAdvanced:
    """Stub básico para bot do Telegram"""
    def __init__(self, token: str, bot):
        self.token = token
        self.bot = bot
        # lazy import para não quebrar se pacote não estiver instalado
        try:
            from telegram import Bot
            from telegram.ext import Updater, CommandHandler
            self._tg_bot = Bot(token=token)
            self._updater = Updater(token=token, use_context=True)
        except ImportError:
            self._tg_bot = None
            self._updater = None

    def run(self):
        # caso o telegram esteja instalado, inicia handlers simples
        if self._updater:
            dispatcher = self._updater.dispatcher

            def start(update, context):
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="Bot de trading ativo!")

            dispatcher.add_handler(CommandHandler('start', start))
            self._updater.start_polling()
        else:
            # nada a fazer
            pass

    async def send_notification(self, message: str):
        if self._tg_bot:
            try:
                # usa chat_id configurado no .env ou via bot
                # como stub não temos id, apenas loggar
                print('[Telegram] ' + message)
            except Exception:
                pass
        else:
            print('[Telegram] ' + message)