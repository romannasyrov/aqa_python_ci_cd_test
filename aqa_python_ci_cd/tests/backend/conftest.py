import allure
import pytest
from faker import Faker

from config import TestConfig
from src.backend.clients.http_client.client import HTTPClient
from src.backend.services.auth.adapter import AuthAdapter
from src.backend.services.auth.service import AuthService
from src.backend.services.cart.adapter import CartAdapter
from src.backend.services.cart.service import CartService
from src.backend.services.catalog.adapter import CatalogAdapter
from src.backend.services.catalog.service import CatalogService

fake = Faker()


class User:
    def __init__(self, username, token):
        self.username = username
        self.token = token


@pytest.fixture(scope="function")
def unique_username() -> str:
    return fake.user_name()


@pytest.fixture(scope="function")
def valid_password() -> str:
    return TestConfig.VALID_PASSWORD


@pytest.fixture(scope="session")
def http_client() -> HTTPClient:
    return HTTPClient(host=TestConfig.SHOP_BASE_URL)


@pytest.fixture(scope="function")
def registered_user(auth_service, unique_username, valid_password):
    auth_service.register(
        username=unique_username,
        password=valid_password
    )

    return {
        "username": unique_username,
        "password": valid_password
    }


@pytest.fixture(scope="function")
def logged_user(auth_service, registered_user):
    username = registered_user["username"]
    password = registered_user["password"]

    with allure.step(f"Логин пользователя: {username}"):
        response = auth_service.login(
            username=username,
            password=password
        )

        return User(
            username=username,
            token=response.token
        )


@pytest.fixture(scope="function")
def authorized_api_client(logged_user):
    return HTTPClient(
        host=TestConfig.SHOP_BASE_URL,
        default_headers={
            "Authorization": f"Bearer {logged_user.token}",
            "Content-Type": "application/json"
        }
    )


# PUBLIC fixtures

@pytest.fixture(scope="session")
def cart_adapter_unauthorized(http_client):
    return CartAdapter(api_client=http_client)


@pytest.fixture(scope="session")
def cart_service_unauthorized(cart_adapter_unauthorized):
    return CartService(adapter=cart_adapter_unauthorized)


@pytest.fixture(scope="session")
def catalog_adapter_unauthorized(http_client):
    return CatalogAdapter(api_client=http_client)


# AUTH fixtures

@pytest.fixture(scope="function")
def cart_adapter(authorized_api_client):
    return CartAdapter(api_client=authorized_api_client)


@pytest.fixture(scope="function")
def cart_service(cart_adapter):
    return CartService(adapter=cart_adapter)


@pytest.fixture(scope="function")
def catalog_adapter(authorized_api_client):
    return CatalogAdapter(api_client=authorized_api_client)


@pytest.fixture(scope="function")
def catalog_service(catalog_adapter) -> CatalogService:
    return CatalogService(adapter=catalog_adapter)


@pytest.fixture(scope="session")
def auth_adapter(http_client):
    return AuthAdapter(api_client=http_client)


@pytest.fixture(scope="session")
def auth_service(auth_adapter) -> AuthService:
    return AuthService(adapter=auth_adapter)
