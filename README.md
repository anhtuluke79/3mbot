# Telegram Bot – Railway Deploy

Bot Telegram (async) dựa trên `python-telegram-bot` v20.x. Tích hợp:
- Ghép Càng, Đảo Số
- Xiên n
- Phong thủy theo ngày/Can Chi, Chốt số hôm nay
- Ủng hộ & góp ý (hiển thị ảnh QR)

## Cấu trúc
```
.
├─ telegram_bot_main.py
├─ cang_dao.py
├─ phongthuy.py
├─ ungho.py
├─ xien.py
├─ requirements.txt
├─ Procfile
├─ railway.toml
└─ .env.sample
```

> **Lưu ý**: Nếu dùng Ủng hộ & góp ý có kèm ảnh QR, hãy đặt file `qr_ung_ho.png` cạnh `ungho.py` hoặc theo đúng đường dẫn trong mã của bạn.

## Chạy local
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export BOT_TOKEN=123456:ABC...                      # Windows PowerShell: $env:BOT_TOKEN="..."
python telegram_bot_main.py
```

## Deploy lên GitHub + Railway

### 1) Đưa mã lên GitHub
```bash
git init
git add .
git commit -m "init: telegram bot for railway"
git branch -M main
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

### 2) Tạo project trên Railway
- Vào https://railway.app, tạo New Project → **Deploy from Repo**, chọn repo vừa push.
- Railway sẽ tự build qua **Nixpacks** dựa trên `requirements.txt`.
- Vào tab **Variables** và thêm biến:
  - `BOT_TOKEN` = token của bot Telegram
- Trong tab **Services**:
  - Kiểu tiến trình: **Worker** (vì bot chạy long polling, không cần port).
  - Start command đã được chỉ định trong `Procfile`/`railway.toml` là `python telegram_bot_main.py`.

> Nếu bạn thấy Railway tạo service kiểu Web: đổi sang **Worker** hoặc xóa PORT yêu cầu. Bot *không* cần HTTP inbound khi chạy long polling.

### 3) Mẹo & sự cố thường gặp
- *Missing env BOT_TOKEN*: hãy chắc chắn đã khai báo biến môi trường trên Railway.
- *python-telegram-bot version mismatch*: bản 20.x dùng `ApplicationBuilder` & `filters`. Nếu bạn chỉnh khác, nhớ tương thích.
- *Muốn Webhook thay vì Polling*: cần 1 URL công khai + chứng chỉ/secret; khi đó sửa `main()` để `app.run_webhook(...)` và mở port Web. Với Railway đơn giản nhất là giữ **polling**.

---

Made with ❤️
