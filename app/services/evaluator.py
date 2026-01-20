from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.schemas import (
    EvaluationRequest,
    EvaluationResponse,
    PolicyChoice,
    ResponseMetadata,
    ScenarioOutput,
    StakeholderImpact,
    StakeholderOutputs,
)


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _bonus_estimate(eps: float) -> float:
    return max(0.5, min(2.5, 0.6 + eps * 0.5))


def _prudence_score(gearing_percent: float) -> float:
    return max(1.0, min(10.0, 9.0 - (gearing_percent / 15.0)))


def _calculate_metrics(profit_after_tax: float, debt: float, equity: float, shares: float) -> dict:
    eps = _safe_divide(profit_after_tax, shares)
    gearing = _safe_divide(debt, equity) * 100.0 if equity > 0 else 0.0
    return {
        "eps": eps,
        "gearing": gearing,
        "bonus_estimate": _bonus_estimate(eps),
        "prudence_score": _prudence_score(gearing),
    }


def _format_delta(value: float, decimals: int = 2) -> str:
    return f"{abs(value):.{decimals}f}"


def _policy_labels(policy_choice: PolicyChoice) -> tuple[str, str]:
    if policy_choice == PolicyChoice.DEV_CAPITALISE_VS_EXPENSE:
        return "Capitalise", "Expense"
    return "Fair value", "Cost"


def _build_investor_impact(
    policy_choice: PolicyChoice, base_metrics: dict, option_a: dict, option_b: dict
) -> StakeholderImpact:
    label_a, label_b = _policy_labels(policy_choice)
    eps_base = base_metrics["eps"]
    eps_a = option_a["eps"]
    eps_b = option_b["eps"]
    delta_a = eps_a - eps_base
    delta_b = eps_b - eps_base

    bullets = [
        f"{label_a} moves EPS {('up' if delta_a > 0 else 'down' if delta_a < 0 else 'flat')} by "
        f"{_format_delta(delta_a, 2)} vs base.",
        f"{label_b} moves EPS {('up' if delta_b > 0 else 'down' if delta_b < 0 else 'flat')} by "
        f"{_format_delta(delta_b, 2)} vs base.",
    ]

    narrative = (
        f"EPS shifts from {eps_base:.2f} in the base case to {eps_a:.2f} under {label_a} "
        f"and {eps_b:.2f} under {label_b}. Investors weigh earnings uplift against the "
        "quality and sustainability of those earnings, favoring policies backed by durable cash flows."
    )

    return StakeholderImpact(title="Investors", bullet_impacts=bullets, narrative=narrative)


def _build_lender_impact(
    policy_choice: PolicyChoice,
    base_metrics: dict,
    option_a: dict,
    option_b: dict,
    covenant_max_gearing: float | None,
) -> StakeholderImpact:
    label_a, label_b = _policy_labels(policy_choice)
    base_gearing = base_metrics["gearing"]
    gearing_a = option_a["gearing"]
    gearing_b = option_b["gearing"]
    delta_a = gearing_a - base_gearing
    delta_b = gearing_b - base_gearing

    bullets = [
        f"{label_a} shifts gearing {('down' if delta_a < 0 else 'up' if delta_a > 0 else 'flat')} by "
        f"{_format_delta(delta_a, 1)}pp vs base.",
        f"{label_b} shifts gearing {('down' if delta_b < 0 else 'up' if delta_b > 0 else 'flat')} by "
        f"{_format_delta(delta_b, 1)}pp vs base.",
    ]

    covenant_note = ""
    if covenant_max_gearing is not None:
        worst_gearing = max(base_gearing, gearing_a, gearing_b)
        if worst_gearing > covenant_max_gearing:
            covenant_note = f"Covenant risk: gearing at {worst_gearing:.1f}% exceeds {covenant_max_gearing:.1f}%."
        else:
            covenant_note = (
                f"Covenant headroom remains with gearing at {worst_gearing:.1f}% "
                f"vs a {covenant_max_gearing:.1f}% limit."
            )
        bullets.append(covenant_note)

    narrative = (
        f"Balance sheet leverage moves from {base_gearing:.1f}% in the base case to {gearing_a:.1f}% "
        f"under {label_a} and {gearing_b:.1f}% under {label_b}. Lenders focus on balance sheet "
        "strength and the level of covenant headroom through the cycle."
    )
    if covenant_note:
        narrative = f"{narrative} {covenant_note}"

    return StakeholderImpact(title="Lenders", bullet_impacts=bullets, narrative=narrative)


def _stub_management_regulators(policy_choice: PolicyChoice) -> tuple[StakeholderImpact, StakeholderImpact]:
    if policy_choice == PolicyChoice.DEV_CAPITALISE_VS_EXPENSE:
        management = StakeholderImpact(
            title="Management",
            bullet_impacts=[
                "Bonus metrics improve with capitalisation.",
                "Delivery pressure increases to justify the asset.",
            ],
            narrative=(
                "Management benefits from a smoother earnings profile. "
                "Execution discipline becomes the key justification for the choice."
            ),
        )
        regulators = StakeholderImpact(
            title="Regulators",
            bullet_impacts=[
                "Expect tighter documentation on development criteria.",
                "Scrutiny on impairment testing cadence.",
            ],
            narrative=(
                "Regulators focus on evidence that capitalised projects meet recognition criteria. "
                "They signal that disclosure quality will drive acceptance."
            ),
        )
        return management, regulators

    management = StakeholderImpact(
        title="Management",
        bullet_impacts=[
            "Valuation teams gain prominence in reporting cycles.",
            "Narrative must explain revaluation drivers.",
        ],
        narrative=(
            "Management spends more time defending valuation inputs. "
            "A clear story on value drivers becomes central to stakeholder trust."
        ),
    )
    regulators = StakeholderImpact(
        title="Regulators",
        bullet_impacts=[
            "Expect robust valuation governance processes.",
            "Cost basis may reduce disclosure burden.",
        ],
        narrative=(
            "Regulators focus on valuation independence and model governance. "
            "They look for consistency in assumptions across reporting periods."
        ),
    )
    return management, regulators


def _build_scenarios(payload: EvaluationRequest) -> dict:
    base_metrics = _calculate_metrics(
        payload.profit_after_tax, payload.debt, payload.equity, payload.shares_outstanding
    )

    if payload.policy_choice == PolicyChoice.DEV_CAPITALISE_VS_EXPENSE:
        development_cost = max(0.0, payload.operating_profit * 0.2)
        net_cost = development_cost * (1 - payload.tax_rate)

        option_a_metrics = _calculate_metrics(
            payload.profit_after_tax + net_cost,
            payload.debt,
            payload.equity + development_cost,
            payload.shares_outstanding,
        )
        option_b_metrics = _calculate_metrics(
            payload.profit_after_tax - net_cost,
            payload.debt,
            payload.equity - net_cost,
            payload.shares_outstanding,
        )
        return {
            "base_case": base_metrics,
            "option_a": option_a_metrics,
            "option_b": option_b_metrics,
        }

    fair_value_uplift = max(0.0, payload.equity * 0.04)
    option_a_metrics = _calculate_metrics(
        payload.profit_after_tax + fair_value_uplift * (1 - payload.tax_rate) * 0.2,
        payload.debt,
        payload.equity + fair_value_uplift * 0.5,
        payload.shares_outstanding,
    )
    option_b_metrics = _calculate_metrics(
        payload.profit_after_tax - fair_value_uplift * (1 - payload.tax_rate) * 0.1,
        payload.debt,
        payload.equity - fair_value_uplift * 0.2,
        payload.shares_outstanding,
    )
    return {
        "base_case": base_metrics,
        "option_a": option_a_metrics,
        "option_b": option_b_metrics,
    }


def evaluate(payload: EvaluationRequest) -> EvaluationResponse:
    scenarios = _build_scenarios(payload)
    base_metrics = scenarios["base_case"]
    option_a_metrics = scenarios["option_a"]
    option_b_metrics = scenarios["option_b"]

    investors = _build_investor_impact(payload.policy_choice, base_metrics, option_a_metrics, option_b_metrics)
    lenders = _build_lender_impact(
        payload.policy_choice, base_metrics, option_a_metrics, option_b_metrics, payload.covenant_max_gearing
    )
    management, regulators = _stub_management_regulators(payload.policy_choice)

    timestamp = datetime.now(timezone.utc).isoformat()

    return EvaluationResponse(
        metadata=ResponseMetadata(
            request_id=str(uuid4()),
            timestamp_utc=timestamp,
            company_name=payload.company_name,
            policy_choice=payload.policy_choice,
            currency=payload.currency,
        ),
        base_case=ScenarioOutput(label="Base case", headline_metrics=scenarios["base_case"]),
        option_a=ScenarioOutput(label="Option A", headline_metrics=scenarios["option_a"]),
        option_b=ScenarioOutput(label="Option B", headline_metrics=scenarios["option_b"]),
        stakeholders=StakeholderOutputs(
            investors=investors, lenders=lenders, management=management, regulators=regulators
        ),
    )
