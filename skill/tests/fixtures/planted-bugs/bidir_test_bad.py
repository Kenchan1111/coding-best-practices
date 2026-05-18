def prediction_limit(values, side="upper"):
    mean = sum(values) / len(values)
    if side == "upper":
        return mean + 1
    return mean + 1


def test_prediction_limit_upper():
    values = [1, 2, 3]
    assert prediction_limit(values, side="upper") > 2
