from http import HTTPStatus

import allure
import pytest

from src.backend.services.catalog.constants.sort import SortOption
from src.backend.services.catalog.models.request_models import CatalogRequestModel
from src.utils.constants.response_messages import CommonResponseMessages
from src.utils.validators.assert_wrappers import assert_equal
from src.utils.validators.rest_api import validate_catalog_response, validate_response

pytestmark = [
    allure.feature("Тесты на каталог"),
    pytest.mark.catalog,
]


class TestCatalog:

    @allure.title("Фильтр: Получение каталога товаров")
    @pytest.mark.smoke
    def test_get_full_catalog(self, catalog_service):
        with allure.step("Отправка запроса на получение каталога товаров"):
            response = catalog_service.get_catalog()
        with allure.step("Валидация ответа каталога товаров"):
            assert_equal(
                actual_value=len(response) > 0,
                expected_value=True,
                allure_title="Каталог не пустой",
            )

    @allure.title("Фильтр по диапазону цен: минимальная - максимальная цена")
    @pytest.mark.smoke
    @pytest.mark.parametrize("min_price, max_price", [
        (None, 80000),
        (150000, None),
        (80000, 150000),
        (150000, 180000),
        pytest.param(
            100000, 70000,
            marks=pytest.mark.negative,
        ),
        (0, 0),
    ]
                             )
    def test_price_range_filter(self, catalog_service, min_price, max_price):
        with allure.step("Отправка запроса на получение каталога товаров с фильтрацией"):
            params = CatalogRequestModel(
                min_price=min_price,
                max_price=max_price
            )
            response = catalog_service.get_catalog(params=params)
        with allure.step("Валидация ответа каталога товаров"):
            is_invalid_range = (
                    min_price is not None and
                    max_price is not None and
                    min_price > max_price
            )
            is_zero_range = (
                    min_price == 0 and
                    max_price == 0
            )
            if is_invalid_range:
                assert_equal(
                    actual_value=len(response) == 0,
                    expected_value=True,
                    allure_title="Каталог пустой",
                )
                return

            if is_zero_range:
                assert_equal(
                    actual_value=len(response) == 0,
                    expected_value=True,
                    allure_title="Каталог пустой",
                )
                return

            assert_equal(
                actual_value=len(response) > 0,
                expected_value=True,
                allure_title="Каталог не пустой",
            )
            validate_catalog_response(
                products=response,
                max_price=max_price,
                min_price=min_price
            )

    @allure.title("Фильтр по бренду")
    @pytest.mark.smoke
    @pytest.mark.parametrize("brand", ["Apple", "Xiaomi", "Samsung"])
    def test_brand_filter(self, catalog_service, brand):
        with allure.step(f"Отправка запроса на получение каталога товаров с фильтрацией по бренду - {brand}"):
            params = CatalogRequestModel(
                brand=brand
            )
            response = catalog_service.get_catalog(params=params)
        with allure.step("Валидация ответа каталога товаров"):
            assert_equal(
                actual_value=len(response) > 0,
                expected_value=True,
                allure_title="Каталог не пустой",
            )
            validate_catalog_response(
                products=response,
                brand=brand
            )

    @allure.title("Фильтр по бренду и диапазону цен")
    @pytest.mark.parametrize("brand, min_price, max_price", [
        ("Apple", 70000, 100000),
        ("Samsung", 90000, 120000),
        ("Xiaomi", 100000, 110000)
    ])
    def test_brand_and_price_range_filter(self, catalog_service, brand, min_price, max_price):
        with allure.step(
                f"Отправка запроса на получение каталога товаров с фильтрацией по бренду и диапазону - {brand} "
                f"с диапазоном {min_price} - {max_price}"):
            params = CatalogRequestModel(
                brand=brand,
                min_price=min_price,
                max_price=max_price
            )
            response = catalog_service.get_catalog(params=params)

        with allure.step("Валидация ответа каталога товаров"):
            assert_equal(
                actual_value=len(response) > 0,
                expected_value=True,
                allure_title="Каталог не пустой",
            )
            validate_catalog_response(
                products=response,
                brand=brand,
                min_price=min_price,
                max_price=max_price
            )

    @allure.title("Фильтр по неизвестному бренду")
    @pytest.mark.parametrize("brand", ["NonExistentBrand"])
    def test_unknown_brand(self, catalog_service, brand):
        with allure.step(
                f"Отправка запроса на получение каталога товаров с фильтрацией по несуществующему бренду - {brand}"):
            params = CatalogRequestModel(
                brand=brand
            )
            response = catalog_service.get_catalog(params=params)
        with allure.step("Валидация ответа каталога товаров"):
            assert_equal(
                actual_value=len(response) == 0,
                expected_value=True,
                allure_title="Каталог пустой",
            )

    @allure.title("Сортировка")
    @pytest.mark.smoke
    @pytest.mark.parametrize("sort", [
        SortOption.NAME_ASC,
        SortOption.NAME_DESC,
        SortOption.PRICE_ASC,
        SortOption.PRICE_DESC,
    ])
    def test_sorting(self, catalog_service, sort):
        with allure.step(f"Отправка запроса на получение каталога товаров с сортировкой {SortOption.NAME_ASC.value}"):
            params = CatalogRequestModel(sort=sort)
            response = catalog_service.get_catalog(params=params)

        with allure.step("Валидация ответа каталога товаров"):
            assert_equal(
                actual_value=len(response) > 0,
                expected_value=True,
                allure_title="Каталог не пустой",
            )
            validate_catalog_response(
                products=response,
                sort_direction=sort
            )

    @allure.title("Фильтр: Получение каталога товаров неавторизованным пользователем")
    @pytest.mark.negative
    def test_get_catalog_unauthorized_user(self, catalog_adapter_unauthorized):
        with allure.step("Отправка запроса на получение каталога товаров неавторизованным пользователем"):
            response = catalog_adapter_unauthorized.get_catalog()
        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.UNAUTHORIZED,
                expected_text=CommonResponseMessages.TOKEN_IS_INVALID.value
            )
