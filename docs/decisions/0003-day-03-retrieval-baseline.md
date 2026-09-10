# Decision 0003: Day 3 retrieval baseline

## Decision

Use a pure-Python TF-IDF cosine index as the first local vector-retrieval baseline. Run it against both fixed-size and section-aware chunks and return the top-k results with document, PDF page, printed page, section, text, and document metadata.

## Why this baseline

- It is deterministic and inspectable.
- It requires no API key, model download, or network call.
- It gives us a vector-space baseline before introducing dense embeddings.
- It keeps the retrieval interface independent from the eventual storage backend.

## Initial observation

On six manually written queries at top-k=5, both fixed-size and section-aware strategies hit the expected printed page in 3/6 cases. The wrong-machine query also returned generic compressed-air content instead of no results. These are baseline failures, not results to optimize away silently.

## Known limitations

- TF-IDF captures lexical overlap, not semantic similarity.
- No asset-identity or model filter is applied.
- No hybrid lexical/dense ranking or reranker exists.
- Page-hit is a coarse inspection metric; it does not prove that the returned chunk supports an answer.
