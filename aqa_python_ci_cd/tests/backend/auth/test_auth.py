from http import HTTPStatus

import allure
import pytest

from src.backend.services.auth.constants.response_messages import AuthResponseMessages
from src.backend.services.auth.models.request_models import LoginUserRequest
from src.base_model import MessageBaseModel
from src.utils.validators.assert_wrappers import assert_equal
from src.utils.validators.rest_api import validate_response

pytestmark = [
    allure.feature("Тесты на авторизацию"),
    pytest.mark.auth,
]


class TestAuth:

    @allure.title('Авторизация: Успешная')
    @pytest.mark.smoke
    def test_auth_successful(self, auth_service, registered_user):
        username = registered_user["username"]
        password = registered_user["password"]

        with allure.step(f"Авторизация пользователя: {username}"):
            response = auth_service.login(
                username=username,
                password=password
            )
        with allure.step("Проверка наличия токена в ответе"):
            assert_equal(
                actual_value=response.token is not None,
                expected_value=True,
                allure_title="В ответе получен токен"
            )


class TestAuthNegative:

    @allure.title('Авторизация: Невалидный логин')
    @pytest.mark.smoke
    @pytest.mark.negative
    def test_auth_invalid_login(self, auth_adapter, valid_password, unique_username):
        user_data = LoginUserRequest(
            username=unique_username,
            password=valid_password
        )

        with allure.step(f"Авторизация пользователя: {user_data.username} с паролем {user_data.password}"):
            response = auth_adapter.login(user_data=user_data)

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.UNAUTHORIZED
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=AuthResponseMessages.INVALID_CREDENTIALS.value,
                allure_title=f"Ошибка: {AuthResponseMessages.INVALID_CREDENTIALS.value}",
            )

    @allure.title('Авторизация: Невалидный пароль')
    @pytest.mark.smoke
    @pytest.mark.negative
    @pytest.mark.parametrize("password", ["blob", "passw!23", "   ", ""])
    def test_auth_invalid_password(self, auth_adapter, registered_user, password):
        user_data = LoginUserRequest(
            username=registered_user["username"],
            password=password
        )

        with allure.step(f"Авторизация пользователя: {user_data.username} с паролем {user_data.password}"):
            response = auth_adapter.login(user_data=user_data)

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.UNAUTHORIZED
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=AuthResponseMessages.INVALID_CREDENTIALS.value,
                allure_title=f"Ошибка: {AuthResponseMessages.INVALID_CREDENTIALS.value}",
            )
