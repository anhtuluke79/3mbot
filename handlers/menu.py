from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import pandas as pd
from datetime import datetime
from dateutil import parser
from handlers.cang_dao import clean_numbers_input as clean_numbers_cang
from handlers.xien import clean_numbers_input as clean_numbers_xien
from handlers.ungho import ung_ho_gop_y
# (Không còn import admin/utils)

# ================== KEYBOARDS ==================
def get_menu_keyboard(user_id=None):
    keyboard = [
                [InlineKeyboardButton("🔢 Ghép xiên/ Càng/ Đảo số", callback_data="ghep_xien_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số", callback_data="phongthuy")],
        [InlineKeyboardButton("💖 Ủng hộ & Góp ý", callback_data="ung_ho_gop_y")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ketqua_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Kết quả theo ngày", callback_data="kq_theo_ngay")],
        [InlineKeyboardButton("🔥 Kết quả mới nhất", callback_data="kq_moi_nhat")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ])

def get_xien_cang_dao_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Xiên 2", callback_data="xien2"),
         InlineKeyboardButton("✨ Xiên 3", callback_data="xien3"),
         InlineKeyboardButton("✨ Xiên 4", callback_data="xien4")],
        [InlineKeyboardButton("🔢 Ghép càng 3D", callback_data="ghep_cang3d"),
         InlineKeyboardButton("🔢 Ghép càng 4D", callback_data="ghep_cang4d")],
        [InlineKeyboardButton("🔄 Đảo số", callback_data="dao_so")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ])

def get_back_reset_keyboard(menu_callback="menu"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Trở về", callback_data=menu_callback),
         InlineKeyboardButton("🔄 Reset", callback_data="reset")]
    ])

# =========== FORMAT KQ XSMB ===========

def tra_ketqua_theo_ngay(date_text):
    try:
        df = pd.read_csv('xsmb.csv')
    except Exception as e:
        return f"❗ Không đọc được dữ liệu xsmb.csv: {e}"
    try:
        sample = df['date'].astype(str).iloc[0]
        if '-' in sample and len(sample.split('-')[0]) == 4:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        else:
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    except Exception:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if 'DB' in df.columns:
        df['DB'] = df['DB'].astype(str).str.zfill(5)
    try:
        d = parser.parse(date_text, dayfirst=True).date()
    except Exception:
        return "❗ Định dạng ngày không hợp lệ. Ví dụ: 2024-07-25 hoặc 25/07/2024"
    row = df[df['date'].dt.date == d]
    if row.empty:
        return f"❗ Không có dữ liệu cho ngày {d.strftime('%d-%m-%Y')}"
    r = row.iloc[0]
    ngay_str = d.strftime('%d-%m-%Y')
    return format_xsmb_ketqua(r, ngay_str)

def tra_ketqua_moinhat():
    try:
        df = pd.read_csv('xsmb.csv')
        date_examples = df['date'].astype(str).head(3).tolist()
        if all('-' in d and len(d.split('-')[0]) == 4 for d in date_examples):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        else:
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        df['DB'] = df['DB'].astype(str).str.zfill(5)
        row = df.sort_values('date', ascending=False).iloc[0]
        ngay_str = row['date'].strftime('%d-%m-%Y')
        return format_xsmb_ketqua(row, ngay_str)
    except Exception as e:
        return f"❗ Lỗi tra cứu: {e}"

# ============= MENU & CALLBACKS =============
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = "📋 *Chào mừng bạn đến với Trợ lý Xổ số!*"
    if update.message:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=get_menu_keyboard(user_id),
            parse_mode="Markdown"
        )

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    # Menu chính
    if data == "menu":
        await query.edit_message_text("Bạn muốn làm gì tiếp?", reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")
        return

        if data == "kq_theo_ngay":
        context.user_data["wait_kq_date"] = True
        await query.edit_message_text("Nhập ngày (VD: 2024-07-25 hoặc 25/07/2024):", reply_markup=get_back_reset_keyboard("ketqua"), parse_mode="Markdown")
        return
    if data == "kq_moi_nhat":
        text = tra_ketqua_moinhat()
        await query.edit_message_text(text, reply_markup=get_ketqua_keyboard(), parse_mode="Markdown")
        return

    # Xiên/Càng/Đảo
    if data == "ghep_xien_cang_dao":
        await query.edit_message_text("Chọn thao tác:", reply_markup=get_xien_cang_dao_keyboard(), parse_mode="Markdown")
        return
    if data in ("xien2", "xien3", "xien4"):
        n = int(data[-1])
        context.user_data["wait_for_xien_input"] = n
        await query.edit_message_text(f"Nhập dàn số (tách bằng khoảng trắng/phẩy). Bot sẽ ghép xiên {n}:", reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"), parse_mode="Markdown")
        return
    if data == "ghep_cang3d":
        context.user_data["wait_cang3d_numbers"] = True
        await query.edit_message_text("Nhập dàn số *2 hoặc 3 chữ số* (tách khoảng trắng/phẩy). Sau đó bot sẽ hỏi càng:", reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"), parse_mode="Markdown")
        return
    if data == "ghep_cang4d":
        context.user_data["wait_cang4d_numbers"] = True
        await query.edit_message_text("Nhập dàn số *3 chữ số* (tách khoảng trắng/phẩy). Sau đó bot sẽ hỏi càng:", reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"), parse_mode="Markdown")
        return
    if data == "dao_so":
        context.user_data["wait_for_dao_so"] = True
        await query.edit_message_text("Nhập 1 số bất kỳ (2-6 chữ số, VD: 1234):", reply_markup=get_back_reset_keyboard("ghep_xien_cang_dao"), parse_mode="Markdown")
        return

    # Phong thủy
    if data == "phongthuy":
        await query.edit_message_text("Nhập ngày dương (VD: 2024-07-25, 25/07/2024) *hoặc* nhập trực tiếp Can Chi (VD: Giáp Tý):", reply_markup=get_back_reset_keyboard("menu"), parse_mode="Markdown")
        context.user_data["wait_phongthuy"] = True
        return

    # Ủng hộ
    if data == "ung_ho_gop_y":
        await ung_ho_gop_y(update, context)
        return

    # Hướng dẫn
    if data == "huongdan":
        hd = (
            "ℹ️ *Hướng dẫn nhanh*\n"
            "- Xiên: nhập dàn số (22 33 44 ...) rồi chọn Xiên 2/3/4.\n"
            "- Càng: chọn Ghép càng 3D/4D, nhập dàn, sau đó nhập *càng* (1 chữ số).\n"
            "- Đảo số: nhập số 2-6 chữ số, bot trả mọi hoán vị.\n"
            "- KQ: chọn KQ theo ngày hoặc KQ mới nhất (cần file xsmb.csv).\n"
            "- Phong thủy: nhập ngày dương hoặc can chi."
        )
        await query.edit_message_text(hd, reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")
        return

    # Reset
    if data == "reset":
        context.user_data.clear()
        await query.edit_message_text("🔄 Đã reset trạng thái!", reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")
        return

    # Fallback
    await query.edit_message_text("❓ Không xác định chức năng.", reply_markup=get_menu_keyboard(user_id), parse_mode="Markdown")
