"""Pilot identity must survive retrieval-context conversion without implying approval."""

import pytest
from pydantic import ValidationError

from backend.app.models import Asset, AssetContext, AssetStatus


def asset_data(**changes):
    return dict(
        asset_id="pilot-001", manufacturer="Example OEM",
        equipment_family="diesel_generator", model="fixture-model", **changes,
    )


def test_legacy_asset_is_unconfirmed():
    asset = Asset(**asset_data())
    assert asset.asset_status is AssetStatus.ASSET_UNCONFIRMED
    assert AssetContext.from_asset(asset).engine_model is None


def test_component_identity_round_trip():
    asset = Asset(**asset_data(
        engine_model="engine-fixture", alternator_manufacturer="Example Alternator",
        alternator_model="alternator-fixture", controller_model="controller-fixture",
        asset_status="ASSET_CONFIRMED", identity_reference="inspection-record-001",
    ))
    context = AssetContext.model_validate_json(AssetContext.from_asset(asset).model_dump_json())
    for name in (
        "engine_model", "alternator_manufacturer", "alternator_model", "controller_model",
        "asset_status", "identity_reference",
    ):
        assert getattr(context, name) == getattr(asset, name)


@pytest.mark.parametrize("model,data", [(Asset, asset_data()), (AssetContext, {})])
def test_confirmation_requires_reference(model, data):
    with pytest.raises(ValidationError, match="identity_reference"):
        model(**data, asset_status="ASSET_CONFIRMED")


@pytest.mark.parametrize("status", list(AssetStatus))
def test_status_round_trip(status):
    asset = Asset(**asset_data(asset_status=status, identity_reference="record-001"))
    assert Asset.model_validate_json(asset.model_dump_json()).asset_status is status


@pytest.mark.parametrize("changes", [
    {"engine_model": " "}, {"alternator_model": ""}, {"controller_model": " "},
    {"asset_status": "APPROVED_TO_OPERATE"}, {"identity_reference": " "},
])
def test_invalid_identity_rejected(changes):
    with pytest.raises(ValidationError):
        Asset(**asset_data(**changes))
