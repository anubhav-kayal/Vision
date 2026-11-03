"""Small relational schema shared by pilot repositories."""

from sqlalchemy import JSON, ForeignKey, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class OrganizationRow(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]


class SiteRow(Base):
    __tablename__ = "sites"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str]


class AssetRow(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"))
    payload: Mapped[dict] = mapped_column(JSON)


class DocumentRow(Base):
    __tablename__ = "document_revisions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"))
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"))
    payload: Mapped[dict] = mapped_column(JSON)


class SessionRow(Base):
    __tablename__ = "diagnostic_sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class EvidenceRow(Base):
    __tablename__ = "image_evidence"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("diagnostic_sessions.id"))
    payload: Mapped[dict] = mapped_column(JSON)


def database(url: str):
    engine = create_engine(url)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    return engine, sessionmaker(engine, expire_on_commit=False)
