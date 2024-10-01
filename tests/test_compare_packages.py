import pytest
import json
from click.testing import CliRunner
from unittest import mock
from compare_pkg.compare_packages import compare_packages  # Импортируй свою функцию из скрипта


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_get_packages_data():
    with mock.patch('compare_packages.get_packages_data') as mock_data:
        yield mock_data


@pytest.fixture
def mock_compare_package_lists():
    with mock.patch('compare_packages.compare_package_lists') as mock_compare:
        yield mock_compare


# Тест корректного вывода в консоль при использовании json
def test_compare_packages_output_json(runner, mock_get_packages_data, mock_compare_package_lists):
    # Мокаем возвращаемые данные
    mock_get_packages_data.return_value = (
        [{'name': 'pkg1', 'version': '1.0', 'release': '1'}],  # packages branch1
        [{'name': 'pkg2', 'version': '2.0', 'release': '1'}]  # packages branch2
    )

    # Мокаем результат сравнения
    mock_compare_package_lists.return_value = {
        "in_p10_not_in_sisyphus": ["pkg2-2.0-1"],
        "in_sisyphus_not_in_p10": ["pkg1-1.0-1"],
        "higher_version_in_sisyphus": []
    }

    result = runner.invoke(compare_packages,
                           ['--url', 'http://example.com', '--branch1', 'sisyphus', '--branch2', 'p10'])

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "in_p10_not_in_sisyphus": ["pkg2-2.0-1"],
        "in_sisyphus_not_in_p10": ["pkg1-1.0-1"],
        "higher_version_in_sisyphus": []
    }


# Тест записи в файл
def test_compare_packages_output_file(runner, mock_get_packages_data, mock_compare_package_lists, tmp_path):
    mock_get_packages_data.return_value = (
        [{'name': 'pkg1', 'version': '1.0', 'release': '1'}],  # packages branch1
        [{'name': 'pkg2', 'version': '2.0', 'release': '1'}]  # packages branch2
    )

    mock_compare_package_lists.return_value = {
        "in_p10_not_in_sisyphus": ["pkg2-2.0-1"],
        "in_sisyphus_not_in_p10": ["pkg1-1.0-1"],
        "higher_version_in_sisyphus": []
    }

    output_file = tmp_path / "output.json"

    result = runner.invoke(compare_packages,
                           ['--url', 'http://example.com', '--branch1', 'sisyphus', '--branch2', 'p10', '--output-file',
                            str(output_file)])

    assert result.exit_code == 0
    assert json.loads(output_file.read_text()) == {
        "in_p10_not_in_sisyphus": ["pkg2-2.0-1"],
        "in_sisyphus_not_in_p10": ["pkg1-1.0-1"],
        "higher_version_in_sisyphus": []
    }


# Тест на обработку ошибки
def test_compare_packages_error_handling(runner, mock_get_packages_data):
    mock_get_packages_data.side_effect = RuntimeError("Ошибка соединения")

    result = runner.invoke(compare_packages,
                           ['--url', 'http://example.com', '--branch1', 'sisyphus', '--branch2', 'p10'])

    assert result.exit_code == 0
    assert "Произошла ошибка: Ошибка соединения" in result.output

