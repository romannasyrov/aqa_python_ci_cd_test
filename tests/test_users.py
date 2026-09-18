import allure
import pytest
import requests

from clients.api_client import ApiClient


@allure.title('Получение юзера')
def test_get_user(api_client):
    response = api_client.get("/users/1")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == 1
    assert body["name"]
    assert body["email"]


@allure.title('Создание юзера')
def test_create_post(posts_service):
    response = posts_service.create_post(
        title="bla",
        body="bla123",
        userId=1
    )

    body = response.json()

    assert response.status_code == 201
    assert body["title"] == "bla"
    assert body["body"] == "bla123"
    assert body["user_id"] == 1


@allure.title('Успех с первой попытки')
def test_retry_success_first_attempt(api_client, mocker):
    mock_response = mocker.Mock(status_code=200, json=lambda: {"id": 1})
    mock_request = mocker.patch.object(
        requests.Session, "request", return_value=mock_response
    )

    response = api_client.get("/posts/1")

    assert response.status_code == 200
    assert mock_request.call_count == 1


@allure.title('Успех со второй попытки')
def test_retry_on_timeout_then_success(mocker):
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

    client = ApiClient(host="https://api.example.com")
    response = client.get("/posts/1")

    assert response.status_code == 200
    assert mock_request.call_count == 3


@allure.title('Ошибка подключения и после успех')
def test_retry_on_connection_error_then_success(mocker):
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

    client = ApiClient(host="https://api.example.com")
    response = client.get("/posts/1")

    assert response.status_code == 200
    assert mock_request.call_count == 2


@allure.title('Все попытки исчерпаны')
def test_retry_all_attempts_failed(mocker):
    mock_request = mocker.patch.object(
        requests.Session,
        "request",
        side_effect=requests.Timeout("timeout"),
    )
    mocker.patch("time.sleep")

    client = ApiClient(host="https://api.example.com")

    with pytest.raises(requests.Timeout):
        client.get("/posts/1")

    assert mock_request.call_count == 3


@allure.title('Максимум попыток')
def test_retry_count(api_client, mocker):
    mock_request = mocker.patch.object(
        requests.Session,
        "request",
        side_effect=requests.Timeout("timeout"),
    )
    mocker.patch("time.sleep")

    with pytest.raises(requests.Timeout):
        api_client.get("/posts/1")

    assert mock_request.call_count == 3


@allure.title('Тест задержки повторного запроса')
def test_retry_delays(api_client, mocker):
    mock_request = mocker.patch.object(
        requests.Session,
        "request",
        side_effect=requests.Timeout("timeout"),
    )
    mock_sleep = mocker.patch("time.sleep")

    with pytest.raises(requests.Timeout):
        api_client.get("/posts/1")

    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1)
    mock_sleep.assert_any_call(2)


@allure.title('Без повторного вызова после 404 ошибки')
def test_no_retry_on_404(api_client, mocker):
    mock_response = mocker.Mock(status_code=404)
    mock_request = mocker.patch.object(
        requests.Session,
        "request",
        return_value=mock_response,
    )

    response = api_client.get("/posts/999")

    assert response.status_code == 404
    assert mock_request.call_count == 1  # retry не вызывался
