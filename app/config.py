currencies = ["E Coin", "Cash Online", "Lucky"]
course = {"E Coin": 1, "Cash Online": 2, "Lucky": 3}
categories = ["Кроссовки", "Рюкзаки", "Футболки"]
ref_reward = ""
sub_reward = ""
cur_link = ""


def convert_value(value: int, first: str, second: str) -> int:
    first_rate = course[first]
    second_rate = course[second]

    return int(value * second_rate / first_rate)
