import re
from itertools import permutations

def clean_numbers_input(text):
    """Chuẩn hóa input, lấy ra các số (dàn 2 hoặc 3 số) từ text."""
    numbers = re.split(r"[ ,;\n]+", text.strip())
    return [s.lstrip('0').zfill(2) if len(s.lstrip('0')) == 1 else s.zfill(3) if len(s) == 3 else s for s in numbers if s.isdigit() and 2 <= len(s) <= 3]

def ghep_cang(numbers, cang):
    """
    Ghép càng vào đầu các số trong dàn.
    - numbers: list các số (dàn 2 hoặc 3 số)
    - cang: string chứa 1 hoặc nhiều càng (1 số, hoặc nhiều số cách nhau dấu cách/phẩy)
    """
    cangs = [x for x in re.split(r"[ ,;\n]+", str(cang).strip()) if x.isdigit() and len(x) == 1]
    if not cangs:
        cangs = ["0"]
    res = []
    for cg in cangs:
        for n in numbers:
            # Nếu n có 2 số -> càng + 2 số => 3D, nếu n có 3 số -> càng + 3 số => 4D
            res.append(f"{cg}{n.zfill(3)}" if len(n) == 3 else f"{cg}{n.zfill(2)}")
    return sorted(set(res))

def dao_so(s):
    """Tạo tất cả hoán vị số (2-6 chữ số)."""
    s = str(s)
    if not s.isdigit() or not (2 <= len(s) <= 6):
        return []
    return sorted(set(["".join(p) for p in permutations(s)]))
