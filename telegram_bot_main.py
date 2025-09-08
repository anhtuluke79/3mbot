import os
import logging
from datetime import datetime
from typing import List

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# === Import các module người dùng đã cung cấp ===
# Lưu ý: các file này cần nằm cùng thư mục với file main này
from cang_dao import clean_numbers_input as clean_nums_cang, ghep_cang, dao_so
from phongthuy import (
    phongthuy_tudong,
    get_can_chi_ngay,
    chuan_hoa_can_chi,
    sinh_so_hap_cho_ngay,
    chot_so_format,
)
from ungho import ung_ho_gop_y
from xien import clean_numbers_input as clean_nums_xien, gen_xien, format_xien_result

# =========================
# Logging
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# Helpers
# =========================

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔢 Ghép Càng", callback_data="menu_cang"),
            InlineKeyboardButton("🔀 Đảo Số", callback_data="menu_dao"),
        ],
        [
            InlineKeyboardButton("🎯 Xiên n", callback_data="menu_xien"),
            InlineKeyboardButton("🔮 Phong Thủy", callback_data="menu_phongthuy"),
        ],
        [
            InlineKeyboardButton("📌 Chốt số hôm nay", callback_data="menu_chotso"),
        ],
        [
            InlineKeyboardButton("💖 Ủng hộ & góp ý", callback_data="menu_ungho"),
        ],
    ])


def menu_text() -> str:
    return (
        "👋 *Chào mừng đến với trợ lý số!*\n\n"
        "Chọn tính năng bên dưới hoặc dùng các lệnh:\n"
        "• /cang – Ghép càng vào dàn số\n"
        "• /dao – Đảo số (hoán vị 2–6 chữ số)\n"
        "• /xien – Ghép xiên n từ dàn\n"
        "• /phongthuy – Tra phong thủy ngày/can chi\n"
        "• /chotso – Gợi ý chốt số theo ngày hiện tại\n"
        "• /ungho – Ủng hộ & góp ý\n"
        "• /help – Hướng dẫn chi tiết"
    )


# =========================
# Command Handlers
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(menu_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())


ASYNC_GUIDES = {
    "cang": (
        "*Ghép Càng*\n"
        "Gửi theo 1 trong các cách:\n"
        "1) `cang: 1 2 3` xuống dòng dàn số\n"
        "   Ví dụ:\n"
        "   cang: 1 3\n"
        "   12 34 567\n\n"
        "2) Gõ trực tiếp: `1,3 | 12 34 567` (trước dấu | là danh sách càng)\n"
    ),
    "dao": (
        "*Đảo Số*\n"
        "Gửi 1 số có 2–6 chữ số để tạo mọi hoán vị.\n"
        "Ví dụ: `123` hoặc `0123`."
    ),
    "xien": (
        "*Xiên n*\n"
        "Cú pháp: \n`/xien n` rồi xuống dòng nhập dàn số (mỗi số >= 2 chữ số).\n"
        "Ví dụ:\n/xien 3\n11 22 33 44 55"
    ),
    "phongthuy": (
        "*Phong thủy theo ngày/can chi*\n"
        "Gửi ngày dương \\(vd: 2024-07-25, 25/07, 25-07-2024\\) _hoặc_ gửi trực tiếp can chi \\(Giáp Tý, Quý Hợi\\).\n"
        "Ngoài ra có thể đơn giản gõ \"hôm nay\" hoặc gửi ngày bất kỳ."
    ),
    "chotso": (
        "*Chốt số hôm nay*\n"
        "Dựa trên can chi ngày hiện tại và bộ số hạp. Không phải khuyến nghị tài chính."
    ),
}


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "\n\n".join(ASYNC_GUIDES.values())
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "menu":
        await q.edit_message_text(menu_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return
    if data == "menu_ungho":
        # Reuse handler from ungho.py
        await ung_ho_gop_y(update, context)
        return

    guide_map = {
        "menu_cang": ASYNC_GUIDES["cang"],
        "menu_dao": ASYNC_GUIDES["dao"],
        "menu_xien": ASYNC_GUIDES["xien"],
        "menu_phongthuy": ASYNC_GUIDES["phongthuy"],
        "menu_chotso": ASYNC_GUIDES["chotso"],
    }
    guide = guide_map.get(data, menu_text())
    await q.edit_message_text(guide, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]]))


# --------- /cang ---------
async def cang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ghép càng vào dàn số.
    Hỗ trợ 2 kiểu: (1) 'cang: 1 2 3' rồi xuống dòng dàn số; (2) '1,2 | 12 34 567'.
    """
    if not update.message:
        return
    text = (update.message.text or "").replace("/cang", "").strip()
    if not text:
        await update.message.reply_text(ASYNC_GUIDES["cang"], parse_mode=ParseMode.MARKDOWN)
        return

    cangs: List[str] = []
    body = text

    # Kiểu 1: cang: ... \n <dan>
    if "cang:" in text.lower():
        parts = text.split("\n", 1)
        header = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        cang_part = header.split(":", 1)[1]
        cangs = [x for x in cang_part.replace(",", " ").split() if x.isdigit() and len(x) == 1]
    # Kiểu 2: 1 2 3 | 12 34 567
    elif "|" in text:
        left, right = text.split("|", 1)
        cangs = [x for x in left.replace(",", " ").split() if x.isdigit() and len(x) == 1]
        body = right

    numbers = clean_nums_cang(body)
    if not numbers:
        await update.message.reply_text("❗ Không nhận được dàn số hợp lệ.")
        return

    cang_str = " ".join(cangs) if cangs else "0"
    res = ghep_cang(numbers, cang_str)
    # Tự chia dòng cho dễ đọc
    chunk = 25
    lines = [", ".join(res[i:i+chunk]) for i in range(0, len(res), chunk)]
    reply = "*Kết quả ghép càng:*\n" + "\n".join(lines)
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


# --------- /dao ---------
async def dao_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = (update.message.text or "").replace("/dao", "").strip()
    if not text:
        await update.message.reply_text(ASYNC_GUIDES["dao"], parse_mode=ParseMode.MARKDOWN)
        return
    target = "".join([c for c in text if c.isdigit()])
    perms = dao_so(target)
    if not perms:
        await update.message.reply_text("❗ Vui lòng gửi 1 số có 2–6 chữ số.")
        return
    chunk = 40
    lines = [", ".join(perms[i:i+chunk]) for i in range(0, len(perms), chunk)]
    await update.message.reply_text("*Các hoán vị:*\n" + "\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# --------- /xien ---------
async def xien_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    parts = (update.message.text or "").split("\n", 1)
    header = parts[0]
    body = parts[1] if len(parts) > 1 else ""

    toks = header.split()
    if len(toks) < 2:
        await update.message.reply_text(ASYNC_GUIDES["xien"], parse_mode=ParseMode.MARKDOWN)
        return
    try:
        n = int(toks[1])
    except Exception:
        await update.message.reply_text("❗ Cú pháp sai. Ví dụ: /xien 3\n11 22 33 44 55", parse_mode=ParseMode.MARKDOWN)
        return

    numbers = clean_nums_xien(body)
    combos = gen_xien(numbers, n)
    result = format_xien_result(combos)
    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)


# --------- /phongthuy ---------
async def phongthuy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = (update.message.text or "").replace("/phongthuy", "").strip()
    if not text:
        await update.message.reply_text(ASYNC_GUIDES["phongthuy"], parse_mode=ParseMode.MARKDOWN)
        return
    reply = phongthuy_tudong(text)
    await update.message.reply_text(reply)


# --------- /chotso ---------
async def chotso_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    from datetime import datetime
    today = datetime.now()
    y, m, d = today.year, today.month, today.day
    can_chi = chuan_hoa_can_chi(get_can_chi_ngay(y, m, d))
    sohap_info = sinh_so_hap_cho_ngay(can_chi)
    reply = chot_so_format(can_chi, sohap_info, today.strftime("%d-%m-%Y"))
    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


# --------- /ungho ---------
async def ungho_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ung_ho_gop_y(update, context)


# --------- Fallbacks ---------
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nhận diện nhanh một số input tự do: nếu là ngày/can chi -> phong thủy."""
    if not update.message:
        return
    t = (update.message.text or "").strip()
    # Nếu người dùng gõ "hôm nay"
    if t.lower() in {"hom nay", "hôm nay", "today"}:
        await chotso_cmd(update, context)
        return
    # Nếu có vẻ là ngày/can chi thì xử lý phong thủy
    reply = phongthuy_tudong(t)
    if not reply.startswith("❗") and not reply.startswith("❓"):
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text(menu_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())


# =========================
# Bootstrapping
# =========================

def build_application() -> Application:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing env BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cang", cang_cmd))
    app.add_handler(CommandHandler("dao", dao_cmd))
    app.add_handler(CommandHandler("xien", xien_cmd))
    app.add_handler(CommandHandler("phongthuy", phongthuy_cmd))
    app.add_handler(CommandHandler("chotso", chotso_cmd))
    app.add_handler(CommandHandler("ungho", ungho_cmd))

    # Menu callbacks
    app.add_handler(CallbackQueryHandler(menu_callback))

    # Text router (after commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    return app


def main():
    app = build_application()
    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
