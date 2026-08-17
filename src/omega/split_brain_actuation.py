"""Dual-key local actuation bridge for the synthetic telemetry laboratory.

A policy decider may authorize an intent, but cannot execute it. An independent
actuator must approve the exact same intent digest and only then may a caller-
provided local callback run. This module has no hardware, network, or flight
command transport.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Callable, Mapping

EVIDENCE_STATE = "LOCAL_DUAL_KEY_ACTUATION_SIMULATION_NOT_FLIGHT_AUTHORITY"
DEFAULT_MAX_TTL_SECONDS = 300.0


def _canonical_json(value: Mapping[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _sign(key: bytes, digest: str, role: str) -> str:
    return hmac.new(key, f"{role}:{digest}".encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class ActuationIntent:
    intent_id: str
    action: str
    resource: str
    parameters: dict[str, object]
    preconditions: dict[str, object]
    issued_at: float
    expires_at: float
    nonce: str
    evidence_state: str = EVIDENCE_STATE

    def payload(self) -> dict[str, object]:
        return {
            "intent_id": self.intent_id,
            "action": self.action,
            "resource": self.resource,
            "parameters": self.parameters,
            "preconditions": self.preconditions,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "nonce": self.nonce,
            "evidence_state": self.evidence_state,
        }

    @property
    def digest(self) -> str:
        return _digest(self.payload())


@dataclass(frozen=True)
class DecisionReceipt:
    role: str
    intent_id: str
    intent_digest: str
    signature: str
    signed_at: float
    evidence_state: str = EVIDENCE_STATE


@dataclass(frozen=True)
class ExecutionReceipt:
    executed: bool
    reason: str
    intent_id: str
    intent_digest: str
    checked_at: float
    decision_valid: bool
    actuator_valid: bool
    preconditions_valid: bool
    result: object | None = None
    postcondition: object | None = None
    evidence_state: str = EVIDENCE_STATE

    def as_dict(self) -> dict[str, object]:
        return {
            "executed": self.executed,
            "reason": self.reason,
            "intent_id": self.intent_id,
            "intent_digest": self.intent_digest,
            "checked_at": self.checked_at,
            "decision_valid": self.decision_valid,
            "actuator_valid": self.actuator_valid,
            "preconditions_valid": self.preconditions_valid,
            "result": self.result,
            "postcondition": self.postcondition,
            "evidence_state": self.evidence_state,
        }


class MissionAssuranceSplitBrain:
    """Require independent decider and actuator signatures before local execution."""

    def __init__(
        self,
        decider_key: bytes,
        actuator_key: bytes,
        *,
        clock: Callable[[], float] = time.time,
        max_ttl_seconds: float = DEFAULT_MAX_TTL_SECONDS,
    ) -> None:
        if not isinstance(decider_key, bytes) or len(decider_key) < 32:
            raise ValueError("decider_key must contain at least 32 bytes")
        if not isinstance(actuator_key, bytes) or len(actuator_key) < 32:
            raise ValueError("actuator_key must contain at least 32 bytes")
        if hmac.compare_digest(decider_key, actuator_key):
            raise ValueError("decider and actuator keys must be independent")
        if max_ttl_seconds <= 0:
            raise ValueError("max_ttl_seconds must be positive")
        self._decider_key = decider_key
        self._actuator_key = actuator_key
        self._clock = clock
        self._max_ttl_seconds = float(max_ttl_seconds)
        self._executed_intents: set[str] = set()

    @classmethod
    def ephemeral(
        cls,
        *,
        clock: Callable[[], float] = time.time,
        max_ttl_seconds: float = DEFAULT_MAX_TTL_SECONDS,
    ) -> "MissionAssuranceSplitBrain":
        return cls(
            secrets.token_bytes(32),
            secrets.token_bytes(32),
            clock=clock,
            max_ttl_seconds=max_ttl_seconds,
        )

    def create_intent(
        self,
        *,
        action: str,
        resource: str,
        parameters: Mapping[str, object] | None = None,
        preconditions: Mapping[str, object] | None = None,
        ttl_seconds: float = 30.0,
    ) -> ActuationIntent:
        action = str(action).strip()
        resource = str(resource).strip()
        ttl = float(ttl_seconds)
        if not action or not resource:
            raise ValueError("action and resource are required")
        if ttl <= 0 or ttl > self._max_ttl_seconds:
            raise ValueError("ttl_seconds exceeds configured split-brain horizon")
        now = float(self._clock())
        return ActuationIntent(
            intent_id=secrets.token_hex(16),
            action=action,
            resource=resource,
            parameters=dict(parameters or {}),
            preconditions=dict(preconditions or {}),
            issued_at=now,
            expires_at=now + ttl,
            nonce=secrets.token_hex(12),
        )

    def decider_approve(self, intent: ActuationIntent) -> DecisionReceipt:
        now = float(self._clock())
        return DecisionReceipt(
            role="decider",
            intent_id=intent.intent_id,
            intent_digest=intent.digest,
            signature=_sign(self._decider_key, intent.digest, "decider"),
            signed_at=now,
        )

    def actuator_approve(self, intent: ActuationIntent) -> DecisionReceipt:
        now = float(self._clock())
        return DecisionReceipt(
            role="actuator",
            intent_id=intent.intent_id,
            intent_digest=intent.digest,
            signature=_sign(self._actuator_key, intent.digest, "actuator"),
            signed_at=now,
        )

    def _valid_receipt(
        self,
        intent: ActuationIntent,
        receipt: DecisionReceipt | None,
        *,
        role: str,
    ) -> bool:
        if receipt is None or receipt.role != role:
            return False
        if receipt.intent_id != intent.intent_id or receipt.intent_digest != intent.digest:
            return False
        key = self._decider_key if role == "decider" else self._actuator_key
        expected = _sign(key, intent.digest, role)
        return hmac.compare_digest(receipt.signature, expected)

    def execute(
        self,
        intent: ActuationIntent,
        *,
        decision: DecisionReceipt | None,
        actuator_approval: DecisionReceipt | None,
        precondition_check: Callable[[ActuationIntent], bool],
        execute: Callable[[ActuationIntent], object],
        postcondition_check: Callable[[ActuationIntent, object], object] | None = None,
    ) -> ExecutionReceipt:
        checked_at = float(self._clock())
        decision_valid = self._valid_receipt(intent, decision, role="decider")
        actuator_valid = self._valid_receipt(intent, actuator_approval, role="actuator")
        preconditions_valid = False

        reason = "authorized"
        if intent.intent_id in self._executed_intents:
            reason = "replay_rejected"
        elif checked_at >= intent.expires_at:
            reason = "intent_expired"
        elif not decision_valid:
            reason = "decider_approval_invalid"
        elif not actuator_valid:
            reason = "actuator_approval_invalid"
        else:
            try:
                preconditions_valid = bool(precondition_check(intent))
            except Exception:
                preconditions_valid = False
            if not preconditions_valid:
                reason = "preconditions_failed"

        if reason != "authorized":
            return ExecutionReceipt(
                False,
                reason,
                intent.intent_id,
                intent.digest,
                checked_at,
                decision_valid,
                actuator_valid,
                preconditions_valid,
            )

        result = execute(intent)
        self._executed_intents.add(intent.intent_id)
        postcondition = (
            postcondition_check(intent, result) if postcondition_check is not None else None
        )
        return ExecutionReceipt(
            True,
            "executed",
            intent.intent_id,
            intent.digest,
            checked_at,
            True,
            True,
            True,
            result=result,
            postcondition=postcondition,
        )

    @property
    def executed_count(self) -> int:
        return len(self._executed_intents)
