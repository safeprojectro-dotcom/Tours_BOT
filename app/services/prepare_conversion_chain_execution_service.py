"""B16D2B: execute prepare-conversion-chain via existing bridge / catalog / execution-link services + guarded audit."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin_guarded_action import AdminGuardedActionAttempt, AdminGuardedActionStep
from app.models.enums import AdminGuardedActionAttemptStatus, AdminGuardedActionStepStatus
from app.schemas.admin_prepare_conversion_chain_plan import (
    AdminPrepareConversionChainExecutionResultRead,
    AdminPrepareConversionChainExecutionStepResultRead,
    AdminPrepareConversionChainPlanRead,
)
from app.services.admin_guarded_action_audit_service import (
    ACTION_PREPARE_CONVERSION_CHAIN,
    SOURCE_ENTITY_SUPPLIER_OFFER,
    AdminGuardedActionAuditService,
)
from app.repositories.supplier_offer_execution_link import SupplierOfferExecutionLinkRepository
from app.services.admin_prepare_conversion_chain_plan_service import AdminPrepareConversionChainPlanService
from app.services.admin_tour_write import (
    AdminTourCatalogActivationStateError,
    AdminTourCatalogActivationValidationError,
    AdminTourNotFoundError,
    AdminTourWriteService,
)
from app.services.supplier_offer_execution_link_service import (
    SupplierOfferExecutionLinkNotFoundError,
    SupplierOfferExecutionLinkService,
    SupplierOfferExecutionLinkValidationError,
)
from app.services.supplier_offer_tour_bridge_service import (
    SupplierOfferTourBridgeExistingTourError,
    SupplierOfferTourBridgeNotFoundError,
    SupplierOfferTourBridgeService,
    SupplierOfferTourBridgeStateError,
    SupplierOfferTourBridgeTourNotFoundError,
    SupplierOfferTourBridgeValidationError,
)

_STEP_ORDER = (
    "ensure_tour_bridge",
    "activate_tour_for_catalog",
    "ensure_active_execution_link",
)


class PrepareConversionChainExecutionService:
    def __init__(
        self,
        *,
        audit: AdminGuardedActionAuditService | None = None,
        plan: AdminPrepareConversionChainPlanService | None = None,
        bridge: SupplierOfferTourBridgeService | None = None,
        tour_write: AdminTourWriteService | None = None,
        execution_links: SupplierOfferExecutionLinkService | None = None,
        execution_link_repo: SupplierOfferExecutionLinkRepository | None = None,
    ) -> None:
        self._audit = audit or AdminGuardedActionAuditService()
        self._plan = plan or AdminPrepareConversionChainPlanService()
        self._bridge = bridge or SupplierOfferTourBridgeService()
        self._tour_write = tour_write or AdminTourWriteService()
        self._exec = execution_links or SupplierOfferExecutionLinkService()
        self._exec_link_repo = execution_link_repo or SupplierOfferExecutionLinkRepository()

    def execute(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        idempotency_key: str,
        confirm: bool,
        actor_surface: str = "service",
        requested_by: str | None = None,
        dry_run: bool = False,
    ) -> AdminPrepareConversionChainExecutionResultRead:
        key = self._audit.validate_idempotency_key(idempotency_key)
        now = datetime.now(UTC)

        if dry_run:
            plan = self._plan.read_plan(session, offer_id=supplier_offer_id)
            return self._dry_run_response(
                supplier_offer_id=supplier_offer_id,
                idempotency_key=key,
                confirm=confirm,
                actor_surface=actor_surface,
                requested_by=requested_by,
                plan=plan,
                generated_at=now,
            )

        if not confirm:
            raise ValueError("confirm must be True for non-dry prepare_conversion_chain execution")

        attempt, created = self._audit.get_or_create_attempt(
            session,
            action_code=ACTION_PREPARE_CONVERSION_CHAIN,
            source_entity_type=SOURCE_ENTITY_SUPPLIER_OFFER,
            source_entity_id=supplier_offer_id,
            idempotency_key=key,
            requested_by=requested_by,
            dry_run=False,
            extra={"actor_surface": actor_surface},
        )

        if not created:
            st = attempt.status
            if st == AdminGuardedActionAttemptStatus.RUNNING.value:
                raise ValueError(
                    f"idempotency_key {key!r} maps to an attempt still marked running; retry later or escalate",
                )
            if st in (
                AdminGuardedActionAttemptStatus.SUCCEEDED.value,
                AdminGuardedActionAttemptStatus.FAILED.value,
                AdminGuardedActionAttemptStatus.PARTIAL_SUCCESS.value,
            ):
                return self._replay_stored_attempt(
                    session,
                    attempt=attempt,
                    supplier_offer_id=supplier_offer_id,
                    idempotency_key=key,
                    confirm=confirm,
                    actor_surface=actor_surface,
                    requested_by=requested_by,
                    generated_at=now,
                )

        self._audit.set_attempt_status(session, attempt, status=AdminGuardedActionAttemptStatus.RUNNING)

        plan = self._plan.read_plan(session, offer_id=supplier_offer_id)
        allowed, blockers = self._execution_precheck(plan)

        if not allowed:
            self._audit.set_attempt_status(
                session,
                attempt,
                status=AdminGuardedActionAttemptStatus.FAILED,
                error_code="precheck_blocked",
                error_message="; ".join(blockers) if blockers else "not_executable",
            )
            session.refresh(attempt)
            return AdminPrepareConversionChainExecutionResultRead(
                supplier_offer_id=supplier_offer_id,
                dry_run=False,
                confirm=confirm,
                actor_surface=actor_surface,
                idempotency_key=key,
                requested_by=requested_by,
                attempt_id=attempt.id,
                attempt_status=attempt.status,
                overall_status="blocked",
                blockers=blockers,
                message="Prepare conversion chain precheck failed.",
                tour_id=None,
                execution_link_id=None,
                prepare_conversion_chain_plan_status=plan.prepare_conversion_chain_plan_status,
                steps=[],
                generated_at=now,
            )

        if plan.prepare_conversion_chain_plan_status == "already_prepared":
            return self._execute_all_satisfied(
                session,
                attempt=attempt,
                plan=plan,
                supplier_offer_id=supplier_offer_id,
                idempotency_key=key,
                confirm=confirm,
                actor_surface=actor_surface,
                requested_by=requested_by,
                generated_at=now,
            )

        return self._execute_partial_chain(
            session,
            attempt=attempt,
            supplier_offer_id=supplier_offer_id,
            idempotency_key=key,
            confirm=confirm,
            actor_surface=actor_surface,
            requested_by=requested_by,
            generated_at=now,
        )

    @staticmethod
    def _execution_precheck(plan: AdminPrepareConversionChainPlanRead) -> tuple[bool, list[str]]:
        if not plan.prepare_conversion_chain_eligible:
            return False, list(plan.eligibility_blockers)
        if plan.prepare_conversion_chain_plan_status == "ineligible":
            return False, list(plan.eligibility_blockers) or list(plan.plan_blockers) or ["ineligible"]
        if plan.prepare_conversion_chain_plan_status == "already_prepared":
            return True, []
        if any(s.would_execute for s in plan.steps):
            return True, []
        if all(s.already_satisfied for s in plan.steps):
            return True, []
        return False, list(plan.plan_blockers) or ["no_executable_prepare_steps"]

    def _dry_run_response(
        self,
        *,
        supplier_offer_id: int,
        idempotency_key: str,
        confirm: bool,
        actor_surface: str,
        requested_by: str | None,
        plan: AdminPrepareConversionChainPlanRead,
        generated_at: datetime,
    ) -> AdminPrepareConversionChainExecutionResultRead:
        allowed, blockers = self._execution_precheck(plan)
        steps_out: list[AdminPrepareConversionChainExecutionStepResultRead] = []
        for s in plan.steps:
            if s.already_satisfied:
                st: Any = "skipped"
                detail: dict[str, Any] | None = {"reason": "already_satisfied", "dry_run": True}
            elif s.would_execute:
                st = "skipped"
                detail = {"dry_run": True, "would_mutate": True}
            else:
                st = "skipped"
                detail = {"dry_run": True, "would_mutate": False, "plan_step_status": s.status}
            steps_out.append(
                AdminPrepareConversionChainExecutionStepResultRead(
                    step_code=s.code,
                    step_order=s.order_index,
                    status=st,
                    detail=detail,
                )
            )

        overall: Any = "dry_run_preview"
        message = "Dry run: no audit rows or business mutations."
        if not allowed:
            overall = "blocked"
            message = "Dry run: chain would be blocked by current readiness."

        return AdminPrepareConversionChainExecutionResultRead(
            supplier_offer_id=supplier_offer_id,
            dry_run=True,
            confirm=confirm,
            actor_surface=actor_surface,
            idempotency_key=idempotency_key,
            requested_by=requested_by,
            attempt_id=None,
            attempt_status=None,
            overall_status=overall,
            blockers=blockers,
            message=message,
            tour_id=None,
            execution_link_id=None,
            prepare_conversion_chain_plan_status=plan.prepare_conversion_chain_plan_status,
            steps=steps_out,
            generated_at=generated_at,
        )

    def _execute_all_satisfied(
        self,
        session: Session,
        *,
        attempt: AdminGuardedActionAttempt,
        plan: AdminPrepareConversionChainPlanRead,
        supplier_offer_id: int,
        idempotency_key: str,
        confirm: bool,
        actor_surface: str,
        requested_by: str | None,
        generated_at: datetime,
    ) -> AdminPrepareConversionChainExecutionResultRead:
        step_models: list[AdminPrepareConversionChainExecutionStepResultRead] = []
        for s in plan.steps:
            row = self._audit.create_step(
                session,
                attempt=attempt,
                step_code=s.code,
                step_order=s.order_index,
                detail={"reason": "already_prepared_plan"},
            )
            self._audit.complete_step(
                session,
                row,
                status=AdminGuardedActionStepStatus.SKIPPED,
                detail={"reason": "already_satisfied"},
            )
            step_models.append(self._step_to_result(row))

        tour_id, link_id = self._resolve_ids_from_session(session, supplier_offer_id=supplier_offer_id)
        merged = {**(attempt.extra or {}), "tour_id": tour_id, "execution_link_id": link_id}
        attempt.extra = merged
        session.add(attempt)
        session.flush()

        self._audit.set_attempt_status(session, attempt, status=AdminGuardedActionAttemptStatus.SUCCEEDED)
        session.refresh(attempt)

        return AdminPrepareConversionChainExecutionResultRead(
            supplier_offer_id=supplier_offer_id,
            dry_run=False,
            confirm=confirm,
            actor_surface=actor_surface,
            idempotency_key=idempotency_key,
            requested_by=requested_by,
            attempt_id=attempt.id,
            attempt_status=attempt.status,
            overall_status="succeeded",
            blockers=[],
            message="All preparation steps already satisfied; no business mutations performed.",
            tour_id=tour_id,
            execution_link_id=link_id,
            prepare_conversion_chain_plan_status=plan.prepare_conversion_chain_plan_status,
            steps=step_models,
            generated_at=generated_at,
        )

    def _execute_partial_chain(
        self,
        session: Session,
        *,
        attempt: AdminGuardedActionAttempt,
        supplier_offer_id: int,
        idempotency_key: str,
        confirm: bool,
        actor_surface: str,
        requested_by: str | None,
        generated_at: datetime,
    ) -> AdminPrepareConversionChainExecutionResultRead:
        created_by = requested_by or f"prepare_conversion_chain:{actor_surface}"
        tour_id_holder: dict[str, int | None] = {"tour_id": None}
        step_models: list[AdminPrepareConversionChainExecutionStepResultRead] = []
        any_mutating_success = False

        for order_idx, expected_code in enumerate(_STEP_ORDER, start=1):
            plan = self._plan.read_plan(session, offer_id=supplier_offer_id)
            step_plan = plan.steps[order_idx - 1]
            assert step_plan.code == expected_code

            row = self._audit.create_step(session, attempt=attempt, step_code=step_plan.code, step_order=order_idx)

            if step_plan.already_satisfied:
                self._pull_tour_id_after_skip(session, supplier_offer_id=supplier_offer_id, holder=tour_id_holder)
                self._audit.complete_step(
                    session,
                    row,
                    status=AdminGuardedActionStepStatus.SKIPPED,
                    detail={"reason": "already_satisfied"},
                )
                step_models.append(self._step_to_result(row))
                continue

            if step_plan.status == "not_applicable":
                self._audit.complete_step(
                    session,
                    row,
                    status=AdminGuardedActionStepStatus.SKIPPED,
                    detail={"reason": "not_applicable"},
                )
                step_models.append(self._step_to_result(row))
                continue

            if not step_plan.would_execute:
                msg = "; ".join(step_plan.blockers) if step_plan.blockers else "step_not_executable"
                self._audit.complete_step(
                    session,
                    row,
                    status=AdminGuardedActionStepStatus.FAILED,
                    error_code="plan_step_blocked",
                    error_message=msg,
                )
                step_models.append(self._step_to_result(row))
                step_models.extend(
                    self._audit_skipped_tail(
                        session,
                        attempt=attempt,
                        after_step_order=order_idx,
                        skip_reason="previous_step_blocked",
                    ),
                )
                att_st = (
                    AdminGuardedActionAttemptStatus.PARTIAL_SUCCESS
                    if any_mutating_success
                    else AdminGuardedActionAttemptStatus.FAILED
                )
                self._audit.set_attempt_status(
                    session,
                    attempt,
                    status=att_st,
                    error_code="plan_step_blocked",
                    error_message=msg,
                )
                session.refresh(attempt)
                tour_id, link_id = self._resolve_ids_from_session(session, supplier_offer_id=supplier_offer_id)
                return AdminPrepareConversionChainExecutionResultRead(
                    supplier_offer_id=supplier_offer_id,
                    dry_run=False,
                    confirm=confirm,
                    actor_surface=actor_surface,
                    idempotency_key=idempotency_key,
                    requested_by=requested_by,
                    attempt_id=attempt.id,
                    attempt_status=attempt.status,
                    overall_status="partial_success" if att_st == AdminGuardedActionAttemptStatus.PARTIAL_SUCCESS else "failed",
                    blockers=[msg],
                    message="Prepare conversion chain stopped on a blocked step.",
                    tour_id=tour_id,
                    execution_link_id=link_id,
                    prepare_conversion_chain_plan_status=plan.prepare_conversion_chain_plan_status,
                    steps=step_models,
                    generated_at=generated_at,
                )

            self._audit.set_step_running(session, row)
            try:
                detail = self._mutate_step(
                    session,
                    supplier_offer_id=supplier_offer_id,
                    step_code=step_plan.code,
                    created_by=created_by,
                    tour_id_holder=tour_id_holder,
                )
            except (
                SupplierOfferTourBridgeValidationError,
                SupplierOfferTourBridgeStateError,
                SupplierOfferTourBridgeExistingTourError,
                SupplierOfferTourBridgeTourNotFoundError,
                SupplierOfferTourBridgeNotFoundError,
                AdminTourCatalogActivationValidationError,
                AdminTourCatalogActivationStateError,
                AdminTourNotFoundError,
                SupplierOfferExecutionLinkValidationError,
                SupplierOfferExecutionLinkNotFoundError,
                RuntimeError,
            ) as exc:
                code, msg = self._map_exception(exc)
                self._audit.complete_step(
                    session,
                    row,
                    status=AdminGuardedActionStepStatus.FAILED,
                    error_code=code,
                    error_message=msg,
                )
                step_models.append(self._step_to_result(row))
                step_models.extend(
                    self._audit_skipped_tail(
                        session,
                        attempt=attempt,
                        after_step_order=order_idx,
                        skip_reason="previous_step_failed",
                    ),
                )
                att_st = (
                    AdminGuardedActionAttemptStatus.PARTIAL_SUCCESS
                    if any_mutating_success
                    else AdminGuardedActionAttemptStatus.FAILED
                )
                self._audit.set_attempt_status(
                    session,
                    attempt,
                    status=att_st,
                    error_code=code,
                    error_message=msg,
                )
                session.refresh(attempt)
                tour_id, link_id = self._resolve_ids_from_session(session, supplier_offer_id=supplier_offer_id)
                return AdminPrepareConversionChainExecutionResultRead(
                    supplier_offer_id=supplier_offer_id,
                    dry_run=False,
                    confirm=confirm,
                    actor_surface=actor_surface,
                    idempotency_key=idempotency_key,
                    requested_by=requested_by,
                    attempt_id=attempt.id,
                    attempt_status=attempt.status,
                    overall_status="partial_success" if att_st == AdminGuardedActionAttemptStatus.PARTIAL_SUCCESS else "failed",
                    blockers=[msg],
                    message="Prepare conversion chain stopped on a failed mutation step.",
                    tour_id=tour_id,
                    execution_link_id=link_id,
                    prepare_conversion_chain_plan_status=plan.prepare_conversion_chain_plan_status,
                    steps=step_models,
                    generated_at=generated_at,
                )

            self._audit.complete_step(
                session,
                row,
                status=AdminGuardedActionStepStatus.SUCCEEDED,
                detail=detail,
            )
            step_models.append(self._step_to_result(row))
            any_mutating_success = True

        tour_id, link_id = self._resolve_ids_from_session(session, supplier_offer_id=supplier_offer_id)
        attempt.extra = {**(attempt.extra or {}), "tour_id": tour_id, "execution_link_id": link_id}
        session.add(attempt)
        session.flush()
        self._audit.set_attempt_status(session, attempt, status=AdminGuardedActionAttemptStatus.SUCCEEDED)
        session.refresh(attempt)

        final_plan = self._plan.read_plan(session, offer_id=supplier_offer_id)
        return AdminPrepareConversionChainExecutionResultRead(
            supplier_offer_id=supplier_offer_id,
            dry_run=False,
            confirm=confirm,
            actor_surface=actor_surface,
            idempotency_key=idempotency_key,
            requested_by=requested_by,
            attempt_id=attempt.id,
            attempt_status=attempt.status,
            overall_status="succeeded",
            blockers=[],
            message=None,
            tour_id=tour_id,
            execution_link_id=link_id,
            prepare_conversion_chain_plan_status=final_plan.prepare_conversion_chain_plan_status,
            steps=step_models,
            generated_at=generated_at,
        )

    def _mutate_step(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        step_code: str,
        created_by: str,
        tour_id_holder: dict[str, int | None],
    ) -> dict[str, Any]:
        if step_code == "ensure_tour_bridge":
            res = self._bridge.create_or_replay_bridge(
                session,
                supplier_offer_id=supplier_offer_id,
                created_by=created_by,
                notes=None,
                existing_tour_id=None,
            )
            tour_id_holder["tour_id"] = res.tour_id
            return {"tour_id": res.tour_id, "bridge_id": res.id, "idempotent_replay": res.idempotent_replay}

        if step_code == "activate_tour_for_catalog":
            tid = tour_id_holder["tour_id"]
            if tid is None:
                br = self._bridge.get_active_bridge(session, supplier_offer_id=supplier_offer_id)
                if br is None:
                    raise RuntimeError("internal: missing active bridge before catalog activation")
                tid = br.tour_id
                tour_id_holder["tour_id"] = tid
            act = self._tour_write.activate_tour_for_catalog(
                session,
                tour_id=tid,
                activated_by=created_by,
                notes=None,
            )
            return {
                "tour_id": tid,
                "idempotent_replay": act.idempotent_replay,
                "tour_status": act.status.value,
            }

        if step_code == "ensure_active_execution_link":
            tid = tour_id_holder["tour_id"]
            if tid is None:
                br = self._bridge.get_active_bridge(session, supplier_offer_id=supplier_offer_id)
                if br is None:
                    raise RuntimeError("internal: missing active bridge before execution link")
                tid = br.tour_id
                tour_id_holder["tour_id"] = tid
            link = self._exec.link_offer_to_tour(session, offer_id=supplier_offer_id, tour_id=tid)
            return {"tour_id": tid, "execution_link_id": link.id}

        raise RuntimeError(f"unknown prepare_conversion_chain step {step_code!r}")

    @staticmethod
    def _map_exception(exc: Exception) -> tuple[str, str]:
        if isinstance(exc, SupplierOfferTourBridgeValidationError):
            return "tour_bridge_validation", ",".join(exc.missing_fields)
        if isinstance(exc, SupplierOfferTourBridgeStateError):
            return exc.code, exc.message
        if isinstance(exc, SupplierOfferTourBridgeExistingTourError):
            return "tour_bridge_existing_tour", exc.message
        if isinstance(exc, SupplierOfferTourBridgeTourNotFoundError):
            return "tour_bridge_tour_not_found", "Tour not found."
        if isinstance(exc, SupplierOfferTourBridgeNotFoundError):
            return "tour_bridge_not_found", "Offer not found."
        if isinstance(exc, AdminTourCatalogActivationValidationError):
            return "catalog_activation_validation", ",".join(exc.missing_fields)
        if isinstance(exc, AdminTourCatalogActivationStateError):
            return "catalog_activation_state", str(exc)
        if isinstance(exc, AdminTourNotFoundError):
            return "tour_not_found", "Tour not found."
        if isinstance(exc, SupplierOfferExecutionLinkValidationError):
            return "execution_link_validation", exc.message
        if isinstance(exc, SupplierOfferExecutionLinkNotFoundError):
            return "execution_link_not_found", "Offer not found."
        return type(exc).__name__, str(exc)

    @staticmethod
    def _step_to_result(row: AdminGuardedActionStep) -> AdminPrepareConversionChainExecutionStepResultRead:
        raw = row.status
        if raw == AdminGuardedActionStepStatus.SUCCEEDED.value:
            out: Any = "succeeded"
        elif raw == AdminGuardedActionStepStatus.FAILED.value:
            out = "failed"
        elif raw == AdminGuardedActionStepStatus.SKIPPED.value:
            out = "skipped"
        else:
            out = "failed"
        return AdminPrepareConversionChainExecutionStepResultRead(
            step_code=row.step_code,
            step_order=row.step_order,
            status=out,
            error_code=row.error_code,
            error_message=row.error_message,
            detail=row.detail,
        )

    def _audit_skipped_tail(
        self,
        session: Session,
        *,
        attempt: AdminGuardedActionAttempt,
        after_step_order: int,
        skip_reason: str,
    ) -> list[AdminPrepareConversionChainExecutionStepResultRead]:
        out: list[AdminPrepareConversionChainExecutionStepResultRead] = []
        for ord_ in range(after_step_order + 1, len(_STEP_ORDER) + 1):
            code = _STEP_ORDER[ord_ - 1]
            row = self._audit.create_step(session, attempt=attempt, step_code=code, step_order=ord_)
            self._audit.complete_step(
                session,
                row,
                status=AdminGuardedActionStepStatus.SKIPPED,
                detail={"reason": skip_reason},
            )
            out.append(self._step_to_result(row))
        return out

    def _pull_tour_id_after_skip(
        self,
        session: Session,
        *,
        supplier_offer_id: int,
        holder: dict[str, int | None],
    ) -> None:
        if holder["tour_id"] is not None:
            return
        br = self._bridge.get_active_bridge(session, supplier_offer_id=supplier_offer_id)
        if br is not None:
            holder["tour_id"] = br.tour_id

    def _resolve_ids_from_session(self, session: Session, *, supplier_offer_id: int) -> tuple[int | None, int | None]:
        br = self._bridge.get_active_bridge(session, supplier_offer_id=supplier_offer_id)
        tour_id = br.tour_id if br is not None else None
        link_id: int | None = None
        if tour_id is not None:
            active = self._exec_link_repo.get_active_for_offer(
                session,
                supplier_offer_id=supplier_offer_id,
                for_update=False,
            )
            if active is not None:
                link_id = active.id
        return tour_id, link_id

    def _replay_stored_attempt(
        self,
        session: Session,
        *,
        attempt: AdminGuardedActionAttempt,
        supplier_offer_id: int,
        idempotency_key: str,
        confirm: bool,
        actor_surface: str,
        requested_by: str | None,
        generated_at: datetime,
    ) -> AdminPrepareConversionChainExecutionResultRead:
        session.refresh(attempt)
        st = attempt.status
        if st == AdminGuardedActionAttemptStatus.SUCCEEDED.value:
            overall: Any = "succeeded"
            msg = "Idempotent replay of a succeeded prepare_conversion_chain attempt."
        elif st == AdminGuardedActionAttemptStatus.PARTIAL_SUCCESS.value:
            overall = "partial_success"
            msg = (
                "Idempotent replay of a partial_success prepare_conversion_chain attempt; "
                "use a new idempotency_key to retry."
            )
        elif st == AdminGuardedActionAttemptStatus.FAILED.value:
            overall = "failed"
            msg = (
                "Idempotent replay of a failed prepare_conversion_chain attempt; "
                "use a new idempotency_key to retry."
            )
        else:  # pragma: no cover
            raise ValueError(f"unexpected attempt status for replay: {st!r}")

        step_rows = list(
            session.scalars(
                select(AdminGuardedActionStep)
                .where(AdminGuardedActionStep.attempt_id == attempt.id)
                .order_by(AdminGuardedActionStep.step_order),
            ).all(),
        )
        step_models = [self._step_to_result(r) for r in step_rows]
        tour_id, link_id = self._resolve_ids_from_session(session, supplier_offer_id=supplier_offer_id)
        plan = self._plan.read_plan(session, offer_id=supplier_offer_id)
        blockers: list[str] = []
        if attempt.error_message:
            blockers = [attempt.error_message]

        return AdminPrepareConversionChainExecutionResultRead(
            supplier_offer_id=supplier_offer_id,
            dry_run=False,
            confirm=confirm,
            actor_surface=actor_surface,
            idempotency_key=idempotency_key,
            requested_by=requested_by,
            attempt_id=attempt.id,
            attempt_status=attempt.status,
            overall_status=overall,
            blockers=blockers,
            message=msg,
            tour_id=tour_id,
            execution_link_id=link_id,
            prepare_conversion_chain_plan_status=plan.prepare_conversion_chain_plan_status,
            steps=step_models,
            generated_at=generated_at,
        )


__all__ = ["PrepareConversionChainExecutionService"]
