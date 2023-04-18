from itertools import repeat, takewhile
from pathlib import Path
from typing import Union

def create_parent_dir(fname: Union[str, Path]):
    pdir = Path(fname).parent
    pdir.mkdir(parents=True, exist_ok=True)

def count_file_lines(fname: Union[str, Path]):
    # based on https://stackoverflow.com/a/27518377
    with open(fname, 'rb') as f:
        bufgen = takewhile(lambda x: x, (f.raw.read(1024*1024) for _ in repeat(None)))
        return sum(buf.count(b'\n') for buf in bufgen)