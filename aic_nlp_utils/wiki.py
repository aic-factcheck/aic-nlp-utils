from collections import defaultdict, Counter, OrderedDict
import html
from pathlib import Path
import re

from lxml.html.clean import Cleaner
from tqdm import tqdm

from .json import read_jsonl, write_jsonl
from .encoding import nfc

def _filter_and_fix_wiki_extract(root_dir, min_length, textcol="text", remove_re=None, file_names="**"):
    # min_length - shorter pages (text) are removed
    # remove_re - matching pages (text) are removed
    records = []
    glob_str = f"**/{file_names}"
    print(glob_str)
    source_jsonls = sorted(Path(root_dir).glob(glob_str))
    for source_json in tqdm(source_jsonls):
        for r in read_jsonl(source_json):
            r["original_id"] = int(r["id"])
            r["id"] = r["title"].strip()
            r["text"] = html.unescape(r[textcol].strip())
            if textcol != "text":
                del r[textcol]
            r["id"] = nfc(r["id"])
            r["title"] = nfc(r["title"])
            r["text"] = nfc(r["text"])
            records.append(r)
    print(f"# all: {len(records)}")
    cntr = Counter((r["text"] for r in records))
    records = [r for r in records if cntr[r["text"]] == 1]
    print(f"# without duplicate texts: {len(records)}")
    records = [r for r in records if len(r["text"]) >= min_length]
    print(f"# without short texts: {len(records)}")
    if remove_re:
        pattern = re.compile(remove_re)
        records = [r for r in tqdm(records) if not re.match(pattern, r["text"])]
        print(f"# without text removed based on RE: {len(records)}")
    return records

def _fix_html(records, kill_tags, remove_tags, remove_text):
    cleaner = Cleaner(page_structure=False, links=False, kill_tags=kill_tags, remove_tags=remove_tags)
    TAG_RE = re.compile(r'<[^>]+>')

    n_html = 0
    n_unfixed = 0
    n_err = 0
    for r in tqdm(records):
        for rt in remove_text:
            r["text"] = r["text"].replace(rt, "")
        if "<" in r["text"]: # simple rough tag detection
            n_html += 1
            try:
                r["text"] = cleaner.clean_html(r["text"])
            except:
                n_err += 1
            r["text"] = TAG_RE.sub('', r["text"]).strip()
            if "<" in r["text"]:
                n_unfixed += 1
    print(f"# fixed HTML: {n_html}, remaining: {n_unfixed}, errors: {n_err}")
    return records


def filter_and_fix_wiki_extract_for_lang(root_dir, output_jsonl, lang, textcol="text", file_names="**"):
    assert lang in ["cs", "en", "pl", "sk"]
    remove_text = []
    if lang == "cs":
        min_length = 10
        remove_re = r"\#PŘESMĚRUJ[^\n]*|\#REDIRECT[^\n]*|\#redirect[^\n]*"
        kill_tags = ["id", "minor", "ns", "parentid", "timestamp", "contributor", "comment", "model", "format", "templatestyles"]
        remove_tags = ["revision"]
        remove_text = ["Externí odkazy.", "Odkazy.", "Reference.", "Literatura.", "Související články.", '"V tomto článku byl použit textu z článku ."', ': | | | | |', ': | | | |', ': | | |', ': | |', ': |', '• \xa0 \xa0 • • • •', '"V tomto článku byly použity textů z článků']
    elif lang == "en":
        min_length = 10
        remove_re=r"[^\n]* refers? to:?$|[^\n]* stands? for:?$|[^\n]*\n.* refers? to:?$|[^\n]*refers? to:\n[^\n]*|[^\n]*the following:?$|[^\n]* mean:?$|[^\n]* be:$|[^\n]* is:$|\#REDIRECT[^\n]*"
        kill_tags = ["ref", "onlyinclude"]
        remove_tags = []
    elif lang == "pl":
        min_length = 30
        remove_re=r"[^\n]* to:$|\#PATRZ[^\n]*|[^\n]* może oznaczać:$"
        kill_tags = []
        remove_tags  = ["poem"]
        remove_text = ["\right]</math>"]
    elif lang == "sk":
        min_length = 10
        remove_re=r"[^\n]* je:?$|[^\n]* môže byť:?$"
        kill_tags = ["indicator"]
        remove_tags  = []
        remove_text = ['je zatiaľ „“. Pomôž Wikipédii tým, že ho [ doplníš a rozšíriš.]"']

    records = _filter_and_fix_wiki_extract(root_dir, min_length, remove_re=remove_re, textcol=textcol, file_names=file_names)
    records = _fix_html(records, kill_tags, remove_tags, remove_text)
    write_jsonl(output_jsonl, records)
    return records
