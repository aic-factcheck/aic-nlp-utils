from pathlib import Path
from typing import Any, Sequence, Union
import ujson

def _create_parent_dir(fname):
    pdir = Path(fname).parent
    pdir.mkdir(parents=True, exist_ok=True)


def read_json(fname: Union[str, Path]) -> Any:
    with open(fname, 'r') as json_file:
        data = ujson.load(json_file)
    return data


def read_jsonl(jsonl: Union[str, Path]) -> Any:
    with open(jsonl, 'r') as json_file:
        data = []
        for jline in json_file:
            rec = ujson.loads(jline)
            data.append(rec)
    return data


def write_json(fname: Union[str, Path], data: Any, indent: int=3, mkdir:bool=False) -> None:
    if mkdir:
        _create_parent_dir(fname)
    with open(str(fname), 'w', encoding='utf8') as json_file:
        ujson.dump(data, json_file, ensure_ascii=False, indent=indent, default=str)


def write_jsonl(jsonl: Union[str, Path], data: Sequence, mkdir: bool=False) -> None:
    if mkdir:
        _create_parent_dir(jsonl)
    # data is an iterable (list) of JSON-compatible structures (OrderedDict)
    with open(jsonl, 'w', encoding='utf8') as json_file:
        for r in data:
            ujson.dump(r, json_file, ensure_ascii=False, default=str)
            json_file.write("\n")

