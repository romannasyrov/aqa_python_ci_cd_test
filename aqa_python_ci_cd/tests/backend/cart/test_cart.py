import random
from http import HTTPStatus

import allure
import pytest

from src.backend.services.cart.constants.response_messages import CartResponseMessages
from src.backend.services.cart.models.request_models import AddToCartRequest, RemoveFromCartRequest
from src.base_model import MessageBaseModel
from src.utils.constants.response_messages import CommonResponseMessages
from src.utils.validators.assert_wrappers import assert_equal, attach_expected_data
from src.utils.validators.rest_api import validate_response
from tests.backend.cart.conftest import available_products

pytestmark = [
    allure.feature("Тесты на корзину"),
    pytest.mark.cart,
]


class TestCart:

    @allure.title("Корзина: Добавить товар в корзину")
    @pytest.mark.smoke
    def test_add_to_cart(self, cart_service, available_products):
        with allure.step("Получение тестового товара"):
            test_product = random.choice(available_products)
            attach_expected_data(
                data=test_product,
                name=f"Эталонный товар: {test_product.name}"
            )

        with allure.step("Отправка запроса на добавление товара в корзину"):
            cart_service.add_to_cart(
                params=AddToCartRequest(
                    item_id=test_product.id,
                    quantity=1
                )
            )

        with allure.step("Проверка состояния корзины с товаром"):
            cart = cart_service.get_cart()

            assert_equal(
                actual_value=len(cart.items),
                expected_value=1,
                allure_title="Добавлен только один товар в корзину",
            )
            assert_equal(
                actual_value=cart.items[0].quantity,
                expected_value=1,
                allure_title=f"Добавлено корректное количество товара: {cart.items[0].quantity}",
            )
            assert_equal(
                actual_value=cart.items[0].item_id,
                expected_value=test_product.id,
                allure_title=f"У товара ожидаемый id: {test_product.id}",
            )
            assert_equal(
                actual_value=cart.items[0].name,
                expected_value=test_product.name,
                allure_title=f"У товара ожидаемое наименование: {test_product.name}",
            )
            assert_equal(
                actual_value=cart.items[0].price,
                expected_value=test_product.price,
                allure_title=f"У товара ожидаемая цена: {test_product.price}",
            )

    @allure.title("Корзина: Удалить товар из корзины")
    @pytest.mark.smoke
    def test_remove_item_from_cart(self, cart_service, available_products):
        with allure.step("Получение тестового товара"):
            test_product = random.choice(available_products)
            attach_expected_data(
                data=test_product,
                name=f"Эталонный товар: {test_product.name}"
            )

        with allure.step("Отправка запроса на добавление товара в корзину"):
            cart_service.add_to_cart(
                params=AddToCartRequest(
                    item_id=test_product.id,
                    quantity=1
                )
            )
        with allure.step(f"{CartResponseMessages.ITEM_REMOVED_FROM_CART.value}"):
            response = cart_service.remove_from_cart(
                params=RemoveFromCartRequest(
                    item_id=test_product.id,
                )
            )
            assert_equal(
                actual_value=response.message,
                expected_value=CartResponseMessages.ITEM_REMOVED_FROM_CART.value,
            )

        with allure.step("Проверка состояния корзины"):
            cart = cart_service.get_cart()
            assert_equal(
                actual_value=len(cart.items),
                expected_value=0,
                allure_title="В корзине после удаления отсутствуют товары",
            )

    @allure.title("Корзина: Добавить один товар несколько раз")
    @pytest.mark.smoke
    def test_add_single_product_multiple_times(self, cart_service, available_products):
        with allure.step("Получение тестового товара"):
            test_product = random.choice(available_products)
            attach_expected_data(
                data=test_product,
                name=f"Эталонный товар: {test_product.name}"
            )

        with allure.step("Отправка запроса на добавление товара в корзину 2 раза"):
            cart_service.add_to_cart(
                params=AddToCartRequest(
                    item_id=test_product.id,
                    quantity=1
                )
            )
            cart_service.add_to_cart(
                params=AddToCartRequest(
                    item_id=test_product.id,
                    quantity=1
                )
            )

            with allure.step("Проверка состояния корзины с товарами"):
                cart = cart_service.get_cart()

                assert_equal(
                    actual_value=cart.items[0].quantity,
                    expected_value=2,
                    allure_title="Количество товара в корзине: 2",
                )

    @allure.title("Корзина: Добавить разные товары в разном количестве")
    @pytest.mark.smoke
    def test_add_multiple_different_items(self, cart_service, available_products):
        with allure.step("Получить 2 разных тестовых товара"):
            if len(available_products) < 2:
                pytest.skip("Недостаточно товаров в каталоге для теста")

            item1, item2 = random.sample(available_products, k=2)
            qty1 = random.randint(1, 99)
            qty2 = random.randint(1, 99)
            attach_expected_data(
                data={
                    "product": item1.model_dump(),
                    "expected_quantity": qty1
                },
                name=f"Эталонный товар: {item1.name}",
            )
            attach_expected_data(
                data={
                    "product": item2.model_dump(),
                    "expected_quantity": qty2
                },
                name=f"Эталонный товар: {item2.name}"
            )

        with allure.step("Отправка запроса на добавление товаров в корзину"):
            cart_service.add_to_cart(AddToCartRequest(item_id=item1.id, quantity=qty1))
            cart_service.add_to_cart(AddToCartRequest(item_id=item2.id, quantity=qty2))

        with allure.step("Проверка состояния корзины с товаром"):
            cart = cart_service.get_cart()

            assert_equal(
                actual_value=len(cart.items),
                expected_value=2,
                allure_title="В корзине 2 товара",
            )

        with allure.step("Проверка что ожидаемые товары добавлены в корзину"):
            cart_item1 = next((item for item in cart.items if item.item_id == item1.id), None)
            cart_item2 = next((item for item in cart.items if item.item_id == item2.id), None)

            assert cart_item1 is not None
            assert cart_item2 is not None

            assert_equal(
                actual_value=cart_item1.quantity,
                expected_value=qty1,
                allure_title=f"Товар '{item1.name}' с item_id: {item1.id} добавлен в корзину в кол-ве: {qty1}"
            )
            assert_equal(
                actual_value=cart_item2.quantity,
                expected_value=qty2,
                allure_title=f"Товар '{item2.name}' с item_id: {item2.id} добавлен в корзину в кол-ве: {qty2}"
            )


class TestCartNegative:

    @allure.title("Корзина: Добавить товар неавторизованным пользователем")
    @pytest.mark.smoke
    @pytest.mark.negative
    def test_add_item_unauthorized_user(self, cart_adapter_unauthorized, available_products):
        with allure.step("Получение тестового товара"):
            test_product = random.choice(available_products)
            attach_expected_data(
                data=test_product,
                name=f"Эталонный товар: {test_product.name}"
            )

        with allure.step(
                f"Отправка запроса на добавление товара с id {test_product.id} в корзину неавторизованным пользователем"
        ):
            response = cart_adapter_unauthorized.add_to_cart(
                json=AddToCartRequest(
                    item_id=test_product.id,
                    quantity=1
                ).model_dump()
            )
        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.UNAUTHORIZED,
                expected_text=CommonResponseMessages.TOKEN_IS_INVALID.value
            )

    @allure.title("Корзина: Удалить товар не добавленный в корзину")
    @pytest.mark.negative
    def test_remove_item_not_in_cart(self, cart_adapter, available_products):
        with allure.step("Получение тестового товара"):
            test_product = random.choice(available_products)
            attach_expected_data(
                data=test_product,
                name=f"Эталонный товар: {test_product.name}"
            )

        with allure.step("Удалить товар не добавленный в корзину"):
            response = cart_adapter.remove_from_cart(
                json=RemoveFromCartRequest(
                    item_id=test_product.id
                ).model_dump()
            )

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.OK
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=CartResponseMessages.NO_PRODUCTS_IN_CART.value,
                allure_title=CartResponseMessages.NO_PRODUCTS_IN_CART.value
            )

    @allure.title("Корзина: Добавить товар с невалидным item_id")
    @pytest.mark.bug
    @pytest.mark.negative
    @pytest.mark.parametrize("item_id", [-1, 0, 999999])
    @pytest.mark.skip(
        reason="Баг в API: ожидалась корректная обработка невалидных item_id`s, но сервер возвращает — "
               "500 Internal Server Error")
    def test_add_invalid_item_id(self, cart_adapter, item_id):
        with allure.step(f"Отправить запрос на добавление товара с item_id: {item_id}"):
            response = cart_adapter.add_to_cart(
                json=AddToCartRequest(
                    item_id=item_id,
                    quantity=1
                ).model_dump()
            )

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )
            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=CommonResponseMessages.INVALID_DATA.value,
                allure_title=f"Invalid item_id: {item_id}"
            )

    @allure.title("Корзина: Добавить товар с quantity = 0")
    @pytest.mark.bug
    @pytest.mark.negative
    @pytest.mark.skip(reason="Баг в API: ожидалась ошибка при добавлении товара с невалидным quantity, "
                             f"но сервер возвращает 200 с сообщением '{CartResponseMessages.ITEM_ADDED_TO_CART}'")
    def test_add_zero_quantity(self, cart_adapter, available_products):
        with allure.step("Получить случайный товар из каталога"):
            test_product = random.choice(available_products)

        with allure.step("Отправить запрос на добавление товара в корзину в quantity = 0"):
            response = cart_adapter.add_to_cart(
                params=AddToCartRequest(
                    item_id=test_product.id,
                    quantity=0
                ).model_dump()
            )

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )
            response_data = MessageBaseModel.model_validate(response.json())
            assert_equal(
                actual_value=response_data.message,
                expected_value=CommonResponseMessages.INVALID_DATA.value,
                allure_title=f"Ошибка: отправлен некорректный запрос с quantity = 0",
            )

    @allure.title("Корзина: Удалить товар с несуществующим item_id")
    @pytest.mark.bug
    @pytest.mark.negative
    @pytest.mark.skip(reason=f"Баг в API: удаление несуществующего товара возвращает 200 с сообщением \
        '{CartResponseMessages.NO_PRODUCTS_IN_CART.value}'")
    def test_remove_non_existent_item(self, cart_adapter, catalog_service):
        with allure.step("Получение каталога товаров"):
            test_products = catalog_service.get_catalog()
        with allure.step("Получить максимальный item_id из каталога и прибавить к нему 1"):
            max_item_id = max(product.id for product in test_products)
            non_existent_id = max_item_id + 1

        with allure.step("Удалить товар с несуществующим item_id"):
            response = cart_adapter.remove_from_cart(
                json=RemoveFromCartRequest(
                    item_id=non_existent_id,
                ).model_dump()
            )
        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=CommonResponseMessages.PRODUCT_NOT_FOUND.value,
                allure_title=f"Ошибка: {CommonResponseMessages.PRODUCT_NOT_FOUND.value}",
            )

    @allure.title("Корзина: Добавить товар с несуществующим item_id")
    @pytest.mark.bug
    @pytest.mark.negative
    @pytest.mark.skip(reason="Баг в API: ожидалась ошибка при добавлении товара с несуществующим item_id")
    def test_add_non_existent_item(self, cart_adapter, available_products, catalog_service):
        with allure.step("Получение каталога товаров"):
            test_products = catalog_service.get_catalog()
        with allure.step("Получить максимальный item_id из каталога и прибавить к нему 1"):
            max_item_id = max(product.id for product in test_products)
            non_existent_id = max_item_id + 1

        with allure.step(
                f"Отправка запроса на добавление товара с несуществующим item_id в корзину: {non_existent_id}"):
            response = cart_adapter.add_to_cart(
                params=AddToCartRequest(
                    item_id=non_existent_id,
                    quantity=1
                ).model_dump()
            )

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=CommonResponseMessages.PRODUCT_NOT_FOUND.value,
                allure_title=f"Ошибка: {CommonResponseMessages.PRODUCT_NOT_FOUND.value}",
            )
