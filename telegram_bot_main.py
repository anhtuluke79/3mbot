import os
import logging
import re
from itertools import combinations, permutations
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
from cang_dao import clean_numbers_input as clean_nums_cang  # dùng chuẩn hoá từ module cũ
from phongthuy import (
    phongthuy_tudong,
    get_can_chi_ngay,
    chuan_hoa_can_chi,
    sinh_so_hap_cho_ngay,
    chot_so_format,
)
from ungho import ung_ho_gop_y
from xien import clean_numbers_input as clean_nums_xien  # chỉ dùng nếu muốn tái sử dụng

# =========================
# Logging
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# Helpers & Session state
# =========================
# mode: None|cang3d|cang4d|dao|xien|phongthuy
USER_MODE_KEY = "mode"
USER_XIEN_N_KEY = "xien_n"
USER_PENDING_NUMS = "pending_nums"   # dàn 2 số (3D) hoặc 3 số (4D)

# ---- Core helpers (mới) cho càng / đảo / xiên ----

def _unique_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def parse_cang_list(text: str):
    """Lấy các 'càng' 1 chữ số, loại trùng, giữ thứ tự."""
    return _unique_keep_order([c for c in re.split(r"[^0-9]", text) if c and len(c) == 1])

def parse_numbers_2_3(text: str):
    """Lấy dàn 2-3 chữ số từ text, cắt tối đa 3 chữ số đầu cho mỗi token."""
    raw = [t for t in re.split(r"[^0-9]", text) if t]
    norm = []
    for t in raw:
        if len(t) >= 2:
            t2 = t[:3]
            if len(t2) in (2, 3):
                norm.append(t2)
    return _unique_keep_order(norm)

def ghep_cang_v2(dan_2_3: List[str], cangs: List[str]):
    """Ghép càng đứng TRƯỚC dàn 2-3 số → tạo 3-4 số. Nếu không có càng → mặc định '0'."""
    if not cangs:
        cangs = ["0"]
    out = []
    for c in cangs:
        for num in dan_2_3:
            if len(num) in (2, 3):
                out.append(c + num)
    return _unique_keep_order(out)

def dao_so_v2(s: str):
    """Mọi hoán vị đúng độ dài chuỗi s (2–6), loại trùng, sắp xếp ổn định."""
    digits = re.sub(r"[^0-9]", "", s)
    if not (2 <= len(digits) <= 6):
        return []
    perms = set("".join(p) for p in permutations(digits, len(digits)))
    return sorted(perms)

def clean_numbers_for_xien(text: str):
    """Các mục >= 2 chữ số để ghép xiên; loại trùng, giữ thứ tự xuất hiện."""
    nums = [t for t in re.split(r"[^0-9]", text) if len(t) >= 2]
    return _unique_keep_order(nums)

def gen_xien_v2(nums: List[str], n: int):
    if not (2 <= n <= 10):
        return []
    if len(nums) < n:
        return []
    return ["-".join(c) for c in combinations(nums, n)]

def format_list_chunks(items, per_line=25):
    return "\n".join(", ".join(items[i:i+per_line]) for i in range(0, len(items), per_line))

# =========================
# UI
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

def cang_submenu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("3D", callback_data="menu_cang3d"),
         InlineKeyboardButton("4D", callback_data="menu_cang4d")],
        [InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")],
    ])

def menu_text() -> str:
    return (
        "👋 *Chào mừng đến với trợ lý số!*\n\n"
        "Chọn tính năng bên dưới hoặc dùng các lệnh:\n"
        "• /cang3d – Ghép càng 3D theo 2 bước\n"
        "• /cang4d – Ghép càng 4D theo 2 bước\n"
        "• /dao – Đảo số (hoán vị 2–6 chữ số)\n"
        "• /xien – Ghép xiên n từ dàn\n"
        "• /phongthuy – Tra phong thủy ngày/can chi\n"
        "• /chotso – Gợi ý chốt số theo ngày hiện tại\n"
        "• /ungho – Ủng hộ & góp ý\n"
        "• /help – Hướng dẫn chi tiết"
    )

# =========================
# Guides
# =========================
ASYNC_GUIDES = {
    "cang3d": (
        "*Ghép Càng 3D*\n"
        "Bước 1: nhập dàn 2 số, ví dụ: `23 32, 34,43 45 75`\n"
        "Bước 2: nhập càng (1 chữ số), ví dụ: `1 2,3`\n"
        "→ Kết quả: 1+23→123, 1+32→132, 1+34→134, 1+43→143, ...\n"
    ),
    "cang4d": (
        "*Ghép Càng 4D*\n"
        "Bước 1: nhập dàn 3 số, ví dụ: `123 321 345`\n"
        "Bước 2: nhập càng (1 chữ số), ví dụ: `1 2`\n"
        "→ Kết quả: 1+123→1123, 2+345→2345, ...\n"
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
        "Gửi ngày dương (2024-07-25, 25/07/2024, ...) *hoặc* gửi trực tiếp can chi (Giáp Tý, Quý Hợi).\n"
        "Ngoài ra có thể gõ \"hôm nay\"."
    ),
    "chotso": (
        "*Chốt số hôm nay*\n"
        "Dựa trên can chi ngày hiện tại và bộ số hạp. Không phải khuyến nghị tài chính."
    ),
}

# =========================
# Command Handlers
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # reset mode when /start
    context.user_data[USER_MODE_KEY] = None
    context.user_data[USER_XIEN_N_KEY] = None
    context.user_data[USER_PENDING_NUMS] = None
    if update.message:
        await update.message.reply_text(menu_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[USER_MODE_KEY] = None
    context.user_data[USER_XIEN_N_KEY] = None
    context.user_data[USER_PENDING_NUMS] = None
    text = "\n\n".join(ASYNC_GUIDES.values())
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "menu":
        context.user_data[USER_MODE_KEY] = None
        context.user_data[USER_XIEN_N_KEY] = None
        context.user_data[USER_PENDING_NUMS] = None
        await q.edit_message_text(menu_text(), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        return
    if data == "menu_ungho":
        context.user_data[USER_MODE_KEY] = None
        await ung_ho_gop_y(update, context)
        return
    if data == "menu_cang":
        context.user_data[USER_MODE_KEY] = None
        context.user_data[USER_PENDING_NUMS] = None
        await q.edit_message_text("*Chọn loại ghép càng*", parse_mode=ParseMode.MARKDOWN, reply_markup=cang_submenu())
        return
    if data == "menu_cang3d":
        context.user_data[USER_MODE_KEY] = "cang3d"
        context.user_data[USER_PENDING_NUMS] = None
        await q.edit_message_text(ASYNC_GUIDES["cang3d"], parse_mode=ParseMode.MARKDOWN, reply_markup=cang_submenu())
        return
    if data == "menu_cang4d":
        context.user_data[USER_MODE_KEY] = "cang4d"
        context.user_data[USER_PENDING_NUMS] = None
        await q.edit_message_text(ASYNC_GUIDES["cang4d"], parse_mode=ParseMode.MARKDOWN, reply_markup=cang_submenu())
        return
    if data == "menu_phongthuy":
        context.user_data[USER_MODE_KEY] = "phongthuy"
        await q.edit_message_text(ASYNC_GUIDES["phongthuy"], parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]]))
        return
    if data == "menu_chotso":
        context.user_data[USER_MODE_KEY] = None
        # gọi trực tiếp chốt số
        fake_update = Update(update.update_id, message=q.message)  # reuse message field
        await chotso_cmd(fake_update, context)
        return
    if data == "menu_xien":
        context.user_data[USER_MODE_KEY] = "xien"
        context.user_data[USER_XIEN_N_KEY] = None
        await q.edit_message_text(ASYNC_GUIDES["xien"], parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]]))
        return
    if data == "menu_dao":
        context.user_data[USER_MODE_KEY] = "dao"
        await q.edit_message_text(ASYNC_GUIDES["dao"], parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Trở về menu", callback_data="menu")]]))
        return

# --------- /cang3d & /cang4d (lệnh tắt) ---------
async def cang3d_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[USER_MODE_KEY] = "cang3d"
    context.user_data[USER_PENDING_NUMS] = None
    if update.message:
        await update.message.reply_text(ASYNC_GUIDES["cang3d"], parse_mode=ParseMode.MARKDOWN)

async def cang4d_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data[USER_MODE_KEY] = "cang4d"
    context.user_data[USER_PENDING_NUMS] = None
    if update.message:
        await update.message.reply_text(ASYNC_GUIDES["cang4d"], parse_mode=ParseMode.MARKDOWN)

# --------- /dao ---------
async def dao_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = (update.message.text or "").replace("/dao", "").strip()
    if not text:
        context.user_data[USER_MODE_KEY] = "dao"
        await update.message.reply_text(ASYNC_GUIDES["dao"], parse_mode=ParseMode.MARKDOWN)
        return
    target = "".join([c for c in text if c.isdigit()])
    perms = dao_so_v2(target)
    if not perms:
        await update.message.reply_text("❗ Vui lòng gửi 1 số có 2–6 chữ số.")
        return
    await update.message.reply_text("*Các hoán vị:*\n" + format_list_chunks(perms, 40), parse_mode=ParseMode.MARKDOWN)

# --------- /xien ---------
async def xien_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    parts = (update.message.text or "").split("\n", 1)
    header = parts[0]
    body = parts[1] if len(parts) > 1 else ""

    toks = header.split()
    if len(toks) < 2:
        # bật chế độ nhập xiên theo 2 bước
        context.user_data[USER_MODE_KEY] = "xien"
        context.user_data[USER_XIEN_N_KEY] = None
        await update.message.reply_text(ASYNC_GUIDES["xien"], parse_mode=ParseMode.MARKDOWN)
        return
    try:
        n = int(toks[1])
    except Exception:
        await update.message.reply_text("❗ Cú pháp sai. Ví dụ: /xien 3\n11 22 33 44 55", parse_mode=ParseMode.MARKDOWN)
        return

    numbers = clean_numbers_for_xien(body)
    combos = gen_xien_v2(numbers, n)
    if not combos:
        await update.message.reply_text("❗ Dàn số chưa đủ để ghép xiên hoặc n không hợp lệ.")
        return
    await update.message.reply_text(f"*Kết quả xiên {n}:*\n" + format_list_chunks(combos, 20), parse_mode=ParseMode.MARKDOWN)

# --------- /phongthuy ---------
async def phongthuy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = (update.message.text or "").replace("/phongthuy", "").strip()
    if not text:
        context.user_data[USER_MODE_KEY] = "phongthuy"
        await update.message.reply_text(ASYNC_GUIDES["phongthuy"], parse_mode=ParseMode.MARKDOWN)
        return
    reply = phongthuy_tudong(text)
    await update.message.reply_text(reply)

# --------- /chotso ---------
async def chotso_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # cho phép gọi từ menu_callback (reuse message)
    msg = update.message or getattr(update, "effective_message", None)
    if not msg:
        return
    today = datetime.now()
    y, m, d = today.year, today.month, today.day
    can_chi = chuan_hoa_can_chi(get_can_chi_ngay(y, m, d))
    sohap_info = sinh_so_hap_cho_ngay(can_chi)
    reply = chot_so_format(can_chi, sohap_info, today.strftime("%d-%m-%Y"))
    await msg.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

# --------- /ungho ---------
async def ungho_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ung_ho_gop_y(update, context)

# --------- Text router (free text) ---------
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Định tuyến text theo chế độ người dùng.
    - 3D/4D: nhập dàn → nhập càng → trả kết quả.
    - Xiên: hỗ trợ dạng 'n=3' + dàn, hoặc dùng lệnh /xien n.
    - 'hôm nay' khi không ở mode nào -> chốt số.
    """
    if not update.message:
        return
    t = (update.message.text or "").strip()
    mode = context.user_data.get(USER_MODE_KEY)

    # Lối tắt chốt số
    if not mode and t.lower() in {"hom nay", "hôm nay", "today"}:
        await chotso_cmd(update, context)
        return

    # CANG 3D/4D – 2 bước
    if mode == "cang3d" or mode == "cang4d":
        # Bước 1: nhận dàn
        if not context.user_data.get(USER_PENDING_NUMS):
            nums = parse_numbers_2_3(t)
            want_len = 2 if mode == "cang3d" else 3
            nums = [x for x in nums if len(x) == want_len]
            if not nums:
                await update.message.reply_text("❗ Hãy nhập dàn số đúng định dạng (2 số cho 3D, 3 số cho 4D).")
                return
            context.user_data[USER_PENDING_NUMS] = nums
            await update.message.reply_text("Đã nhận dàn số. Bây giờ gửi *càng* (ví dụ: `1 2,3`).", parse_mode=ParseMode.MARKDOWN)
            return
        # Bước 2: nhận càng
        cangs = parse_cang_list(t)
        if not cangs:
            await update.message.reply_text("❗ Không đọc được càng. Ví dụ: `1 2,3`.")
            return
        nums = context.user_data.get(USER_PENDING_NUMS) or []
        res = ghep_cang_v2(nums, cangs)
        # reset
        context.user_data[USER_PENDING_NUMS] = None
        await update.message.reply_text("*Kết quả ghép:*\n" + format_list_chunks(res, 25), parse_mode=ParseMode.MARKDOWN)
        return

    # ĐẢO SỐ ở mode dao: nhập số là chạy
    if mode == "dao":
        target = "".join(ch for ch in t if ch.isdigit())
        perms = dao_so_v2(target)
        if not perms:
            await update.message.reply_text("❗ Vui lòng gửi 1 số có 2–6 chữ số.")
            return
        await update.message.reply_text("*Các hoán vị:*\n" + format_list_chunks(perms, 40), parse_mode=ParseMode.MARKDOWN)
        return

    # XIÊN n – 2 bước: n=... rồi dàn
    if mode == "xien":
        if t.lower().startswith("n="):
            try:
                context.user_data[USER_XIEN_N_KEY] = int(t.split("=", 1)[1])
                await update.message.reply_text("Đã nhận n. Bây giờ gửi dàn số.")
            except Exception:
                await update.message.reply_text("Không đọc được n, ví dụ: n=3")
            return
        n = context.user_data.get(USER_XIEN_N_KEY)
        if n:
            combos = gen_xien_v2(clean_numbers_for_xien(t), n)
            if not combos:
                await update.message.reply_text("❗ Dàn số chưa đủ để ghép xiên.")
                return
            await update.message.reply_text(f"*Kết quả xiên {n}:*\n" + format_list_chunks(combos, 20), parse_mode=ParseMode.MARKDOWN)
            return
        else:
            await update.message.reply_text("Bạn chưa đặt n. Gửi ví dụ: n=3")
            return

    # PHONG THỦY mode: mọi text → tra phong thủy
    if mode == "phongthuy":
        reply = phongthuy_tudong(t)
        await update.message.reply_text(reply)
        return

    # Mặc định: trả menu
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
    app.add_handler(CommandHandler("cang3d", cang3d_cmd))
    app.add_handler(CommandHandler("cang4d", cang4d_cmd))
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
