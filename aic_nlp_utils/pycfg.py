from argparse import ArgumentParser
from pathlib import Path
from pprint import pformat
import shutil
from typing import Callable, Dict, Optional, Union

from .files import create_parent_dir


def parse_pycfg_args():
    parser = ArgumentParser()
    parser.add_argument('pycfg', type=str)
    return parser.parse_args()


def read_pycfg(pycfg: Union[str, Path], save_dir_fn: Optional[Callable]=None) -> Dict:
    print(f"Reading Python config: {pycfg}")
    d = {}
    config_py = Path(pycfg)
    exec(config_py.read_text(), d) # read an execute the python config file
    cfg = d["config"]() # this method must be defined by the config file
    if save_dir_fn is not None:
        fdir = Path(save_dir_fn(cfg))
        fname = Path(fdir, "config.py")
        create_parent_dir(fname)
        print(f"Writing the evaluated Python config backup to: {fname}")
        Path(fname).write_text(pformat(cfg, indent=3, sort_dicts=False))
        fname_orig = Path(fdir, "config.orig.py")
        print(f"Copying the original Python config backup to: {fname_orig}")
        shutil.copy(config_py, fname_orig)
    return cfg