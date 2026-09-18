import pytest

from src.backend.services.catalog.models.response_models import Product
from src.backend.services.catalog.service import CatalogService


@pytest.fixture
def available_products(catalog_service: CatalogService) -> list[Product]:
    catalog = catalog_service.get_catalog()

    if not catalog:
        pytest.skip("Каталог пустой, тест пропущен")

    return catalog
