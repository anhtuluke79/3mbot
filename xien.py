# xien.py
import re
import itertools
from itertools import combinations
from typing import List, Iterable, Tuple

# -----------------------
# Tiện ích chung
# -----------------------
def _unique_keep_order(seq: Iterable[str]) -> List[str]:
    """Loại trùng nhưng giữ nguyên thứ tự xuất hiện."""
    seen = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# -----------------------
# API cũ (tương thích ngược)
# -----------------------
def clean_numbers_input(text: str) -> List[str]:
    """
    Chuẩn hóa chuỗi số nhập vào, bỏ ký tự thừa, chỉ lấy số có 2 chữ số trở lên,
    tách bằng khoảng trắng, phẩy, xuống dòng.
    """
    raw = text.replace(",", " ").replace("\n", " ")
    nums = [x.strip() for x in raw.split()
            if x.strip().isdigit() and len(x.strip()) >= 2]
    return _unique_keep_order(nums)

def gen_xien(numbers: List[str], n: int) -> List[Tuple[str, ...]]:
    """
    Sinh tổ hợp xiên n từ dàn số (trả về list tuple).
    Loại trùng phần tử đầu vào theo thứ tự xuất hiện.
    """
    numbers = _unique_keep_order(numbers)
    if n < 2 or len(numbers) < n:
        return []
    combos = list(itertools.combinations(numbers, n))
    return combos

def format_xien_result(combos: List[Tuple[str, ...]]) -> str:
    """
    Định dạng kết quả ghép xiên (kiểu cũ):
    - Các số trong một tổ hợp ngăn cách bằng '&'
    - Các tổ hợp ngăn cách bằng ', '
    - Sau mỗi 20 tổ hợp thì xuống dòng
    """
    if not combos:
        return "❗ Không đủ số để ghép xiên."
    formatted = ["&".join(combo) for combo in combos]
    lines = []
    for i in range(0, len(formatted), 20):
        chunk = formatted[i:i+20]
        lines.append(", ".join(chunk))
    result = "*Kết quả tổ hợp xiên:*\n" + "\n".join(lines)
    return result


# -----------------------
# API mới (đang dùng trong bot)
# -----------------------
def clean_numbers_for_xien(text: str) -> List[str]:
    """Lấy các mục >= 2 chữ số để ghép xiên; loại trùng, giữ thứ tự xuất hiện."""
    nums = [t for t in re.split(r"[^0-9]", text) if len(t) >= 2]
    return _unique_keep_order(nums)

def gen_xien_v2(nums: List[str], n: int) -> List[str]:
    """
    Sinh tổ hợp xiên n theo đúng thứ tự xuất hiện (chỉ cho n = 2, 3, 4).
    Trả về list chuỗi với định dạng 'a&b' (xiên 2), 'a&b&c' (xiên 3), 'a&b&c&d' (xiên 4).
    """
    if n not in {2, 3, 4}:
        return []  # chỉ hỗ trợ xiên 2/3/4 theo yêu cầu
    nums = _unique_keep_order([x for x in nums if len(x) >= 2])
    if len(nums) < n:
        return []
    return ["&".join(c) for c in combinations(nums, n)]
