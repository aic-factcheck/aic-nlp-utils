from collections.abc import Iterable
from typing import List

from tqdm.autonotebook import tqdm

def batch_apply(func, data, batch_size: int, show_progress: bool=False) -> List:
    # the output is always a list
    n = len(data)
    n_batches = (n + batch_size - 1) // batch_size
    
    def ranges():
        first = 0
        while first < n:
            last = min(first + batch_size, n)
            yield (first, last)
            first = last
    
    res = []
    ranges_ = ranges()
    iter_ = tqdm(ranges_, total=n_batches) if show_progress else ranges_
    for f, l in iter_:
        r = func(data[f:l])
        if not isinstance(r, Iterable):
            r = [r]
        elif not isinstance(r, list):
            r = list(r)
        res += r
    return res