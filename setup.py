import pathlib

from setuptools import find_packages, setup

BASE_DIR = pathlib.Path(__file__).resolve().parent


setup(
    name="awaiter",
    version="0.0.1",
    packages=find_packages(),
    long_description=(BASE_DIR / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Yuki Igarashi",
    author_email="me@bonprosoft.com",
    license="MIT License",
    install_requires=[
        "astor>=0.8.0,<1.0.0",
        "asyncx>=0.0.3",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-asyncio",
        ],
        "lint": [
            "black==22.3.0",
            "flake8==3.9.2",
            "isort==5.1.4",
            "mypy==0.950",
            "pysen==0.10.2",
        ],
    },
    package_data={"awaiter": ["py.typed"]},
)
