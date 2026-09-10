# Decision 0002: Day 2 experiment document

## Decision

Use the U.S. Department of Energy publication **Improving Compressed Air System Performance: A Sourcebook for Industry, Third Edition** (`DOE/EE-1340`) as the first ingestion document.

Source record: [GovInfo content details](https://www.govinfo.gov/app/details/GOVPUB-E-PURL-gpo176573). The document is government-authored, publicly accessible, 114 pages, text-extractable, and covers industrial compressed-air equipment and maintenance/performance topics.

## Why this source

- It is available from a government information repository rather than an unofficial manual mirror.
- Its structure includes a contents section, numbered sections, fact sheets, and appendices.
- It provides enough equipment-specific technical content to test page and section provenance.
- It avoids placing a questionable third-party copy of a proprietary OEM manual in the repository.

## Tradeoff

This is a government technical sourcebook, not a model-specific OEM service manual. It is suitable for testing ingestion and provenance, but it cannot answer asset-specific service questions for a particular compressor model. A later experiment should add a supplied or explicitly licensed OEM manual and test authority/asset filtering against this baseline.

The downloaded PDF is kept locally under `sample_data/raw/` and is ignored by Git. The repository stores only its manifest and a small parsed inspection sample.
