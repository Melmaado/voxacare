import re
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from download_protocols import PROTOCOLS_DIR, SOURCES
from collections import Counter
import hashlib
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_mistralai import MistralAIEmbeddings
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

load_dotenv()

COMMON_WORDS = {
    "fr": {"de", "la", "le", "les", "et", "des", "à", "en", "du", "un", "une", "est", "pour", "par"},
    "nl": {"de", "het", "een", "en", "van", "in", "is", "op", "te", "voor", "met", "die", "dat", "niet"},
    "en": {"the", "of", "and", "to", "in", "a", "is", "for", "on", "with", "that", "by", "as", "be"},
    "de": {"der", "die", "das", "und", "in", "zu", "den", "von", "ist", "mit", "nicht", "für", "auf", "ein"},
    "es": {"de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para"},
}

FRENCH_STOPWORDS = frozenset("""
a à au aux avec ce ces cet cette c d dans de des du elle elles en est et
être il ils j je l la le les leur leurs lui m ma mais me mes moi mon n ne
nous on ou où par pas pour qu que qui s sa se ses son sont sur t ta te
tes toi ton tu un une vos votre vous y
""".split())

def readable(text: str, lang: str) -> bool:
    words = re.findall(r"\w+", text.lower())
    if not words:
        return False
    return sum(w in COMMON_WORDS[lang] for w in words) / len(words) > 0.05

def clean(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()

def load_pages() -> list[Document]:
    pages = []
    for source in SOURCES:
        path = PROTOCOLS_DIR / source["file"]
        raw = [page.extract_text() or "" for page in PdfReader(path).pages]
        normalize = lambda line: re.sub(r"\d+", "#", line.strip())
        line_counts = Counter(normalize(line) for text in raw for line in set(text.splitlines()) if line.strip())
        repeated = {line for line, n in line_counts.items() if len(raw) >= 5 and n > len(raw)/2}
        rejected = 0
        for number, text in enumerate(raw, start=1):
            kept = [line for line in text.splitlines()
                    if normalize(line) not in repeated and not line.strip().isdigit()]
            text = clean("\n".join(kept))
            if len(text) < 200:
                continue
            if not readable(text, source["lang"]):
                rejected += 1
                continue
            pages.append(Document(page_content=text,
                                  metadata={"title": source["title"], "year": source["year"],
                                            "file": source["file"], "page": number,
                                            "lang": source["lang"]}))
        if rejected:
            print(f"WARNING: {rejected} unreadable page(s) skipped in {source['file']}")
    return pages

def split(pages: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150,
                                              separators=["\n\n", "\n", ". ", " ", ""])
    return splitter.split_documents(pages)

INDEX_PATH = PROTOCOLS_DIR / "index.json"
FINGERPRINT_PATH = PROTOCOLS_DIR / "index.fingerprint"
embeddings = MistralAIEmbeddings(model="mistral-embed")

def fingerprint(chunks: list[Document]) -> str:
    h = hashlib.sha256()
    for chunk in chunks:
        h.update(chunk.page_content.encode())
        h.update(str(chunk.metadata).encode())
    return h.hexdigest()

def build_index(chunks: list[Document]) -> InMemoryVectorStore:
    fp = fingerprint(chunks)
    if INDEX_PATH.exists() and FINGERPRINT_PATH.exists() and FINGERPRINT_PATH.read_text() == fp:
        return InMemoryVectorStore.load(str(INDEX_PATH), embeddings)
    store = InMemoryVectorStore(embeddings)
    store.add_documents(chunks)
    store.dump(str(INDEX_PATH))
    FINGERPRINT_PATH.write_text(fp)
    return store

TOKEN = re.compile(r"\w+")

def tokenize(text: str, drop: frozenset = frozenset()) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in drop]

class Retriever:
    def __init__(self, stopwords: bool = False):
        self.drop = FRENCH_STOPWORDS if stopwords else frozenset()
        self.chunks = split(load_pages())
        self.store = build_index(self.chunks)
        self.bm25 = BM25Okapi([tokenize(c.page_content) for c in self.chunks])

    def dense(self, question: str, k: int) -> list[Document]:
        return self.store.similarity_search(question, k=k)
    
    def lexical(self, question: str, k: int) -> list[Document]:
        scores = self.bm25.get_scores(tokenize(question, self.drop))
        best = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.chunks[i] for i in best]

    def hybrid(self, question: str, k: int = 4, candidates: int = 20, c: int = 60) -> list[Document]:
        scores, docs = {}, {}
        for ranking in (self.dense(question, candidates), self.lexical(question, candidates)):
            for rank, doc in enumerate(ranking, start=1):
                key = doc.page_content
                scores[key] = scores.get(key, 0) + 1 / (c + rank)
                docs[key] = doc
        best = sorted(scores, key=scores.get, reverse=True)[:k]
        return [docs[key] for key in best]

if __name__ == "__main__":
    retriever = Retriever()
    print(len(retriever.chunks), "chunks indexed")
    question = "Que faire quand un patient tousse pendant le repas ?"
    for name, results in [("dense", retriever.dense(question, 4)),
                          ("bm25", retriever.lexical(question, 4)),
                          ("hybrid", retriever.hybrid(question))]:
        print(f"\n--- {name} ---")
        for doc in results:
            print(f"{doc.metadata['file']} p.{doc.metadata['page']}: {doc.page_content[:80]!r}")