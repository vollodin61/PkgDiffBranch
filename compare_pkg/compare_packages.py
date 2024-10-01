#!/usr/bin/env python3
import asyncio
import json
from typing import Optional

import click
import rpm
from aiohttp import ClientSession, ClientError
from environs import Env

env = Env()
env.read_env()

API_URL = env("API_URL")


async def fetch_packages(url: str, session: ClientSession, branch: str, arch: str = "x86_64") -> list[dict[str, str]]:
    """
    Асинхронный запрос к API для получения списка пакетов.

    :param url: Базовый URL для запроса.
    :param session: Aiohttp сессия для выполнения запросов.
    :param branch: Название ветки для запроса.
    :param arch: Архитектура для запроса (по умолчанию "x86_64").
    :return: Список пакетов в виде словарей.
    """
    url = f"{url}/{branch}"
    params = {"arch": arch}
    retries = 3
    for attempt in range(retries):
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("packages", [])
                else:
                    print(f"Ошибка: статус {response.status}")
                    return []
        except ClientError as e:
            print(f"Попытка {attempt + 1}: ошибка соединения: {e.__repr__()}")
            if attempt < retries - 1:
                await asyncio.sleep(5)  # Изменено на асинхронный sleep
            else:
                raise RuntimeError(f"Не удалось установить соединение после {retries} попыток")


async def get_packages_data(url: str, branch1: str, branch2: str, arch: str) -> tuple[
    list[dict[str, str]], list[dict[str, str]]]:
    """
    Получает данные для двух веток и возвращает их.

    :param url: Базовый URL для API.
    :param branch1: Первая ветка для запроса.
    :param branch2: Вторая ветка для запроса.
    :param arch: Архитектура пакетов.
    :return: Кортеж из списков пакетов для обеих веток.
    """
    async with ClientSession() as session:
        packages1 = await fetch_packages(url, session, branch1, arch)
        packages2 = await fetch_packages(url, session, branch2, arch)
        return packages1, packages2


def compare_package_lists(packages1: list[dict[str, str]], packages2: list[dict[str, str]]) -> dict[str, list[str]]:
    """
    Сравнивает два списка пакетов.

    :param packages1: Список пакетов первой ветки.
    :param packages2: Список пакетов второй ветки.
    :return: Словарь с результатами сравнения.
    """
    diff = {
        "in_p10_not_in_sisyphus": [],
        "in_sisyphus_not_in_p10": [],
        "higher_version_in_sisyphus": []
    }

    sisyphus_pkgs = {pkg['name']: pkg for pkg in packages1}
    p10_pkgs = {pkg['name']: pkg for pkg in packages2}

    for pkg_name in p10_pkgs:
        if pkg_name not in sisyphus_pkgs:
            # Добавляем название пакета с его версией
            version = f"{p10_pkgs[pkg_name]['version']}-{p10_pkgs[pkg_name]['release']}"
            diff["in_p10_not_in_sisyphus"].append(f"{pkg_name}-{version}")
        else:
            p10_pkg = p10_pkgs[pkg_name]
            sisyphus_pkg = sisyphus_pkgs[pkg_name]
            # Сравнение версий с помощью rpm (epoch-version-release)
            evr1 = f"{p10_pkg['version']}-{p10_pkg['release']}"
            evr2 = f"{sisyphus_pkg['version']}-{sisyphus_pkg['release']}"
            if rpm.labelCompare(evr1, evr2) < 0:
                # Добавляем название пакета с его версией
                diff["higher_version_in_sisyphus"].append(f"{pkg_name}-{evr2}")

    for pkg_name in sisyphus_pkgs:
        if pkg_name not in p10_pkgs:
            # Добавляем название пакета с его версией
            version = f"{sisyphus_pkgs[pkg_name]['version']}-{sisyphus_pkgs[pkg_name]['release']}"
            diff["in_sisyphus_not_in_p10"].append(f"{pkg_name}-{version}")

    return diff


@click.command()
@click.option('--url', default=API_URL, help='Base API URL.')
@click.option('--branch1', default='sisyphus', help='First branch to compare.')
@click.option('--branch2', default='p10', help='Second branch to compare.')
@click.option('--arch', default='x86_64', help='Package architecture to filter.')
@click.option('--output', default='json', help='Output format (json or file).')
@click.option('--output-file', default=None, type=click.Path(), help='Optional output to a JSON file.')
def compare_packages(url: str, branch1: str, branch2: str, arch: str, output: str, output_file: Optional[str]):
    """
    Создание cli-утилиты для сравнения пакетов между двумя ветвями.

    :param url: Базовый URL для API.
    :param branch1: Первая ветка для сравнения.
    :param branch2: Вторая ветка для сравнения.
    :param arch: Архитектура пакетов.
    :param output: Формат вывода (json или файл).
    :param output_file: Опциональный файл для вывода JSON.
    """
    try:
        branch1_packages, branch2_packages = asyncio.run(get_packages_data(url, branch1, branch2, arch))
        comparison_result = compare_package_lists(branch1_packages, branch2_packages)

        if output == 'json':
            result = json.dumps(comparison_result, indent=4)
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(result)
                print(f"Result written to {output_file}")
            else:
                print(result)
        else:
            print("Unsupported output format. Please use 'json'.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def main():
    compare_packages()


if __name__ == "__main__":
    main()
