"""Recovery proof for the mission-assurance split-brain execution bridge."""

from __future__ import annotations

from dataclasses import replace

from omega.split_brain_actuation import MissionAssuranceSplitBrain


class Clock:
    def __init__(self, now: float = 2_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def split_brain(clock: Clock) -> MissionAssuranceSplitBrain:
    return MissionAssuranceSplitBrain(
        b"d" * 32,
        b"a" * 32,
        clock=clock,
        max_ttl_seconds=60,
    )


def test_neither_decider_nor_actuator_can_execute_alone() -> None:
    clock = Clock()
    bridge = split_brain(clock)
    intent = bridge.create_intent(action="route", resource="demo-stream", ttl_seconds=10)
    decision = bridge.decider_approve(intent)
    actuator = bridge.actuator_approve(intent)
    calls: list[str] = []

    only_decider = bridge.execute(
        intent,
        decision=decision,
        actuator_approval=None,
        precondition_check=lambda _: True,
        execute=lambda _: calls.append("ran"),
    )
    only_actuator = bridge.execute(
        intent,
        decision=None,
        actuator_approval=actuator,
        precondition_check=lambda _: True,
        execute=lambda _: calls.append("ran"),
    )

    assert only_decider.executed is False
    assert only_decider.reason == "actuator_approval_invalid"
    assert only_actuator.executed is False
    assert only_actuator.reason == "decider_approval_invalid"
    assert calls == []


def test_matching_dual_key_receipts_execute_exact_intent() -> None:
    clock = Clock()
    bridge = split_brain(clock)
    intent = bridge.create_intent(
        action="route",
        resource="demo-stream",
        parameters={"destination": "local-buffer"},
        preconditions={"health": "green"},
        ttl_seconds=10,
    )
    decision = bridge.decider_approve(intent)
    actuator = bridge.actuator_approve(intent)
    calls: list[str] = []

    receipt = bridge.execute(
        intent,
        decision=decision,
        actuator_approval=actuator,
        precondition_check=lambda item: item.preconditions["health"] == "green",
        execute=lambda item: calls.append(item.resource) or {"accepted": True},
        postcondition_check=lambda _item, result: result["accepted"],
    )

    assert receipt.executed is True
    assert receipt.reason == "executed"
    assert receipt.decision_valid is True
    assert receipt.actuator_valid is True
    assert receipt.preconditions_valid is True
    assert receipt.postcondition is True
    assert calls == ["demo-stream"]
    assert bridge.executed_count == 1


def test_receipts_for_different_intent_digest_are_rejected() -> None:
    clock = Clock()
    bridge = split_brain(clock)
    intent = bridge.create_intent(action="route", resource="stream-a", ttl_seconds=10)
    other = replace(intent, resource="stream-b")
    decision = bridge.decider_approve(intent)
    actuator = bridge.actuator_approve(intent)

    receipt = bridge.execute(
        other,
        decision=decision,
        actuator_approval=actuator,
        precondition_check=lambda _: True,
        execute=lambda _: True,
    )

    assert receipt.executed is False
    assert receipt.decision_valid is False
    assert receipt.actuator_valid is False


def test_expired_intent_never_reaches_precondition_or_execute_callbacks() -> None:
    clock = Clock()
    bridge = split_brain(clock)
    intent = bridge.create_intent(action="route", resource="demo-stream", ttl_seconds=5)
    decision = bridge.decider_approve(intent)
    actuator = bridge.actuator_approve(intent)
    callbacks: list[str] = []
    clock.now += 6

    receipt = bridge.execute(
        intent,
        decision=decision,
        actuator_approval=actuator,
        precondition_check=lambda _: callbacks.append("precondition") or True,
        execute=lambda _: callbacks.append("execute"),
    )

    assert receipt.executed is False
    assert receipt.reason == "intent_expired"
    assert callbacks == []


def test_precondition_failure_blocks_execution_after_both_signatures_validate() -> None:
    clock = Clock()
    bridge = split_brain(clock)
    intent = bridge.create_intent(action="route", resource="demo-stream", ttl_seconds=10)
    decision = bridge.decider_approve(intent)
    actuator = bridge.actuator_approve(intent)
    calls: list[str] = []

    receipt = bridge.execute(
        intent,
        decision=decision,
        actuator_approval=actuator,
        precondition_check=lambda _: False,
        execute=lambda _: calls.append("ran"),
    )

    assert receipt.executed is False
    assert receipt.reason == "preconditions_failed"
    assert receipt.decision_valid is True
    assert receipt.actuator_valid is True
    assert calls == []


def test_executed_intent_cannot_be_replayed() -> None:
    clock = Clock()
    bridge = split_brain(clock)
    intent = bridge.create_intent(action="route", resource="demo-stream", ttl_seconds=10)
    decision = bridge.decider_approve(intent)
    actuator = bridge.actuator_approve(intent)
    calls: list[str] = []

    first = bridge.execute(
        intent,
        decision=decision,
        actuator_approval=actuator,
        precondition_check=lambda _: True,
        execute=lambda _: calls.append("ran"),
    )
    second = bridge.execute(
        intent,
        decision=decision,
        actuator_approval=actuator,
        precondition_check=lambda _: True,
        execute=lambda _: calls.append("ran-again"),
    )

    assert first.executed is True
    assert second.executed is False
    assert second.reason == "replay_rejected"
    assert calls == ["ran"]


def test_identical_decider_and_actuator_keys_are_rejected() -> None:
    clock = Clock()
    try:
        MissionAssuranceSplitBrain(b"x" * 32, b"x" * 32, clock=clock)
    except ValueError as error:
        assert "independent" in str(error)
    else:
        raise AssertionError("identical role keys must fail closed")
