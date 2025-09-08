import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.menu import menu, menu_callback_handler
from handlers.input_handler import handle_user_free_input

TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")  # ví dụ: https://your-app-name.up.railway.app

def main():
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN chưa được set trong Railway Variables")
    if not APP_URL:
        raise ValueError("❌ APP_URL chưa được set. VD: https://your-app-name.up.railway.app")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler(["start", "menu"], menu))
    app.add_handler(CallbackQueryHandler(menu_callback_handler))

    # Nhập text tự do
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_free_input))

    PORT = int(os.getenv("PORT", 8080))
    print("🤖 Bot is running with webhook on Railway...")
    app.run_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=f"{APP_URL}/{TOKEN}")

if __name__ == "__main__":
    main()
