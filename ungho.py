import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_ungho_text():
    return (
        "💖 *ỦNG HỘ & GÓP Ý CHO BOT*\n"
        "Cảm ơn bạn đã sử dụng bot! Nếu thấy hữu ích, bạn có thể ủng hộ để mình duy trì và phát triển thêm tính năng.\n\n"
        "🔗 *Chuyển khoản Vietcombank:*\n"
        "`0071003914986`\n"
        "_TRUONG ANH TU_\n\n"
        "Hoặc quét mã QR bên dưới.\n\n"
        "🌟 *Góp ý/đề xuất tính năng*: nhắn trực tiếp qua Telegram hoặc email: tutruong19790519@gmail.com\n"
        "Rất mong nhận được ý kiến của bạn! 😊"
    )

def get_ungho_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]
    ])

def get_qr_image_path():
    # Đường dẫn ảnh mã QR, đặt file qr_ung_ho.png tại root project
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "qr_ung_ho.png")

async def ung_ho_gop_y(update, context):
    text = get_ungho_text()
    qr_path = get_qr_image_path()
    # Xử lý cho cả callback query hoặc command
    if getattr(update, "callback_query", None):
        await update.callback_query.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption=text,
            parse_mode="Markdown",
            reply_markup=get_ungho_keyboard()
        )
    elif getattr(update, "message", None):
        await update.message.reply_photo(
            photo=open(qr_path, "rb"),
            caption=text,
            parse_mode="Markdown",
            reply_markup=get_ungho_keyboard()
        )
