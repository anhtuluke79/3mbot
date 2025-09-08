import itertools

def clean_numbers_input(text):
    """
    Chuẩn hóa chuỗi số nhập vào, bỏ ký tự thừa, chỉ lấy số có 2 chữ số trở lên,
    tách bằng khoảng trắng, phẩy, xuống dòng.
    """
    raw = text.replace(",", " ").replace("\n", " ")
    nums = [x.strip() for x in raw.split() if x.strip().isdigit() and len(x.strip()) >= 2]
    return nums

def gen_xien(numbers, n):
    """
    Sinh tất cả tổ hợp xiên n từ dàn số.
    Trả về list tổ hợp (tuple), mỗi tổ hợp có n số, không trùng nhau.
    """
    numbers = list(dict.fromkeys(numbers))  # Loại bỏ trùng
    if len(numbers) < n:
        return []
    combos = list(itertools.combinations(numbers, n))
    return combos

def format_xien_result(combos):
    """
    Định dạng kết quả ghép xiên:
    - Các số trong tổ hợp ngăn cách bằng &
    - Các tổ hợp ngăn cách bằng dấu phẩy ,
    - Sau mỗi 20 tổ hợp thì xuống dòng
    """
    if not combos:
        return "❗ Không đủ số để ghép xiên."
    # Định dạng từng tổ hợp: 22&33&44,...
    formatted = ["&".join(combo) for combo in combos]
    # Ngắt dòng sau mỗi 20 tổ hợp
    lines = []
    for i in range(0, len(formatted), 20):
        chunk = formatted[i:i+20]
        lines.append(", ".join(chunk))
    result = "*Kết quả tổ hợp xiên:*\n" + "\n".join(lines)
    return result
