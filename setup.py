from setuptools import setup, find_packages
setup(
    name="compare-packages",  # Название пакета
    version="0.1.0",  # Версия пакета
    packages=find_packages(),  # Поиск пакетов в проекте
    install_requires=[
        "aiohttp==3.10.8",
        "click==8.1.7",
        "environs==11.0.0",
        "rpm==0.2.0",
        # Убедитесь, что тестовые зависимости указаны в extras_require, а не в install_requires
    ],
    extras_require={
        'dev': [
            "pytest==8.3.3",
            "pytest-asyncio==0.24.0",
            "pytest-mock==3.14.0",
        ]
    },
    entry_points={
        'console_scripts': [
            'compare-packages=compare_pkg.compare_packages:main',  # Указываем команду и точку входа
        ],
    },
    author="Ilya Volodin",
    author_email="ilya.v.py@gmail.com",
    description="CLI tool for comparing binary packages between two branches in ALT Linux.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/PkgDiffBranch",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)

