from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
long_description = Path("README.md").read_text(encoding="utf-8")

setup(
    name='cloudcraver',
    version='1.0.0',
    author='Manav Adwani',
    author_email='manavadwani86@gmail.com',
    description='Infrastructure Template Generator and Validator with Plugin System',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/upes-open/OSoC-25-Cloud-Craver',

    # Packaging
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    py_modules=["main"],  # Make src/main.py installable

    # Data inclusion
    include_package_data=True,

    # Dependencies
    install_requires=[
        "click",
        "rich",
        "dynaconf",
        "Jinja2",
        "pathlib2",
        "python-dotenv",
        "GitPython",
        "PyYAML",
        "jsonschema",
        "requests",
        "python-dateutil",
        "psutil",
        "colorlog",
        "argparse",
        "regex",
        "python-magic",
        "cryptography",
        "pydantic",
        "aiohttp",
        "orjson",
        "python3-saml",
        "jira",
        "opa-python-client",
        "streamlit",
        "pandas",
        "plotly",
        "ansible-runner",
        "boto3",
        "networkx",
        "pyhcl2",
        "questionary"
    ],

    # CLI entry point
    entry_points={
        'console_scripts': [
            'cloudcraver=main:main',  # src/main.py should define `main()`
        ],
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    python_requires='>=3.8',
)
