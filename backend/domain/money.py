from __future__ import annotations

from decimal import Decimal, InvalidOperation

LAMPORTS_PER_SOL = 1_000_000_000
_LAMPORTS_PER_SOL_DECIMAL = Decimal(LAMPORTS_PER_SOL)


def sol_to_lamports(value: Decimal | str | int | float) -> int:
    """Convert SOL to lamports without accepting sub-lamport precision."""
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid_sol_amount") from exc

    if not amount.is_finite() or amount <= 0:
        raise ValueError("invalid_sol_amount")

    lamports = amount * _LAMPORTS_PER_SOL_DECIMAL
    if lamports != lamports.to_integral_value():
        raise ValueError("amount_has_sub_lamport_precision")

    return int(lamports)


def lamports_to_sol(lamports: int) -> float:
    if lamports < 0:
        raise ValueError("lamports_must_be_non_negative")
    return float(Decimal(lamports) / _LAMPORTS_PER_SOL_DECIMAL)
