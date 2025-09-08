from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_menu_keyboard(user_id=None):
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép xiên (Tổ hợp số)", callback_data="ghep_xien")],
        [InlineKeyboardButton("🎯 Ghép càng/Đảo số", callback_data="ghep_cang_dao")],
        [InlineKeyboardButton("🔮 Phong thủy số (Ngày/Can chi)", callback_data="phongthuy")],
        [InlineKeyboardButton("🎲 Kết quả", callback_data="ketqua")],
        [InlineKeyboardButton("📊 (Đã tắt)", callback_data="thongke_menu")],
        [InlineKeyboardButton("💖 Ủng hộ / Góp ý", callback_data="ung_ho_gop_y")],
        [InlineKeyboardButton("ℹ️ Hướng dẫn & FAQ", callback_data="huongdan")],
        [InlineKeyboardButton("🔄 Reset trạng thái", callback_data="reset")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ketqua_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Kết quả theo ngày", callback_data="kq_theo_ngay")],
        [InlineKeyboardButton("🔥 Kết quả mới nhất", callback_data="kq_moi_nhat")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
def get_soicau_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔥 Số ra liên tục nhiều ngày", callback_data="soicau_lientuc")],
        [InlineKeyboardButton("♻️ Số gan cực đại", callback_data="soicau_ganmax")],
        [InlineKeyboardButton("🔄 Số kép", callback_data="soicau_kep")],
        [InlineKeyboardButton("⬅️ Trở về thống kê", callback_data="thongke_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_thongke_keyboard():
    keyboard = [
        [InlineKeyboardButton("📈 Top số về nhiều nhất", callback_data="topve")],
        [InlineKeyboardButton("📉 Top số về ít nhất", callback_data="topkhan")],
        [InlineKeyboardButton("🔍 Soi cầu/phân tích sâu", callback_data="soicau_menu")],
        [InlineKeyboardButton("🔢 Thống kê đầu/đuôi ĐB", callback_data="dau_cuoi")],
        [InlineKeyboardButton("♻️ Chẵn/lẻ ĐB", callback_data="chanle")],
        [InlineKeyboardButton("🚨 Dàn lô gan", callback_data="logan")],
        [InlineKeyboardButton("🤖 (Đã tắt)", callback_data="ai_rf_choose_n")],
        [InlineKeyboardButton("🎯 Gợi ý dự đoán", callback_data="goiy")],
        [InlineKeyboardButton("⬅️ Trở về", callback_data="menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
def get_ai_rf_ngay_keyboard():
    keyboard = [
        [InlineKeyboardButton("7 ngày", callback_data="ai_rf_N_7"),
         InlineKeyboardButton("14 ngày", callback_data="ai_rf_N_14")],
        [InlineKeyboardButton("21 ngày", callback_data="ai_rf_N_21"),
         InlineKeyboardButton("28 ngày", callback_data="ai_rf_N_28")],
        [InlineKeyboardButton("⬅️ Trở về thống kê", callback_data="thongke_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
def get_back_reset_keyboard(menu_callback="menu"):
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Trở về", callback_data=menu_callback),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_xien_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("✨ Xiên 2", callback_data="xien2"),
            InlineKeyboardButton("✨ Xiên 3", callback_data="xien3"),
            InlineKeyboardButton("✨ Xiên 4", callback_data="xien4")
        ],
        [
            InlineKeyboardButton("⬅️ Menu chính", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cang_dao_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔢 Ghép càng 3D", callback_data="ghep_cang3d")],
        [InlineKeyboardButton("🔢 Ghép càng 4D", callback_data="ghep_cang4d")],
        [InlineKeyboardButton("🔄 Đảo số", callback_data="dao_so")],
        [
            InlineKeyboardButton("⬅️ Menu chính", callback_data="menu"),
            InlineKeyboardButton("🔄 Reset", callback_data="reset")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
