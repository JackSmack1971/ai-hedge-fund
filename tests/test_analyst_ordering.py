"""Regression tests for analyst ordering — fixes #154 (duplicate order=6)."""

from src.utils.analysts import ANALYST_CONFIG, ANALYST_ORDER, get_agents_list


def test_analyst_orders_are_unique():
    orders = [v["order"] for v in ANALYST_CONFIG.values()]
    assert len(orders) == len(
        set(orders)
    ), f"Duplicate order values found: {[o for o in orders if orders.count(o) > 1]}"


def test_analyst_orders_are_contiguous_from_zero():
    orders = sorted(v["order"] for v in ANALYST_CONFIG.values())
    expected = list(range(len(orders)))
    assert orders == expected, f"Orders are not contiguous 0..{len(orders)-1}: {orders}"


def test_analyst_order_list_length_matches_config():
    assert len(ANALYST_ORDER) == len(ANALYST_CONFIG)


def test_get_agents_list_order_is_monotonically_increasing():
    agents = get_agents_list()
    orders = [a["order"] for a in agents]
    assert orders == sorted(orders), "get_agents_list() must return agents in ascending order"


def test_mohnish_pabrai_before_peter_lynch():
    """Mohnish Pabrai (6) must appear before Peter Lynch (7) in the sorted output."""
    agents = get_agents_list()
    keys = [a["key"] for a in agents]
    assert keys.index("mohnish_pabrai") < keys.index("peter_lynch")
