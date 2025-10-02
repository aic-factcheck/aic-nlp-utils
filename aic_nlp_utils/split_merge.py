import re
from typing import List, Iterator, Tuple

from langchain_text_splitters.markdown import ExperimentalMarkdownSyntaxTextSplitter

# https://chatgpt.com/share/68dd2919-44d0-800b-be0a-7f57f9d75c43

EN_ABBREVIATIONS = [
    # Titles
    "Mr", "Mrs", "Ms", "Mx", "Dr", "Prof", "Rev", "Hon", "Sr", "Jr",
    "St", "Gen", "Col", "Maj", "Capt", "Lt", "Sgt", "Adm",

    # Academic & professional degrees
    "PhD", "Ph.D", "M.D", "MD", "B.Sc", "M.Sc", "B.A", "M.A", "LL.B", "J.D",
    "D.D.S", "D.O", "Ed.D", "Psy.D", "M.B.A", "B.Com", "B.Eng",

    # Common text abbreviations
    "etc", "e.g", "i.e", "vs", "cf", "viz", "al", "approx", "ca",
    "p.s", "P.S", "a.k.a", "aka",

    # Months (abbreviated)
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov", "Dec",

    # Time
    "a.m", "p.m", "A.M", "P.M",

    # Units & measures
    "ft", "in", "lb", "oz", "pt", "gal", "mm", "cm", "km", "kg", "mg",
    "ml", "L", "Hz", "kHz", "MHz", "GHz", "°C", "°F",

    # Organizations & geography
    "U.S", "U.K", "U.N", "E.U", "N.A.T.O", "O.E.C.D", "Inc", "Co", "Ltd", "Corp", "Univ",
    "Dept", "Mt", "Ft", "Rd", "Ave", "Blvd", "Sq", "Ctr"
]


CS_ABBREVIATIONS = [
    # Academic & professional titles
    "Ing", "Mgr", "Ph.D", "PhD", "Bc", "JUDr", "RNDr", "doc", "prof", "MUDr",
    "PaedDr", "ThDr", "PhDr", "MVDr", "DrSc", "CSc", "DiS", "RSDr", "MBA",

    # Military / ranks
    "plk", "pplk", "npor", "por", "kpt", "mjr", "gen", "brig", "rtm",

    # Common Czech text abbreviations
    "tj", "např", "atd", "apod", "aj", "resp", "př", "tzv", "mjr", "čj", "čp",
    "č", "obr", "tab", "str", "příl", "pozn", "zkr", "odd", "kap",

    # Organizations & institutions
    "ČR", "ČSR", "ČSFR", "ČSSR", "SR", "EU", "OSN", "SNP", "ÚV", "AV", "UK",
    "SVJ", "OV", "MŠMT", "MF", "MZV", "ČNB",

    # Company / legal abbreviations
    "s.r.o", "a.s", "v.o.s", "o.p.s", "n.o", "spol", "z.s", "a spol",

    # Months
    "led", "ún", "břez", "dub", "květ", "červ", "srp", "září", "říj", "list", "pros",

    # Miscellaneous
    "čl", "bod", "odst", "§", "pozn"
]

ABBREVIATIONS = EN_ABBREVIATIONS + CS_ABBREVIATIONS


def split_paragraphs(text: str) -> List[str]:
    """
    Splits text into paragraphs while preserving exact reconstruction.
    A "paragraph" is defined as a block ending with one or more newlines.
    
    Guarantee: ''.join(split_paragraphs(text)) == text
    """
    if not text:
        return []
    
    # Keep delimiters by splitting on regex that captures them
    import re
    parts = re.split(r'(\n+)', text)
    
    # Merge text + delimiters so reconstruction is exact
    result = []
    buf = ""
    for part in parts:
        if not part:
            continue
        buf += part
        if part.startswith("\n"):  # newline signals end of paragraph
            result.append(buf)
            buf = ""
    if buf:  # trailing text without newline
        result.append(buf)
        
    assert ''.join(result) == text
    return result


def split_sentences(text: str) -> List[str]:
    """
    Sentence splitter with:
    - abbreviation support
    - exact reconstruction (''.join(...) == text)
    - no sentence starts with whitespace except first
    - leading whitespace moved to end of previous sentence
    TODO: optimize for large number of ABBREVIATIONS!
    """
    if not text:
        return []

    # Pattern for sentence-ending punctuation
    sentence_end_re = re.compile(r'[.!?]+(?=(\s|$|[\]\)])|\[\[)')

    result = []
    start = 0

    for match in sentence_end_re.finditer(text):
        end = match.end()
        chunk = text[start:end]

        # Check if punctuation is part of an abbreviation
        abbrev_ok = False
        for abbr in ABBREVIATIONS:
            if text[max(0, end-len(abbr)-1):end-1] == abbr:
                abbrev_ok = True
                break

        if abbrev_ok:
            continue  # don't split, move on

        # Move leading whitespace to previous sentence (except first)
        if result and chunk and chunk[0].isspace():
            result[-1] += chunk[0]  # move whitespace to end of previous
            chunk = chunk[1:]

        result.append(chunk)
        start = end

    # Add trailing text
    if start < len(text):
        chunk = text[start:]
        if result and chunk and chunk[0].isspace():
            result[-1] += chunk[0]
            chunk = chunk[1:]
        result.append(chunk)

    # Verify exact reconstruction
    assert "".join(result) == text, "Split/join mismatch!"
    return result


def split_chars(text: str, maxLength: int) -> List[str]:
    """
    Splits text into chunks of at most maxLength characters while preserving exact reconstruction.
    
    Guarantee: ''.join(split_chars(text, maxLength)) == text
    """
    if not text:
        return []
    
    if maxLength <= 0:
        raise ValueError("maxLength must be > 0")
    
    result = []
    for i in range(0, len(text), maxLength):
        result.append(text[i:i+maxLength])
    
    assert ''.join(result) == text
    return result


def merge_chunks_greedy(
    lengths: List[int],
    maxLength: int
) -> List[List[int]]:
    """
    Forward greedy: pack as much as possible into each segment
    without exceeding maxLength.
    - Oversize single chunks stay alone.
    """
    n = len(lengths)
    i = 0
    out = []
    while i < n:
        seg_sum = lengths[i]
        j = i
        if seg_sum > maxLength:
            # oversize chunk → alone
            out.append([i])
            i += 1
            continue
        while j + 1 < n and seg_sum + lengths[j+1] <= maxLength:
            seg_sum += lengths[j+1]
            j += 1
        out.append(list(range(i, j+1)))
        i = j + 1
    return out


class AbstractDocumentNode:
    def __init__(self) -> None:
        pass
    
    def children(self) -> List["AbstractDocumentNode"]:
        """Returns all children of this node"""
        raise NotImplementedError()
    
    def len(self) -> int:
        """Returns the sum length of the text represented by the whole subtree"""
        raise NotImplementedError()
    
    def text(self) -> str:
        """Returns the text of the whole subtree."""
        raise NotImplementedError()
    
    def print_tree(self, indent=0) -> None:
        raise NotImplementedError()
    
    def collapse(self):
        raise NotImplementedError()
            

class LeafDocumentNode(AbstractDocumentNode):
    def __init__(self, doc: str) -> None:
        super().__init__()
        self.doc = doc
        
    def children(self) -> List["AbstractDocumentNode"]:
        return []
        
    def len(self) -> int:
        return len(self.doc)
        
    def text(self) -> str:
        return self.doc

    def __repr__(self) -> str:
        return f"LeafDocumentNode(doc_len={len(self.doc)})"

    def print_tree(self, indent=0, idx=0) -> None:
        prefix = "    " * indent
        snippet = self.text().replace("\n", " ")[:30]
        print(f"{prefix}- ({idx}): '{snippet}'")
        for child in self.children():
            child.print_tree(indent + 1, idx)
            
    def collapse(self):
        return self
            

class InnerDocumentNode(AbstractDocumentNode):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self._children: List["AbstractDocumentNode"] = []
        
    def children(self) -> List["AbstractDocumentNode"]:
        return self._children
    
    def len(self) -> int:
        return sum(c.len() for c in self._children)
    
    def text(self) -> str:
        return ''.join(c.text() for c in self._children)
    
    def add_child(self, child: "AbstractDocumentNode") -> None:
        self._children.append(child)
        
    def set_child(self, child: "AbstractDocumentNode", idx: int) -> None:
        self._children[idx] = child

    def __repr__(self) -> str:
        return f"InnerDocumentNode(name={self.name!r}, children={len(self._children)})"
   
    def _iter_leaves(
        self, parent: "InnerDocumentNode" = None
    ) -> Iterator[Tuple["LeafDocumentNode", "InnerDocumentNode", int]]:
        for idx, child in enumerate(self._children):
            if isinstance(child, LeafDocumentNode):
                yield (child, self, idx)
            else:
                yield from child._iter_leaves(parent=self) 
                
    def iter_leaves(self) -> Iterator[Tuple["LeafDocumentNode", "InnerDocumentNode", int]]:
        yield from self._iter_leaves(self)
    
    def print_tree(self, indent=0, idx=0) -> None:
        prefix = "    " * indent
        print(f"{prefix}- {self.name} ({idx})")
        for idx, child in enumerate(self.children()):
            child.print_tree(indent + 1, idx)
            
    def collapse(self):
        return LeafDocumentNode(doc=self.text())
    
    
def split_md(node: AbstractDocumentNode) -> InnerDocumentNode:
    splitter = ExperimentalMarkdownSyntaxTextSplitter(strip_headers=False)
    chunks = splitter.split_text(node.text())

    root = InnerDocumentNode("ROOT")
    
    # Stack to track the current path in the hierarchy
    # Each element is (level, header_name, node)
    stack: List[tuple[int, str, InnerDocumentNode]] = [(0, "ROOT", root)]
    
    for chunk in chunks:
        metadata = chunk.metadata
        content = chunk.page_content
        
        # Build the full header path for this chunk
        headers = {}
        for key in ['Header 1', 'Header 2', 'Header 3', 'Header 4', 'Header 5', 'Header 6']:
            if key in metadata:
                level = int(key.split()[-1])
                headers[level] = metadata[key]
        
        if not headers:
            # No header, this is a root-level content
            leaf = LeafDocumentNode(content)
            root.add_child(leaf)
            continue
        
        # Get the deepest header level in this chunk
        max_level = max(headers.keys())
        
        # Pop stack until we're at the right level to add this section
        while len(stack) > 1 and stack[-1][0] >= max_level:
            stack.pop()
        
        # Build the path from parent to the deepest level
        for level in range(stack[-1][0] + 1, max_level + 1):
            parent_level, parent_name, parent_node = stack[-1]
            
            if level in headers:
                # This level has a real header
                header_name = headers[level]
                
                # Check if this section already exists in the stack
                if len(stack) > level and stack[level][0] == level and stack[level][1] == header_name:
                    # Section already exists, just continue
                    continue
                
                # Create new section node
                section_node = InnerDocumentNode(header_name)
                parent_node.add_child(section_node)
                
                # Adjust stack: remove everything beyond parent, then add this node
                stack = stack[:level]
                stack.append((level, header_name, section_node))
            else:
                # Missing level, add dummy
                dummy = InnerDocumentNode("DUMMY")
                parent_node.add_child(dummy)
                stack = stack[:level]
                stack.append((level, "DUMMY", dummy))
        
        # Add the content as a leaf node to the deepest section
        leaf = LeafDocumentNode(content)
        stack[-1][2].add_child(leaf)
        
    return root



def split_node(node: AbstractDocumentNode|str, maxLength: int) -> AbstractDocumentNode:
    # Hierarchically decompose the Markdown
    # goes by splittin sections of increasing levels -> paragraphs -> sentences -> characters
    
    if isinstance(node, str):
        node = LeafDocumentNode(node)
        
    root = split_md(node)
    assert root.text() == node.text()
    
    # Now split all leaves so none is longer than maxLen
    # Split based on paragraphs -> sentences -> characters
    split_stages = [
        ("PAR", split_paragraphs), 
        ("SNT", split_sentences),
        ("CHR", split_chars)
    ]
    for stage, split_fn in split_stages:
        # print(stage)
        n_splits = 0
        for leaf, parent, cidx in root.iter_leaves():
            if leaf.len() > maxLength:
                chunks = split_fn(leaf.text())
                lengths = [len(c) for c in chunks]
                segments = merge_chunks_greedy(lengths, maxLength=maxLength)
                merged_splits = [''.join([chunks[sidx] for sidx in seg]) for seg in segments]
                assert leaf.text() == ''.join(merged_splits)
            
                # create node representing a list of merged splits
                inner_node = InnerDocumentNode(stage)
                for ms in merged_splits:
                    inner_node.add_child(LeafDocumentNode(ms))
                    
                # replace original with that
                parent.set_child(inner_node, cidx)
                
                n_splits += 1
        # print(f"#splits: {n_splits}")
        
    long_leaves = [leaf for leaf in root.iter_leaves() if leaf[0].len() > maxLength]
    assert len(long_leaves) == 0, "Some leaves still too long! This should never happen!"
    
    assert root.text() == node.text(), "Split/join mismatch!"
    return root


def split_node_to_list(node: AbstractDocumentNode|str, maxLength: int):
    root = split_node(node, maxLength=maxLength)
    return [leaf[0].text() for leaf in root.iter_leaves()]
