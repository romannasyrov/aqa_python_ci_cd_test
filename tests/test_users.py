import allure
import pytest
import requests

from clients.api_client import ApiClient


@allure.feature("Users")
@allure.story("Get")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Получение юзера")
def test_get_user(api_client):
    with allure.step("Отправить GET /users/1"):
        response = api_client.get("/users/1")

    with allure.step("Проверить статус 200"):
        assert response.status_code == 200

    with allure.step("Проверить тело ответа"):
        body = response.json()
        assert body["id"] == 1
        assert body["name"]
        assert body["email"]


@allure.feature("Posts")
@allure.story("Create")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Создание поста")
def test_create_post(posts_service, worker_post_data):
    with allure.step("Отправить POST /posts с worker-scoped данными"):
        response = posts_service.create_post(**worker_post_data)

    with allure.step("Проверить, что пост создан (валидация модели ответа)"):
        assert response.id > 0
        assert response.title == worker_post_data["title"]
        assert response.body == worker_post_data["body"]
        assert response.user_id == worker_post_data["userId"]


@allure.feature("API Client")
@allure.story("Retry")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Успех с первой попытки")
def test_retry_success_first_attempt(api_client, mocker):
    with allure.step("Замокать успешный ответ"):
        mock_response = mocker.Mock(status_code=200, json=lambda: {"id": 1})
        mock_request = mocker.patch.object(
            requests.Session, "request", return_value=mock_response
        )

    with allure.step("Отправить GET /posts/1"):
        response = api_client.get("/posts/1")

    with allure.step("Проверить, что запрос был один"):
        assert response.status_code == 200
        assert mock_request.call_count == 1


@allure.feature("API Client")
@allure.story("Retry")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Успех со второй попытки")
def test_retry_on_timeout_then_success(mocker):
    with allure.step("Замокать Timeout, Timeout, затем успех"):
        mock_response = mocker.Mock(status_code=200, json=lambda: {"id": 1})
        mock_request = mocker.patch.object(
            requests.Session,
            "request",
            side_effect=[
                requests.Timeout("timeout"),
                requests.Timeout("timeout"),
                mock_response,
            ],
        )
        mocker.patch("time.sleep")  # не ждём реально

    with allure.step("Отправить запрос"):
        client = ApiClient(host="https://api.example.com")
        response = client.get("/posts/1")

    with allure.step("Проверить, что запрос повторился 3 раза"):
        assert response.status_code == 200
        assert mock_request.call_count == 3


@allure.feature("API Client")
@allure.story("Retry")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Ошибка подключения и после успех")
def test_retry_on_connection_error_then_success(mocker):
    with allure.step("Замокать ConnectionError, затем успех"):
        mock_response = mocker.Mock(status_code=200)
        mock_request = mocker.patch.object(
            requests.Session,
            "request",
            side_effect=[
                requests.ConnectionError("connection error"),
                mock_response,
            ],
        )
        mocker.patch("time.sleep")

    with allure.step("Отправить запрос"):
        client = ApiClient(host="https://api.example.com")
        response = client.get("/posts/1")

    with allure.step("Проверить, что запрос повторился 2 раза"):
        assert response.status_code == 200
        assert mock_request.call_count == 2


@allure.feature("API Client")
@allure.story("Retry")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Все попытки исчерпаны")
def test_retry_all_attempts_failed(mocker):
    with allure.step("Замокать постоянный Timeout"):
        mock_request = mocker.patch.object(
            requests.Session,
            "request",
            side_effect=requests.Timeout("timeout"),
        )
        mocker.patch("time.sleep")

    with allure.step("Отправить запрос и ожидать исключение"):
        client = ApiClient(host="https://api.example.com")
        with pytest.raises(requests.Timeout):
            client.get("/posts/1")

    with allure.step("Проверить, что было 3 попытки"):
        assert mock_request.call_count == 3


@allure.feature("API Client")
@allure.story("Retry")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Тест задержки повторного запроса")
def test_retry_delays(api_client, mocker):
    with allure.step("Мокаем Timeout, time.sleep и random.uniform"):
        mock_request = mocker.patch.object(
            requests.Session,
            "request",
            side_effect=requests.Timeout("timeout"),
        )
        mock_sleep = mocker.patch("time.sleep")
        mocker.patch("random.uniform", return_value=0)

    with allure.step("Отправляем запрос и ждём исключения"):
        with pytest.raises(requests.Timeout):
            api_client.get("/posts/1")

    with allure.step("Проверяем количество попыток и задержек"):
        assert mock_request.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)


@allure.feature("API Client")
@allure.story("Retry")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Без повторного вызова после 404 ошибки")
def test_no_retry_on_404(api_client, mocker):
    with allure.step("Замокать ответ 404"):
        mock_response = mocker.Mock(status_code=404)
        mock_request = mocker.patch.object(
            requests.Session,
            "request",
            return_value=mock_response,
        )

    with allure.step("Отправить GET /posts/999"):
        response = api_client.get("/posts/999")

    with allure.step("Проверить, что запрос был один (без retry)"):
        assert response.status_code == 404
        assert mock_request.call_count == 1


@allure.feature("API Client")
@allure.story("Retry")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Повтор при 5xx, успех после")
@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_retry_on_5xx(api_client, mocker, status):
    with allure.step(f"Замокать {status}, затем 200"):
        mocker.patch("time.sleep")
        mock_request = mocker.patch.object(
            requests.Session,
            "request",
            side_effect=[
                mocker.Mock(status_code=status),
                mocker.Mock(status_code=200),
            ],
        )

    with allure.step("Отправить запрос"):
        response = api_client.get("/posts/1")

    with allure.step("Проверить, что запрос повторился 2 раза"):
        assert response.status_code == 200
        assert mock_request.call_count == 2


@allure.feature("API Client")
@allure.story("Retry")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Все попытки исчерпаны на 5xx")
def test_retry_all_attempts_5xx(api_client, mocker):
    with allure.step("Замокать постоянный 503"):
        mocker.patch("time.sleep")
        mock_request = mocker.patch.object(
            requests.Session,
            "request",
            return_value=mocker.Mock(status_code=503),
        )

    with allure.step("Отправить запрос и ожидать HTTPError"):
        with pytest.raises(requests.HTTPError):
            api_client.get("/posts/1")

    with allure.step("Проверить, что было 3 попытки"):
        assert mock_request.call_count == 3
