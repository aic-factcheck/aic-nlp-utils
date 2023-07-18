from typing import List

def batch_apply(func, data, batch_size) -> List:
    n = len(data)
    first = 0
    res = []
    while first < n:
        last = min(first + batch_size, n)
        res += func(data[first:last])
        first = last
    assert n == len(res)
    return res