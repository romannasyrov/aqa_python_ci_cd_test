from http import HTTPStatus

import allure
import pytest

from src.backend.services.auth.constants.response_messages import AuthResponseMessages
from src.backend.services.auth.models.request_models import RegisterUserRequest
from src.base_model import MessageBaseModel
from src.utils.validators.assert_wrappers import assert_equal
from src.utils.validators.rest_api import validate_response

pytestmark = [
    allure.feature("Тесты на регистрацию"),
    pytest.mark.register,
]


class TestRegister:
    @allure.title("Регистрация: Успешная")
    @pytest.mark.smoke
    def test_register_successful(self, auth_service, unique_username, valid_password):
        with allure.step(f"Регистрация пользователя: {unique_username}"):
            auth_service.register(
                username=unique_username,
                password=valid_password
            )


class TestRegisterNegative:

    @allure.title("Регистрация: Отправка невалидного логина")
    @pytest.mark.negative
    @pytest.mark.parametrize("username", ["u", "us", "use", "user"])
    def test_register_invalid_login(self, auth_adapter, valid_password, username):
        user_data = RegisterUserRequest(
            username=username,
            password=valid_password
        )
        with allure.step(f"Регистрация пользователя: {user_data.username}"):
            response = auth_adapter.register(user_data)

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=AuthResponseMessages.INVALID_USERNAME.value,
                allure_title=f"Ошибка: {AuthResponseMessages.INVALID_USERNAME.value}",
            )

    @allure.title("Регистрация: Отправка пустого логина")
    @pytest.mark.negative
    def test_register_empty_login(self, auth_adapter, valid_password):
        user_data = RegisterUserRequest(
            username="",
            password=valid_password
        )
        with allure.step(f"Регистрация пользователя: {user_data.username}"):
            response = auth_adapter.register(user_data)

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=AuthResponseMessages.INVALID_DATA.value,
                allure_title=f"Ошибка: {AuthResponseMessages.INVALID_DATA.value}",
            )

    @allure.title("Регистрация: Пользователь уже существует")
    @pytest.mark.negative
    def test_register_user_already_exists(self, auth_adapter, registered_user, valid_password):
        user_data = RegisterUserRequest(
            username=registered_user["username"],
            password=registered_user["password"]
        )
        with allure.step(f"Регистрация пользователя: {user_data.username}"):
            response = auth_adapter.register(user_data)

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=AuthResponseMessages.USER_EXISTS.value,
                allure_title=f"Ошибка: {AuthResponseMessages.USER_EXISTS.value}",
            )

    @allure.title("Регистрация: Пароль не соответствует критериям")
    @pytest.mark.negative
    @pytest.mark.parametrize("password", ["blob", "passw!(№", "лицезреть", "   ", "!@#$%^&*", "12345678", "abcdefgh"])
    def test_register_password_doesnt_match_criteria(self, auth_adapter, unique_username, password):
        user_data = RegisterUserRequest(
            username=unique_username,
            password=password
        )
        with allure.step(f"Регистрация пользователя: {user_data.username}"):
            response = auth_adapter.register(user_data)

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=AuthResponseMessages.INVALID_PASSWORD.value,
                allure_title=f"Ошибка: {AuthResponseMessages.INVALID_PASSWORD.value}",
            )

    @allure.title("Регистрация: Очень длинный пароль")
    @pytest.mark.negative
    @pytest.mark.bug
    @pytest.mark.skip(
        reason="Баг в API: нет ограничения на длину пароля")
    def test_register_long_password(self, auth_adapter, unique_username):
        user_data = RegisterUserRequest(
            username=unique_username,
            password="a"*200
        )
        with allure.step(f"Регистрация пользователя: {user_data.username}"):
            response = auth_adapter.register(user_data)

        with allure.step("Валидация ответа"):
            validate_response(
                response=response,
                expected_status=HTTPStatus.BAD_REQUEST
            )

            response_data = MessageBaseModel.model_validate(response.json())

            assert_equal(
                actual_value=response_data.message,
                expected_value=AuthResponseMessages.INVALID_PASSWORD.value,
                allure_title=f"Ошибка: {AuthResponseMessages.INVALID_PASSWORD.value}",
            )
