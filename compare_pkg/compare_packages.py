#!/usr/bin/env python3
import asyncio
import json
import io
import os
import tarfile
from datetime import datetime
from typing import Optional
from zipfile import ZipFile

import click
import rpm
from aiohttp import ClientSession, ClientError
from environs import Env

env = Env()
env.read_env()

API_URL = env("API_URL")
ARCH_LIST = env("ARCH_LIST").split(", ")


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
            print(f"Запрос к API: {url} с параметрами: {params}")

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("packages", [])
                elif response.status == 400:
                    print(f"Пропускаем архитектуру {arch}: статус 400, {response.reason}")
                    return []  # Пропускаем текущую архитектуру
                else:
                    print(f"Ошибка: статус {response.status}, причина: {response.reason}, параметры: {params}")
                    return []
        except ClientError as e:
            print(f"Попытка {attempt + 1}: ошибка соединения: {e.__repr__()} с параметрами: {params}")
            if attempt < retries - 1:
                await asyncio.sleep(5)
            else:
                raise RuntimeError(f"Не удалось установить соединение после {retries} попыток для {params}")


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
@click.option('--arch', default=None,
              help='Package architectures to filter (comma-separated). If omitted, all architectures from ARCH_LIST will be used.')
@click.option('--output', default='file',
              help='Output format: "file" to save results to a file, or "screen" to print to the console.')
@click.option('--output-folder', default=None, type=click.Path(),
              help='Optional output folder for saving files (defaults to current directory).')
@click.option('--archive', default=None,
              help='Optional archive format to save all results (e.g., zip, tar.gz, tar.bz2).')
def compare_packages(url: str, branch1: str, branch2: str, arch: Optional[str], output: str,
                     output_folder: Optional[str], archive: Optional[str]):
    """
    CLI tool to compare packages between two branches with options for architecture, output format, and archiving.

    :param url: Base API URL.
    :param branch1: First branch to compare.
    :param branch2: Second branch to compare.
    :param arch: Package architectures to filter (comma-separated). If omitted, all architectures from ARCH_LIST will be used.
    :param output: Output format: "file" or "screen".
    :param output_folder: Optional folder to save output files.
    :param archive: Optional archive format to save all results (e.g., zip, tar.gz, tar.bz2).
    """
    # Обрабатываем архитектуры: либо все из ARCH_LIST, либо указанные через опцию
    if arch:
        arch_list = [a.strip() for a in arch.split(",")]
    else:
        arch_list = ARCH_LIST

    # Проверка допустимого формата вывода
    if output not in ['file', 'screen']:
        print("Unsupported output format. Please use 'file' or 'screen'.")
        return

    # Устанавливаем директорию для сохранения файлов (если не указана, используется текущая директория)
    if not output_folder:
        output_folder = os.getcwd()

    # Проверка допустимого формата архива
    supported_archives = ['zip', 'tar.gz', 'tar.bz2']
    if archive and archive not in supported_archives:
        print(f"Unsupported archive format: {archive}. Supported formats are: {', '.join(supported_archives)}.")
        return

    # Устанавливаем время для генерации файлов/архивов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # Функция для получения данных сравнения для каждой архитектуры
        def get_comparison_result(architecture: str) -> str:
            branch1_packages, branch2_packages = asyncio.run(
                get_packages_data(url, branch1, branch2, architecture))
            comparison_result = compare_package_lists(branch1_packages, branch2_packages)
            return json.dumps(comparison_result, indent=4)

        # Если указан архив, то сохраняем сразу в архив
        if archive:
            archive_path = os.path.join(output_folder, f"packages_comparison_{timestamp}.{archive}")

            if archive == "zip":
                with ZipFile(archive_path, 'w') as zipf:
                    for architecture in arch_list:
                        result = get_comparison_result(architecture)
                        json_filename = f"{architecture}_{timestamp}.json"
                        zipf.writestr(json_filename, result)
                print(f"Results archived to {archive_path}")

            elif archive in ["tar.gz", "tar.bz2"]:
                mode = 'w:gz' if archive == "tar.gz" else 'w:bz2'
                with tarfile.open(archive_path, mode) as tar:
                    for architecture in arch_list:
                        result = get_comparison_result(architecture)
                        json_filename = f"{architecture}_{timestamp}.json"
                        tarinfo = tarfile.TarInfo(name=json_filename)
                        tarinfo.size = len(result)
                        tar.addfile(tarinfo, io.BytesIO(result.encode('utf-8')))
                print(f"Results archived to {archive_path}")

        else:
            # Если архивация не указана, обрабатываем результат стандартно
            for architecture in arch_list:
                result = get_comparison_result(architecture)

                # Если output = screen, выводим на экран
                if output == 'screen':
                    print(f"Results for architecture {architecture}:\n{result}")
                else:
                    # Формируем название файла: architecture_timestamp.json
                    filename = f"{architecture}_{timestamp}.json"
                    filepath = os.path.join(output_folder, filename)

                    # Сохраняем результат в файл
                    with open(filepath, 'w') as f:
                        f.write(result)
                    print(f"Result for architecture {architecture} written to {filepath}")

    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    compare_packages()


if __name__ == "__main__":
    main()
