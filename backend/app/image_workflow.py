"""Local image intake validates bytes before storage; observations need confirmation."""

import hashlib
import io
import warnings
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError

from backend.app.diagnostics.evidence import ImageEvidence, VisualObservationDraft
from backend.app.diagnostics.models import Observation, ObservationType
from backend.app.persistence import EvidenceRow
from backend.app.providers import ProviderFailure

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MIME_FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}


class LocalObjectStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root) or path == self.root:
            raise ValueError("invalid storage key")
        return path

    def put(self, key, data):
        with self.path(key).open("xb") as output:
            output.write(data)

    def get(self, key):
        return self.path(key).read_bytes()


class ImageWorkflow:
    def __init__(self, sessions, diagnostics, store, vision=None):
        self.sessions, self.diagnostics, self.store, self.vision = sessions, diagnostics, store, vision

    def upload(self, session_id, data, media_type, uploaded_by):
        session = self.diagnostics.get_session(session_id)
        if not data or len(data) > MAX_IMAGE_BYTES or media_type not in MIME_FORMATS:
            raise ValueError("unsupported image type or size")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as image:
                    if image.format != MIME_FORMATS[media_type] or image.width * image.height > 20000000:
                        raise ValueError("image type mismatch or excessive resolution")
                    image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
                Image.DecompressionBombWarning) as exc:
            raise ValueError("invalid image bytes") from exc
        key = uuid4().hex
        metadata = ImageEvidence(
            evidence_id=key, session_id=session_id, asset_id=session.asset.asset_id,
            storage_key=key, content_sha256=hashlib.sha256(data).hexdigest(),
            media_type=media_type, size_bytes=len(data), uploaded_by=uploaded_by,
        )
        draft, reason = None, "VISION_NOT_CONFIGURED"
        if self.vision:
            try:
                draft = self.vision.observe(key, data, media_type, session.asset.model_dump_json())
                draft = VisualObservationDraft.model_validate(draft.model_dump())
                if draft.evidence_id != key:
                    raise ProviderFailure("IMAGE_REFERENCE_MISMATCH")
                reason = "CONFIRM_OBSERVATION"
            except ProviderFailure:
                reason = "VISION_UNAVAILABLE_OR_INVALID"
        self.store.put(key, data)
        payload = dict(metadata=metadata.model_dump(mode="json"),
                       draft=draft.model_dump(mode="json") if draft else None,
                       reason=reason, confirmed=False)
        with self.sessions.begin() as db:
            db.add(EvidenceRow(id=key, session_id=session_id, payload=payload))
        return payload

    def get(self, session_id, evidence_id):
        self.diagnostics.get_session(session_id)
        with self.sessions() as db:
            row = db.get(EvidenceRow, evidence_id)
            if row is None or row.session_id != session_id:
                raise KeyError("image evidence not found")
            return dict(row.payload)

    def confirm(self, session_id, evidence_id, description, parameter, confirmed_by):
        payload = self.get(session_id, evidence_id)
        if payload["confirmed"]:
            raise ValueError("image evidence already confirmed")
        observation = Observation(
            observation_id=f"image-{evidence_id}", type=ObservationType.VISUAL,
            parameter=parameter, value=description, source=f"image:{evidence_id};by:{confirmed_by}",
        )
        result = self.diagnostics.add_observation(session_id, observation)
        payload.update(confirmed=True, confirmed_by=confirmed_by, observation=observation.model_dump(mode="json"))
        with self.sessions.begin() as db:
            db.merge(EvidenceRow(id=evidence_id, session_id=session_id, payload=payload))
        return result
