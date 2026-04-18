"""Track 5b.3a: supplier RFQ response commercial policy validation + effective resolver."""

from __future__ import annotations

from types import SimpleNamespace
from unittest import TestCase

import pytest
from pydantic import ValidationError

from app.models.enums import (
    CommercialResolutionKind,
    CustomMarketplaceRequestStatus,
    SupplierCustomRequestResponseKind,
    SupplierOfferPaymentMode,
    TourSalesMode,
)
from app.schemas.custom_marketplace import SupplierCustomRequestResponseUpsert
from app.services.effective_commercial_execution_policy import (
    EffectiveCommercialExecutionPolicyService,
    validate_supplier_declared_rfq_commercial_pair,
)


class SupplierDeclaredRfqPolicyValidationTests(TestCase):
    def test_full_bus_platform_checkout_rejected(self) -> None:
        with pytest.raises(ValueError, match="full_bus"):
            validate_supplier_declared_rfq_commercial_pair(
                sales_mode=TourSalesMode.FULL_BUS,
                payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            )

    def test_per_seat_platform_ok(self) -> None:
        validate_supplier_declared_rfq_commercial_pair(
            sales_mode=TourSalesMode.PER_SEAT,
            payment_mode=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
        )

    def test_full_bus_assisted_ok(self) -> None:
        validate_supplier_declared_rfq_commercial_pair(
            sales_mode=TourSalesMode.FULL_BUS,
            payment_mode=SupplierOfferPaymentMode.ASSISTED_CLOSURE,
        )

    def test_proposed_upsert_requires_policy_fields(self) -> None:
        with pytest.raises(ValidationError, match="supplier_declared"):
            SupplierCustomRequestResponseUpsert(
                response_kind=SupplierCustomRequestResponseKind.PROPOSED,
                supplier_message="Hello",
                quoted_price=None,
                quoted_currency=None,
            )

    def test_declined_must_not_set_policy_fields(self) -> None:
        with pytest.raises(ValidationError, match="Declined"):
            SupplierCustomRequestResponseUpsert(
                response_kind=SupplierCustomRequestResponseKind.DECLINED,
                supplier_message="No",
                supplier_declared_sales_mode=TourSalesMode.PER_SEAT,
            )


class EffectiveCommercialExecutionPolicyResolverTests(TestCase):
    def _resolve(
        self,
        *,
        tour_sales_mode: TourSalesMode,
        resp_sales: TourSalesMode,
        resp_payment: SupplierOfferPaymentMode,
        request_status: CustomMarketplaceRequestStatus = CustomMarketplaceRequestStatus.SUPPLIER_SELECTED,
        resolution_kind: CommercialResolutionKind | None = None,
        resp_kind: SupplierCustomRequestResponseKind = SupplierCustomRequestResponseKind.PROPOSED,
        sales_null: bool = False,
        pay_null: bool = False,
    ):
        tour = SimpleNamespace(sales_mode=tour_sales_mode)
        req = SimpleNamespace(status=request_status, commercial_resolution_kind=resolution_kind)
        resp = SimpleNamespace(
            response_kind=resp_kind,
            supplier_declared_sales_mode=None if sales_null else resp_sales,
            supplier_declared_payment_mode=None if pay_null else resp_payment,
        )
        return EffectiveCommercialExecutionPolicyService.resolve(tour=tour, request=req, response=resp)

    def test_per_seat_platform_and_tour_allows_self_service(self) -> None:
        r = self._resolve(
            tour_sales_mode=TourSalesMode.PER_SEAT,
            resp_sales=TourSalesMode.PER_SEAT,
            resp_payment=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
        )
        self.assertTrue(r.self_service_hold_allowed)
        self.assertTrue(r.platform_checkout_allowed)
        self.assertFalse(r.assisted_only)
        self.assertIsNone(r.blocked_code)

    def test_per_seat_tour_supplier_assisted_blocks_self_service(self) -> None:
        r = self._resolve(
            tour_sales_mode=TourSalesMode.PER_SEAT,
            resp_sales=TourSalesMode.PER_SEAT,
            resp_payment=SupplierOfferPaymentMode.ASSISTED_CLOSURE,
        )
        self.assertFalse(r.self_service_hold_allowed)
        self.assertFalse(r.platform_checkout_allowed)
        self.assertTrue(r.assisted_only)
        self.assertEqual(r.blocked_code, "supplier_commercial_intent_blocks_self_service")

    def test_per_seat_supplier_platform_full_bus_tour_blocks(self) -> None:
        r = self._resolve(
            tour_sales_mode=TourSalesMode.FULL_BUS,
            resp_sales=TourSalesMode.PER_SEAT,
            resp_payment=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
        )
        self.assertFalse(r.self_service_hold_allowed)
        self.assertFalse(r.platform_checkout_allowed)
        self.assertEqual(r.blocked_code, "tour_sales_mode_blocks_self_service")

    def test_external_resolution_blocks_platform_checkout(self) -> None:
        r = self._resolve(
            tour_sales_mode=TourSalesMode.PER_SEAT,
            resp_sales=TourSalesMode.PER_SEAT,
            resp_payment=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            request_status=CustomMarketplaceRequestStatus.CLOSED_EXTERNAL,
            resolution_kind=CommercialResolutionKind.EXTERNAL_RECORD,
        )
        self.assertTrue(r.external_only)
        self.assertFalse(r.platform_checkout_allowed)
        self.assertFalse(r.self_service_hold_allowed)
        self.assertEqual(r.blocked_code, "external_record")

    def test_incomplete_supplier_policy_blocks(self) -> None:
        r = self._resolve(
            tour_sales_mode=TourSalesMode.PER_SEAT,
            resp_sales=TourSalesMode.PER_SEAT,
            resp_payment=SupplierOfferPaymentMode.PLATFORM_CHECKOUT,
            sales_null=True,
        )
        self.assertFalse(r.self_service_hold_allowed)
        self.assertFalse(r.platform_checkout_allowed)
        self.assertEqual(r.blocked_code, "supplier_policy_incomplete")
