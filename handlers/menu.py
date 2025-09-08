# -*- coding: utf-8 -*-
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from handlers.ungho import ung_ho_gop_y

# ================== KEYBOARDS ==================
def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên/ Càng/ Đảo số", callback_data="ghep_xien_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("💖 Ủng hộ & Góp ý", callback_data="ung_ho_gop_y")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_xien_cang_dao_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✨ Xiên 2", callback_data="xien2"),
            InlineKeyboardButton("✨ Xiên 3", callback_data="xien3"),
            InlineKeyboardButton("✨ Xiên 4", callback_data="xien4"),
        ],
        [
            InlineKeyboardButton("🔢 Ghép càng 3D", callback_data="ghep_cang3d"),
            InlineKeyboardButton("🔢 Ghép càng 4D", callback_data="ghep_cang4d"),
        ],
        [InlineKeyboardButton("🔄 Đảo số", callback_data="dao_so")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")],
    ])

def get_back_reset_keyboard(menu_callback="menu"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Trở về", callback_data=menu_callback),
            InlineKeyboardButton("🔄 Reset", callback_data="reset"),
        ]
    ])

# ================== HANDLERS ==================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📋 *Chào mừng bạn đến với Trợ lý!*"
    if update.message:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=get_menu_keyboard(),
            parse_mode="Markdown",
        )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # Menu chính
    if data == "menu":
        await query.edit_message_text(
            "Bạn muốn làm gì tiếp?",
            reply_markup=get_menu_keyboard(),
            parse_mode="Markdown",
        )
        return

    # Xiên/Càng/Đảo
    if data == "ghep_xien_cang_dao":
        await query.edit_message_text(
            "Chọn thao tác:",
            reply_markup=get_xien_cang_dao_keyboard(),
            parse_mode="Markdown",
        )
        return

    if data in ("xien2", "xien3", "xien4"):
        n = int(data[-1])
        context.user_data["wait_for_xien_input"] = n
        await query.edit_message_text(
            f"Nhập dàn số (tách bằng khoảng trắng/phẩy). Bot sẽ ghép xiên {n}:",
            reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"),
            parse_mode="Markdown",
        )
        return

    if data == "ghep_cang3d":
        context.user_data["wait_cang3d_numbers"] = True
        await query.edit_message_text(
            "Nhập dàn số *2–3 chữ số* (cách/phẩy). Sau đó bot sẽ hỏi *càng*:",
            reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"),
            parse_mode="Markdown",
        )
        return

    if data == "ghep_cang4d":
        context.user_data["wait_cang4d_numbers"] = True
        await query.edit_message_text(
            "Nhập dàn số *3 chữ số* (cách/phẩy). Sau đó bot sẽ hỏi *càng*:",
            reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"),
            parse_mode="Markdown",
        )
        return

    if data == "dao_so":
        context.user_data["wait_for_dao_so"] = True
        await query.edit_message_text(
            "Nhập 1 số 2–6 chữ số (VD: 1234):",
            reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"),
            parse_mode="Markdown",
        )
        return

    # Phong thủy
    if data == "phongthuy":
        context.user_data["wait_phongthuy"] = True
        await query.edit_message_text(
            "Nhập ngày dương (VD: 2024-07-25 hoặc 25/07/2024) *hoặc* Can Chi (VD: Giáp Tý):",
            reply_markup=get_back_reset_keyboard("menu"),
            parse_mode="Markdown",
        )
        return

    # Ủng hộ
    if data == "ung_ho_gop_y":
        await ung_ho_gop_y(update, context)
        return

    # Hướng dẫn
    if data == "huongdan":
        hd = (
            "ℹ️ *Hướng dẫn nhanh*\n"
            "- Xiên: nhập dàn số rồi chọn Xiên 2/3/4.\n"
            "- Càng: chọn 3D/4D → nhập dàn → nhập *càng*.\n"
            "- Đảo số: nhập số 2–6 chữ số, bot trả các hoán vị.\n"
            "- Phong thủy: nhập ngày dương hoặc can chi.\n"
            "Nếu sai luồng, bấm *Reset* rồi làm lại."
        )
        await query.edit_message_text(
            hd,
            reply_markup=get_menu_keyboard(),
            parse_mode="Markdown",
        )
        return

    # Reset
    if data == "reset":
        context.user_data.clear()
        await query.edit_message_text(
            "🔄 Đã reset trạng thái!",
            reply_markup=get_menu_keyboard(),
            parse_mode="Markdown",
        )
        return

    # Fallback
    await query.edit_message_text(
        "❓ Không xác định chức năng.",
        reply_markup=get_menu_keyboard(),
        parse_mode="Markdown",
    )
