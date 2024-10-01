import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from aiohttp import ClientSession, ClientError
from click.testing import CliRunner

from compare_packages import compare_packages, fetch_packages


@pytest.fixture
def mock_api_response():
    """Пример mock ответа API для пакетов."""
    return [
        {"name": "package1", "version": "1.0", "release": "1"},
        {"name": "package2", "version": "2.0", "release": "1"}
    ]


@pytest.fixture
def mock_get_packages_data(mocker, mock_api_response):
    """Mock функции get_packages_data для тестов."""
    return mocker.patch("compare_packages.get_packages_data", return_value=(
        mock_api_response, mock_api_response
    ))


def test_compare_packages_success(mock_get_packages_data):
    """Тест успешного сравнения пакетов с выводом в JSON формате."""
    runner = CliRunner()
    result = runner.invoke(compare_packages, [
        '--url', 'http://test_api.com',
        '--branch1', 'sisyphus',
        '--branch2', 'p10',
        '--arch', 'x86_64'
    ])

    expected_output = json.dumps({
        "in_p10_not_in_sisyphus": [],
        "in_sisyphus_not_in_p10": [],
        "higher_version_in_sisyphus": []
    }, indent=4)

    assert result.exit_code == 0
    assert expected_output in result.output


def test_compare_packages_exception(mock_get_packages_data):
    """Тест на случай возникновения ошибки при получении пакетов."""
    runner = CliRunner()
    mock_get_packages_data.side_effect = Exception("Test exception")

    result = runner.invoke(compare_packages, [
        '--url', 'http://test_api.com',
        '--branch1', 'sisyphus',
        '--branch2', 'p10',
        '--arch', 'x86_64'
    ])

    assert result.exit_code == 0  # Команда завершится успешно
    assert "Произошла ошибка: Test exception" in result.output


@pytest.mark.asyncio
@patch("compare_packages.ClientSession.get")
async def test_fetch_packages_success(mock_get, mock_api_response):
    """Тест успешного запроса пакетов из API."""
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"packages": mock_api_response})
    mock_get.return_value.__aenter__.return_value = mock_response

    async with ClientSession() as session:
        result = await fetch_packages("http://test_api.com", session, "sisyphus")

    assert result == mock_api_response


@pytest.mark.asyncio
@patch("compare_packages.ClientSession.get")
async def test_fetch_packages_connection_error(mock_get):
    """Тест на случай ошибки соединения при запросе пакетов."""
    mock_get.side_effect = ClientError("Connection failed")

    async with ClientSession() as session:
        with pytest.raises(RuntimeError, match="Не удалось установить соединение"):
            await fetch_packages("http://test_api.com", session, "sisyphus")
