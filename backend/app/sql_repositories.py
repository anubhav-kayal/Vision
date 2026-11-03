"""SQL repositories keep validated domain payloads separate from relational keys."""

from sqlalchemy import select

from backend.app.catalog import MODELS
from backend.app.diagnostics.models import DiagnosticSession
from backend.app.diagnostics.repository import DiagnosticSessionRepository
from backend.app.persistence import AssetRow, DocumentRow, OrganizationRow, SessionRow, SiteRow

TABLES = {"organizations": OrganizationRow, "sites": SiteRow,
          "assets": AssetRow, "documents": DocumentRow}


class SqlCatalog:
    def __init__(self, sessions):
        self.sessions = sessions

    def put(self, kind, identifier, value):
        value = MODELS[kind].model_validate(value)
        if kind == "organizations":
            fields = dict(name=value.name)
        elif kind == "sites":
            fields = dict(name=value.name, organization_id=value.organization_id)
        else:
            fields = dict(site_id=value.site_id, payload=value.model_dump(mode="json"))
            if kind == "documents":
                fields["asset_id"] = value.asset_id
        with self.sessions.begin() as session:
            session.merge(TABLES[kind](id=identifier, **fields))

    @staticmethod
    def _decode(kind, row):
        if kind == "organizations":
            data = dict(id=row.id, name=row.name)
        elif kind == "sites":
            data = dict(id=row.id, name=row.name, organization_id=row.organization_id)
        else:
            data = row.payload
        return MODELS[kind].model_validate(data)

    def get(self, kind, identifier):
        with self.sessions() as session:
            row = session.get(TABLES[kind], identifier)
            return self._decode(kind, row) if row else None

    def list(self, kind):
        with self.sessions() as session:
            return [self._decode(kind, row) for row in session.scalars(select(TABLES[kind]))]


class SqlDiagnosticSessionRepository(DiagnosticSessionRepository):
    def __init__(self, sessions):
        self.sessions = sessions

    def save(self, value):
        with self.sessions.begin() as session:
            session.merge(SessionRow(id=value.session_id, payload=value.model_dump(mode="json")))
        return value.model_copy(deep=True)

    def get(self, session_id):
        with self.sessions() as session:
            row = session.get(SessionRow, session_id)
            return DiagnosticSession.model_validate(row.payload) if row else None
