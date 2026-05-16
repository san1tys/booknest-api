import pytest


ENDPOINT_NAMES = [
    "users_me",
    "users_register",
    "users_verify_email",
    "users_resend_verification",
    "users_login",
    "users_logout",
    "users_language",
    "hotels_create",
    "hotels_update",
    "hotels_detail",
    "hotels_list",
    "hotels_delete",
    "rooms_create",
    "rooms_update",
    "rooms_detail",
    "rooms_list",
    "rooms_delete",
    "reviews_list",
    "reviews_create",
    "bookings_create",
    "bookings_list",
    "bookings_availability",
    "bookings_cancel",
]

CASE_MATRIX = [
    (endpoint_name, variant)
    for endpoint_name in ENDPOINT_NAMES
    for variant in ("good", "bad_1", "bad_2")
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("endpoint_name", "variant"),
    CASE_MATRIX,
    ids=[f"{endpoint}:{variant}" for endpoint, variant in CASE_MATRIX],
)
def test_endpoint_response_matrix(
    api_state: dict,
    endpoint_case_map: dict,
    endpoint_name: str,
    variant: str,
) -> None:
    """Exercise one success case and two failure cases for each API endpoint."""
    case = endpoint_case_map[endpoint_name][variant]

    if case.setup is not None:
        case.setup()

    request_data = case.data
    if "data_key" in case.extra:
        request_data = {"refresh": api_state[case.extra["data_key"]]}

    request_kwargs = {}
    if request_data is not None:
        request_kwargs["data"] = request_data
    if case.format is not None:
        request_kwargs["format"] = case.format

    client = api_state["clients"][case.client_name]
    response = getattr(client, case.method.lower())(case.url, **request_kwargs)

    assert response.status_code == case.expected_status
    for key in case.expected_keys:
        assert key in response.data
    for key in case.absent_keys:
        assert key not in response.data
    if case.post_assert is not None:
        case.post_assert(response)
