import pytest

# Fixed user IDs, so a cart left behind by an interrupted run can be emptied by
# DELETE /api/cart with the same ID; each test empties its cart before and after.
UNCHANGED_USER = "cart-method-not-allowed-unchanged"
EMPTY_USER = "cart-method-not-allowed-empty"


def add_item_body(user, product_id, quantity):
    return {"userId": user, "item": {"productId": product_id, "quantity": quantity}}


def cart_items(api, user):
    resp = api.get("/api/cart", params={"sessionId": user})
    assert resp.status_code == 200
    return [(item["productId"], item["quantity"]) for item in resp.json()["items"]]


@pytest.fixture
def empty_cart(api):
    def empty(user):
        assert api.delete("/api/cart", json={"userId": user}).status_code == 204

    users = []

    def make(user):
        users.append(user)
        empty(user)
        return user

    yield make
    for user in users:
        empty(user)


def test_put_cart_answers_405_with_allow_and_empty_body(api, user_id):
    resp = api.request("PUT", "/api/cart", json=add_item_body(user_id, "OLJCESPC7Z", 1), timeout=5)
    assert resp.status_code == 405
    assert resp.headers["Allow"] == "GET, POST, DELETE"
    assert resp.content == b""
    assert resp.elapsed.total_seconds() < 5


def test_patch_cart_answers_like_put(api, user_id):
    put = api.request("PUT", "/api/cart", json=add_item_body(user_id, "OLJCESPC7Z", 1), timeout=5)
    resp = api.request("PATCH", "/api/cart", json=add_item_body(user_id, "OLJCESPC7Z", 1), timeout=5)
    assert resp.status_code == 405
    assert resp.headers["Allow"] == "GET, POST, DELETE"
    assert resp.content == b""
    assert resp.elapsed.total_seconds() < 5
    assert (resp.status_code, resp.headers.get("Allow")) == (put.status_code, put.headers.get("Allow"))


def test_refused_put_and_patch_leave_the_cart_unchanged(api, empty_cart):
    user = empty_cart(UNCHANGED_USER)
    resp = api.post("/api/cart", json=add_item_body(user, "OLJCESPC7Z", 1))
    assert resp.status_code == 200
    for method in ("PUT", "PATCH"):
        resp = api.request(method, "/api/cart", json=add_item_body(user, "66VCHSJNUP", 3), timeout=5)
        assert resp.status_code == 405
    assert cart_items(api, user) == [("OLJCESPC7Z", 1)]


def test_refused_put_adds_nothing_to_an_empty_cart(api, empty_cart):
    user = empty_cart(EMPTY_USER)
    resp = api.request("PUT", "/api/cart", json=add_item_body(user, "OLJCESPC7Z", 1), timeout=5)
    assert resp.status_code == 405
    assert cart_items(api, user) == []
