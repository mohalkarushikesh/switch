"""Indian digit grouping for rupee display."""

from taxpilot.money import group_inr, rupees


def test_indian_grouping():
    assert group_inr(500) == "500"
    assert group_inr(1_000) == "1,000"
    assert group_inr(1_00_000) == "1,00,000"
    assert group_inr(13_55_000) == "13,55,000"
    assert group_inr(1_23_45_678) == "1,23,45,678"


def test_rupees_prefix_and_sign():
    assert rupees(1_15_440) == "₹1,15,440"
    assert group_inr(-4_560) == "-4,560"
