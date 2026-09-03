import re


def normalize_whatsapp(value):
    if not value:
        return None

    number = re.sub(r"[^0-9]", "", str(value))
    if number.startswith("0"):
        number = "62" + number[1:]
    elif number.startswith("8"):
        number = "62" + number

    if not re.fullmatch(r"62\d{8,13}", number):
        return None
    return number
