import pytest
from aiohttp import ClientError

from compare_packages import get_packages_data  # Импортируем функцию, которую тестируем


@pytest.mark.asyncio
async def test_get_packages_data_success(mocker):
    """
    Тест на успешное получение данных для обеих веток.
    """
    mock_packages_branch1 = [{"name": "package1", "version": "1.0", "release": "1"}]
    mock_packages_branch2 = [{"name": "package2", "version": "2.0", "release": "1"}]

    # Мокаем функцию fetch_packages, которая возвращает разные данные для разных веток
    mocker.patch("compare_packages.fetch_packages", side_effect=[mock_packages_branch1, mock_packages_branch2])

    # Вызываем тестируемую функцию
    packages1, packages2 = await get_packages_data("http://test-url.com", "branch1", "branch2", "x86_64")

    # Проверяем, что данные корректно возвращены для обеих веток
    assert packages1 == mock_packages_branch1
    assert packages2 == mock_packages_branch2


@pytest.mark.asyncio
async def test_get_packages_data_fetch_error(mocker):
    """
    Тест на обработку ошибки при запросе для одной из веток.
    """
    mock_packages_branch1 = [{"name": "package1", "version": "1.0", "release": "1"}]

    # Мокаем fetch_packages, первая ветка возвращает данные, вторая - выбрасывает ошибку
    mocker.patch("compare_packages.fetch_packages",
                 side_effect=[mock_packages_branch1, ClientError("Connection error")])

    # Вызываем тестируемую функцию и проверяем, что ошибка пробрасывается
    with pytest.raises(ClientError):
        await get_packages_data("http://test-url.com", "branch1", "branch2", "x86_64")


@pytest.mark.asyncio
async def test_get_packages_data_architecture_handling(mocker):
    """
    Тест на правильную обработку параметра архитектуры.
    """
    mock_packages_branch1 = [{"name": "package1", "version": "1.0", "release": "1"}]
    mock_packages_branch2 = [{"name": "package2", "version": "2.0", "release": "1"}]

    # Мокаем fetch_packages, чтобы убедиться, что параметр арх передается правильно
    fetch_mock = mocker.patch("compare_packages.fetch_packages",
                              side_effect=[mock_packages_branch1, mock_packages_branch2])

    # Вызываем тестируемую функцию с архитектурой arm64
    packages1, packages2 = await get_packages_data("http://test-url.com", "branch1", "branch2", "arm64")

    # Проверяем, что данные корректно возвращены для обеих веток
    assert packages1 == mock_packages_branch1
    assert packages2 == mock_packages_branch2

    # Проверяем, что архитектура была передана правильно
    fetch_mock.assert_any_call("http://test-url.com", mocker.ANY, "branch1", "arm64")
    fetch_mock.assert_any_call("http://test-url.com", mocker.ANY, "branch2", "arm64")
