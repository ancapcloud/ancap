"""Schemas for cryopreservation desk."""
from __future__ import annotations

from pydantic import BaseModel


class CryoServicePublic(BaseModel):
    id: str
    review_target_id: str
    label: str
    price_from_acp: str
    blurb: str


class CryoPartnerPublic(BaseModel):
    id: str
    review_target_id: str
    name: str
    jurisdiction: str
    website: str
    blurb: str
    verified: bool = False
    listing_kind: str = "desk_handoff"
    clinical_endorsement: bool = False
    ethics_note: str = ""
    regulatory_note: str = ""


class CryoCatalogPublic(BaseModel):
    title: str
    tagline: str
    compliance_note: str
    services: list[CryoServicePublic]
    partners: list[CryoPartnerPublic]
    legal_href: str = "/legal/cryo-constitution"
