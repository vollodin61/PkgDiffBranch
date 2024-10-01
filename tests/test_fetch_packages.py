import pytest
from aiohttp import ClientSession
from unittest.mock import AsyncMock
from aiohttp.client_exceptions import ClientError

from compare_pkg.compare_packages import fetch_packages  # Импорт функции из твоего модуля


@pytest.mark.asyncio
async def test_fetch_packages_success(mocker):
    """
    Тест на успешный запрос, когда API возвращает данные о пакетах.
    """
    mock_response_data = {"packages": [{"name": "package1", "version": "1.0", "release": "1"}]}

    # Мокируем ответ с кодом 200 и нужными данными
    mock_session_get = mocker.patch("aiohttp.ClientSession.get")
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_session_get.return_value.__aenter__.return_value = mock_response

    async with ClientSession() as session:
        packages = await fetch_packages("http://test-url.com", session, "branch1")
        assert packages == mock_response_data["packages"]


@pytest.mark.asyncio
async def test_fetch_packages_http_error(mocker):
    """
    Тест на обработку ошибки, когда API возвращает статус, отличный от 200.
    """
    mock_session_get = mocker.patch("aiohttp.ClientSession.get")
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_session_get.return_value.__aenter__.return_value = mock_response

    async with ClientSession() as session:
        packages = await fetch_packages("http://test-url.com", session, "branch1")
        assert packages == []


@pytest.mark.asyncio
async def test_fetch_packages_client_error(mocker):
    """
    Тест на обработку ошибки соединения (ClientError).
    """
    mock_session_get = mocker.patch("aiohttp.ClientSession.get", side_effect=ClientError("Connection error"))

    async with ClientSession() as session:
        with pytest.raises(RuntimeError, match="Не удалось установить соединение после 3 попыток"):
            await fetch_packages("http://test-url.com", session, "branch1")


@pytest.mark.asyncio
async def test_fetch_packages_retry_on_error(mocker):
    """
    Тест на проверку механизма повторных попыток при ошибке соединения.
    """
    mock_session_get = mocker.patch("aiohttp.ClientSession.get")
    mock_session_get.side_effect = [
        ClientError("Connection error"),
        ClientError("Connection error"),
        AsyncMock(status=200, json=AsyncMock(return_value={"packages": []}))
    ]

    async with ClientSession() as session:
        packages = await fetch_packages("http://test-url.com", session, "branch1")
        assert packages == []
