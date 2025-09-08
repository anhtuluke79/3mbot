# Telegram Bot – Railway (refactor, no admin & no utils stats)

Phiên bản đã **loại bỏ** `system/admin` và các mô-đun `utils` thống kê/AI.
Giữ các tính năng: Ghép Xiên/Càng/Đảo, Phong thủy, Ủng hộ.

## Cấu trúc
```
.
├─ main.py
├─ requirements.txt
├─ Procfile
├─ handlers/
│  ├─ __init__.py
│  ├─ input_handler.py
│  ├─ keyboards.py
│  ├─ menu.py
│  ├─ kq.py
│  ├─ phongthuy.py
│  ├─ ungho.py
│  ├─ xien.py
│  └─ cang_dao.py
├─ can_chi_dict.py
└─ thien_can.py
```

## Env vars (Railway → Variables)
- `BOT_TOKEN`
- `APP_URL`  (ví dụ: https://<app>.up.railway.app)

## Ghi chú
- `input_handler.py` bây giờ *không còn* decorator `log_user_action`.
- `menu.py` đã đồng bộ key trạng thái với `input_handler.py`:
  - `dao_so` → `wait_for_dao_so`
  - `kq_theo_ngay` → `wait_kq_date`
