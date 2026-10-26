from frontend.labstock_ui.components.status_badge import sku_chip, status_badge
from frontend.labstock_ui.state.navigation import NavigationState
from frontend.labstock_ui.state.session import SessionState


def test_session_state_and_roles():
    session = SessionState()
    assert session.is_authenticated is False
    assert session.role == "viewer"
    assert session.is_admin is False
    assert session.is_manager is False

    # Simulate admin login
    notified = []
    session.add_listener(lambda: notified.append(True))
    session.login("dummy_token", {"id": 1, "email": "admin@labstock.edu", "role": "administrator"})

    assert session.is_authenticated is True
    assert session.is_admin is True
    assert session.is_manager is True
    assert len(notified) == 1

    # Simulate logout
    session.logout()
    assert session.is_authenticated is False
    assert session.current_user is None
    assert len(notified) == 2


def test_navigation_routing():
    nav = NavigationState()
    history = []
    nav.add_listener(lambda r, p: history.append((r, p)))

    nav.navigate("inventory")
    assert nav.current_route == "inventory"

    nav.navigate("item_details", {"item_id": 42})
    assert nav.current_route == "item_details"
    assert nav.route_params["item_id"] == 42
    assert len(history) == 2


def test_status_badge_and_sku_chip():
    badge_in = status_badge("IN_STOCK")
    assert badge_in.bgcolor == "#EBFBF5"

    badge_low = status_badge("LOW_STOCK")
    assert badge_low.bgcolor == "#FFFBEB"

    badge_out = status_badge("OUT_OF_STOCK")
    assert badge_out.bgcolor == "#FEF2F2"

    chip = sku_chip("EL-MTR-042")
    assert chip.content.value == "EL-MTR-042"
    assert chip.content.font_family == "monospace"


def test_metric_card_component():
    import flet as ft

    from frontend.labstock_ui.components.metric_card import metric_card

    card = metric_card(
        title="Active Catalog SKUs",
        value="48",
        subtitle="12 distinct categories",
        icon=ft.Icons.CATEGORY,
    )
    assert card is not None
    assert card.border_radius == 10


def test_empty_and_loading_states():
    import flet as ft

    from frontend.labstock_ui.components.empty_state import empty_state
    from frontend.labstock_ui.components.loading_state import loading_state

    loading = loading_state("Fetching live balances...")
    assert loading is not None

    empty = empty_state(
        title="No movements recorded",
        message="Stock movements will appear here once receipts or issues are logged.",
        icon=ft.Icons.INVENTORY_2_OUTLINED,
    )
    assert empty is not None
