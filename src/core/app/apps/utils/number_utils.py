def number_format(num) -> str:
    return f"{num:,.2f}"


def amount_format(num):
    if num % 1 == 0:
        return int(num)
    else:
        return num
