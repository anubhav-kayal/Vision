# Pilot Day 1 — Identity and evidence contracts

## Implemented

- Optional engine, alternator, and controller identifiers on assets and retrieval contexts.
- Asset identity defaults to `ASSET_UNCONFIRMED`.
- Recording `ASSET_CONFIRMED` requires an identity reference. This is structural
  validation; a future trusted service must validate that reference and its issuer.
- Image evidence metadata records session, asset, uploader, storage key, MIME type,
  size, SHA-256 hash, and upload time.
- Vision observation drafts retain their image reference, remain unverified, and
  always require confirmation. Unsupported fields and numeric confidence are rejected.
- Existing diagnostic and safety enum values remain compatible. Existing API
  request/assessment response models are reused rather than duplicated.

## Verification

- 79 tests passed (39 existing plus 40 new parameterized cases).
- Week 1 retrieval evaluation remains at 80% hit rate and 0% correct refusal;
  cases 009–012 still fail. A successful runner exit does not mean all cases pass.
- Week 2 diagnostic evaluation retains 100% on its small 15-case deterministic set.
- Python compilation and diff validation are required before commit.

## Pending

- Image bytes are not uploaded, decoded, stored, or analyzed yet. Metadata validation
  does not prove MIME type, hash correctness, ownership, or session/asset association.
- No asset-confirmation authorization or document-applicability policy is implemented.
- Existing generic observation input still accepts verification labels; the new
  restricted draft is the intended boundary for future vision adapters only.
- Existing evidence verification/correction values are preserved; the plan's display
  tags must later map to these values rather than changing persisted enums.
- The next milestone is repository-backed asset/document records and migrations.
- Generator facts and playbooks require an authorized manual and domain review.
