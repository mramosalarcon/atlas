"""System evaluation over historical draws."""

from __future__ import annotations

from typing import Sequence

from atlas.config.settings import PrizeSettings
from atlas.domain.draw import Draw
from atlas.domain.evaluation_result import SystemEvaluationResult
from atlas.domain.exceptions import InvalidSystemError
from atlas.domain.lottery_rules import LotteryRules
from atlas.domain.ticket_system import TicketSystem


def evaluate_system(
    system: TicketSystem,
    draws: Sequence[Draw],
    rules: LotteryRules,
    prizes: PrizeSettings,
) -> SystemEvaluationResult:
    if len(system.tickets) != rules.system_size:
        raise InvalidSystemError(
            f"System must contain {rules.system_size} tickets, got {len(system.tickets)}"
        )

    ge3 = ge4 = ge5 = ge6 = 0
    total_prizes = 0.0
    for draw in draws:
        best_hits = 0
        best_additional = False
        for ticket in system.tickets:
            hit = ticket.hits_against(draw)
            if hit.hits > best_hits or (
                hit.hits == best_hits and hit.additional_match and not best_additional
            ):
                best_hits = hit.hits
                best_additional = hit.additional_match

        if best_hits >= 3:
            ge3 += 1
        if best_hits >= 4:
            ge4 += 1
        if best_hits >= 5:
            ge5 += 1
        if best_hits >= 6:
            ge6 += 1
        total_prizes += prizes.amount_for(best_hits, best_additional)

    draw_count = len(draws)
    total_cost = prizes.ticket_cost * rules.system_size * draw_count
    roi = ((total_prizes - total_cost) / total_cost) if total_cost else 0.0
    coverage = (ge3 / draw_count) if draw_count else 0.0

    return SystemEvaluationResult(
        draws_evaluated=draw_count,
        hits_at_least_3=ge3,
        hits_at_least_4=ge4,
        hits_at_least_5=ge5,
        hits_at_least_6=ge6,
        coverage_ratio_ge3=coverage,
        total_cost=total_cost,
        total_prizes=total_prizes,
        roi=roi,
        prizes_provisional=prizes.provisional,
    )


def format_evaluation_report(result: SystemEvaluationResult, system_name: str) -> str:
    provisional = " (provisional prize table)" if result.prizes_provisional else ""
    return (
        "ATLAS historical evaluation — compares strategy coverage under game rules; "
        "does not predict future draws.\n"
        f"System: {system_name}\n"
        f"Draws evaluated: {result.draws_evaluated}\n"
        f"Draws with >=3 hits: {result.hits_at_least_3}\n"
        f"Draws with >=4 hits: {result.hits_at_least_4}\n"
        f"Draws with >=5 hits: {result.hits_at_least_5}\n"
        f"Draws with >=6 hits: {result.hits_at_least_6}\n"
        f"Coverage (>=3): {result.coverage_ratio_ge3:.4f}\n"
        f"Total cost: {result.total_cost:.2f}\n"
        f"Total prizes{provisional}: {result.total_prizes:.2f}\n"
        f"Historical ROI{provisional}: {result.roi:.4f}\n"
    )
