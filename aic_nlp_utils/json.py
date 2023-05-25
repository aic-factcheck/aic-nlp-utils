from pathlib import Path
from tqdm.autonotebook import tqdm
from typing import Any, Callable, List, Optional, Sequence, Union
import ujson

from .files import create_parent_dir, count_file_lines

def read_json(fname: Union[str, Path]) -> Any:
    """Import JSON file.

    Args:
        fname (Union[str, Path]): JSON file path

    Returns:
        Any: JSON representation
    """
    with open(fname, 'r') as json_file:
        data = ujson.load(json_file)
    return data


def read_jsonl(jsonl: Union[str, Path], show_progress: bool=False) -> List:
    """Imports JSONL file.

    Args:
        jsonl (Union[str, Path]): JSONL file path
        show_progress (bool, optional): Show progress bar. Defaults to False.

    Returns:
        List: list of JSON representations per each line
    """
    with open(jsonl, 'r') as jsonl_file:
        data = []
        iter = tqdm(jsonl_file, unit_scale=True) if show_progress else jsonl_file
        for jline in iter:
            rec = ujson.loads(jline)
            data.append(rec)
    return data


def write_json(fname: Union[str, Path], data: Any, indent: int=3, mkdir: bool=False) -> None:
    """Writes JSON file as UTF8.

    Args:
        fname (Union[str, Path]): JSON file path
        data (Any): Data to write
        indent (int, optional): Indent characters. Defaults to 3.
        mkdir (bool, optional): Create parent directory if not exists. Defaults to False.
    """
    if mkdir:
        create_parent_dir(fname)
    with open(str(fname), 'w', encoding='utf8') as json_file:
        ujson.dump(data, json_file, ensure_ascii=False, indent=indent, default=str)


def write_jsonl(jsonl: Union[str, Path], data: Sequence, mkdir: bool=False, show_progress: bool=False) -> None:
    """Writes JSON file as UTF8.

    Args:
        jsonl (Union[str, Path]): JSONL file path
        data (Sequence): Data to write
        mkdir (bool, optional): Create parent directory if not exists. Defaults to False. Defaults to False.
        show_progress (bool, optional): Show progress bar. Defaults to False.
    """
    if mkdir:
        create_parent_dir(jsonl)
    # data is an iterable (list) of JSON-compatible structures (OrderedDict)
    with open(jsonl, 'w', encoding='utf8') as json_file:
        iter = tqdm(data) if show_progress else data
        for r in iter:
            ujson.dump(r, json_file, ensure_ascii=False, default=str)
            json_file.write("\n")


def process_to_lines(data: Sequence,
                     func: Callable,
                     fname: Union[str, Path],
                     bufsize: int = 1,
                     total: Optional[int]=None,
                     pfunc: Callable=lambda e: e, 
                     cont: bool=True, 
                     mkdir: bool=True, 
                     show_progress: bool=True) -> None:
    """Processes sequential `data` items `e` with `pfunc(func(e))`and stores each result as a file in `fname` file.

    Args:
        data (Sequence): Source sequential data.
        func (Callable): Function to apply to each `data` element.
        fname (Union[str, Path]): Output file name.
        bufsize (int, optional): The file is continually written after `bufsize line are created`. Defaults to 1.
        total (Optional[int], optional): Hint to number of `data` elements. If `len(data)` exists it is inferred automatically. Defaults to None.
        pfunc (Callable): Function applied post `func` aimed at getting formatted string. Defaults to `lambda e: e`.
        cont (bool, optional): Continue partially finished processing? Defaults to True.
        mkdir (bool, optional): Create `fname` parent directory? Defaults to True.
        show_progress (bool, optional): Show `tqdm` progress bars. Defaults to True.

    Raises:
        FileExistsError: If `cont == False` and the file already exist this exception is raised.
    """        
    assert bufsize > 0, bufsize
    fname = Path(fname)

    if total is None:
        try:
            total = len(data)
        except:
            pass

    mode = "w"
    start = 0
    buf = []

    if fname.is_file():
        if cont:
            start = count_file_lines(fname)
            print(f"{fname} exists ({start} lines)")
        else:
            raise FileExistsError(f"file {fname} exists! Use cont=True to continue.")
        mode = "a"
    if mkdir:
        create_parent_dir(fname)

    with open(fname, mode) as f:
        data = iter(data)
        if start > 0:
            pbar = tqdm(total=start, desc="skipping") if show_progress else None
            for i in range(start):
                next(data)
                pbar is None or pbar.update(1)
            pbar is None or pbar.close()

        if total is None or start < total:
            pbar = tqdm(data, initial=start, total=total, desc="processing") if show_progress else None
            for rec in data:
                buf.append(pfunc(func(rec)))
                if len(buf) == bufsize:
                    for l in buf:
                        f.write(l)
                        f.write("\n")
                    f.flush()
                    buf = []
                pbar is None or pbar.update(1)
            pbar is None or pbar.close()
            if len(buf) > 0:
                for l in buf:
                    f.write(l)
                    f.write("\n")
                f.flush()

def process_to_jsonl(*args, **kwargs):
    """Calls `process_to_lines` with `pfunc` transforming data to JSON formatted strings.
    """    
    kwargs["pfunc"] = lambda e: ujson.dumps(e, ensure_ascii=False, default=str)
    process_to_lines(*args, **kwargs)