from decimal import Decimal

import pytest

from backend.domain.money import lamports_to_sol, sol_to_lamports


def test_sol_lamport_round_trip():
    assert sol_to_lamports(Decimal("1.000000001")) == 1_000_000_001
    assert lamports_to_sol(1_000_000_001) == 1.000000001


def test_sub_lamport_precision_is_rejected():
    with pytest.raises(ValueError, match="sub_lamport"):
        sol_to_lamports(Decimal("0.0000000001"))
