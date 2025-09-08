# cang_dao.py
import re
from itertools import permutations
from typing import List

def _unique_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

# ---------- GHÉP CÀNG (3D/4D) ----------
def parse_cang_list(text: str) -> List[str]:
    """Lấy các 'càng' 1 chữ số, loại trùng, giữ thứ tự xuất hiện."""
    return _unique_keep_order([c for c in re.split(r"[^0-9]", text) if c and len(c) == 1])

def parse_numbers_2_3(text: str) -> List[str]:
    """Lấy dàn 2–3 chữ số từ text, mỗi token cắt tối đa 3 chữ số đầu."""
    raw = [t for t in re.split(r"[^0-9]", text) if t]
    norm = []
    for t in raw:
        if len(t) >= 2:
            t2 = t[:3]
            if len(t2) in (2, 3):
                norm.append(t2)
    return _unique_keep_order(norm)

def ghep_cang_v2(dan_2_3: List[str], cangs: List[str]) -> List[str]:
    """Ghép càng đứng TRƯỚC dàn 2–3 số → tạo 3–4 số. Nếu không có càng → mặc định '0'."""
    if not cangs:
        cangs = ["0"]
    out = []
    for c in cangs:
        for num in dan_2_3:
            if len(num) in (2, 3):
                out.append(c + num)
    return _unique_keep_order(out)

# ---------- ĐẢO SỐ ----------
def dao_so_v2(s: str) -> List[str]:
    """Mọi hoán vị đúng độ dài chuỗi s (2–6), loại trùng, sắp xếp ổn định."""
    digits = re.sub(r"[^0-9]", "", s)
    if not (2 <= len(digits) <= 6):
        return []
    perms = set("".join(p) for p in permutations(digits, len(digits)))
    return sorted(perms)

# ---------- TIỆN ÍCH FORMAT ----------
def format_list_chunks(items, per_line=25) -> str:
    """Chia list thành nhiều dòng cho dễ đọc trong Telegram."""
    return "\n".join(", ".join(items[i:i+per_line]) for i in range(0, len(items), per_line))
