from pathlib import Path
import sqlite3
from typing import Union
import unicodedata

def fever_detokenize(txt: str) -> str:
    # updated detokenize, most models are not trained with this...
    txt = txt.replace(" .", ".").replace(" ,", ",").replace(" ?", "?").replace(" :", ":").replace(" ;", ";")
    txt = txt.replace("`` ", '"').replace(" ''", '"').replace(" '", "'")
    txt = txt.replace("-LRB-", "(").replace("-RRB-", ")")
    txt = txt.replace("-LSB-", "/").replace("-RSB-", "/")
    txt = txt.replace("-COLON-", ":")
    txt = txt.replace("( ", "(").replace(" )", ")")
    return txt


def import_corpus_from_sqlite(corpus_db_file: Union[str, Path]):
    original_ids = set()
    corpus = []
    with sqlite3.connect(corpus_db_file, detect_types=sqlite3.PARSE_DECLTYPES) as connection:
        cursor = connection.cursor()
        cursor.execute(f"SELECT id, text FROM documents")
        for id_, text in cursor.fetchall():
            id_ == unicodedata.normalize("NFC", id_)
            if id_ in original_ids: # this happens sometimes due to Wiki snapshot errors...
                print(f"Original ID not unique! {id_}. Skipping...")
                continue
            
            text = unicodedata.normalize("NFC", fever_detokenize(text).strip())
            corpus.append({"id": id_, "text": text})
            original_ids.add(id_)
    return corpus