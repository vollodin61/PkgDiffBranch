#!/usr/bin/env python3
import asyncio
import json
from typing import Optional

import click
import rpm
import asyncio
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

