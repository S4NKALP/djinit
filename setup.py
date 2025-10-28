from setuptools import find_packages, setup

setup(
    name="djinit",
    version="0.1.0",
    description="A CLI tool to setup Django projects",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Sankalp Tharu",
    author_email="sankalptharu50028@gmail.com",
    url="https://github.com/S4NKALP/djinit",
    packages=find_packages(include=["src", "src.*"]),
    include_package_data=True,
    install_requires=[
        "ruff>=0.14.2",
        "click>=8.3.0",
        "rich>=14.2.0",
        "django-environ==0.11.2",
    ],
    entry_points={"console_scripts": ["djinit=src.generator:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Django",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=[
        "django",
        "cli",
        "project",
        "djinit",
        "dj",
        "django-init",
        "django project",
        "django starter",
    ],
    python_requires=">=3.13",
    project_urls={
        "Bug Reports": "https://github.com/S4NKALP/djinit/issues",
        "Source": "https://github.com/S4NKALP/djinit",
        "Documentation": "https://github.com/S4NKALP/djinit#readme",
    },
)
