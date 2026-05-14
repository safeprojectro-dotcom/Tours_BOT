"""Stable Admin HTTP path strings for read-model navigation (B16D1.1)."""


def supplier_offer_prepare_conversion_chain_plan_path(offer_id: int) -> str:
    return f"/admin/supplier-offers/{offer_id}/prepare-conversion-chain/plan"


__all__ = ["supplier_offer_prepare_conversion_chain_plan_path"]
