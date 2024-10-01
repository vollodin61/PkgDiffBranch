import pytest
from compare_packages import compare_package_lists


@pytest.fixture
def packages_sisyphus():
    """Пример списка пакетов для ветки Sisyphus."""
    return [
        {"name": "package1", "version": "1.0", "release": "1"},
        {"name": "package2", "version": "2.0", "release": "1"},
        {"name": "package3", "version": "3.0", "release": "1"}
    ]

@pytest.fixture
def packages_p10():
    """Пример списка пакетов для ветки p10."""
    return [
        {"name": "package2", "version": "1.9", "release": "1"},
        {"name": "package3", "version": "3.0", "release": "1"},
        {"name": "package4", "version": "1.0", "release": "1"}
    ]


def test_compare_package_lists(mocker, packages_sisyphus, packages_p10):
    """
    Тест на корректное сравнение двух списков пакетов.
    """
    # Мокаем функцию labelCompare из rpm, чтобы она корректно сравнивала версии пакетов
    mocker.patch("compare_packages.rpm.labelCompare", side_effect=lambda evr1, evr2: -1 if evr1 < evr2 else 0)

    # Сравниваем пакеты
    result = compare_package_lists(packages_sisyphus, packages_p10)

    # Проверяем результат
    assert result == {
        "in_p10_not_in_sisyphus": ["package4"],
        "in_sisyphus_not_in_p10": ["package1"],
        "higher_version_in_sisyphus": ["package2"]
    }


def test_compare_package_lists_no_differences(mocker, packages_sisyphus):
    """
    Тест на случай, когда оба списка одинаковы.
    """
    # Мокаем labelCompare для корректного сравнения одинаковых версий
    mocker.patch("compare_packages.rpm.labelCompare", return_value=0)

    # Сравниваем идентичные списки пакетов
    result = compare_package_lists(packages_sisyphus, packages_sisyphus)

    # Проверяем, что различий нет
    assert result == {
        "in_p10_not_in_sisyphus": [],
        "in_sisyphus_not_in_p10": [],
        "higher_version_in_sisyphus": []
    }


def test_compare_package_lists_only_in_one_branch(mocker):
    """
    Тест на случай, когда пакеты присутствуют только в одной из веток.
    """
    # Пакеты только в ветке Sisyphus
    packages_sisyphus = [{"name": "package1", "version": "1.0", "release": "1"}]
    packages_p10 = []

    # Мокаем labelCompare
    mocker.patch("compare_packages.rpm.labelCompare", return_value=0)

    # Сравниваем пакеты
    result = compare_package_lists(packages_sisyphus, packages_p10)

    # Проверяем, что пакет присутствует только в ветке Sisyphus
    assert result == {
        "in_p10_not_in_sisyphus": [],
        "in_sisyphus_not_in_p10": ["package1"],
        "higher_version_in_sisyphus": []
    }


def test_compare_package_lists_version_downgrade(mocker):
    """
    Тест на случай, когда версия пакета в p10 выше, чем в Sisyphus.
    """
    packages_sisyphus = [{"name": "package1", "version": "1.0", "release": "1"}]
    packages_p10 = [{"name": "package1", "version": "1.1", "release": "1"}]

    # Мокаем labelCompare так, чтобы версия в p10 была выше
    mocker.patch("compare_packages.rpm.labelCompare", return_value=1)

    # Сравниваем пакеты
    result = compare_package_lists(packages_sisyphus, packages_p10)

    # Проверяем, что нет пакетов с более высокими версиями в Sisyphus
    assert result == {
        "in_p10_not_in_sisyphus": [],
        "in_sisyphus_not_in_p10": [],
        "higher_version_in_sisyphus": []
    }
