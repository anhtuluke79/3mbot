# xien.py
import re
from itertools import combinations
from typing import List

def _unique_keep_order(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def clean_numbers_for_xien(text: str) -> List[str]:
    """Lấy các mục >= 2 chữ số để ghép xiên; loại trùng, giữ thứ tự xuất hiện."""
    nums = [t for t in re.split(r"[^0-9]", text) if len(t) >= 2]
    return _unique_keep_order(nums)

def gen_xien_v2(nums: List[str], n: int) -> List[str]:
    """Sinh tổ hợp xiên n theo đúng thứ tự xuất hiện, mỗi mục ở dạng 'a-b-...'"""
    if not (2 <= n <= 10):
        return []
    if len(nums) < n:
        return []
    return ["-".join(c) for c in combinations(nums, n)]
        chunk = formatted[i:i+20]
        lines.append(", ".join(chunk))
    result = "*Kết quả tổ hợp xiên:*\n" + "\n".join(lines)
    return result
