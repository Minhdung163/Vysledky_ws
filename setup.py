from setuptools import setup, find_packages

setup(
    name="Vysledky_ws",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'selenium',
        'beautifulsoup4',  # Note: bs4 is a common alias for beautifulsoup4
        'requests',
        'async_lru',
        'aiohttp',
        'asyncio; python_version<"3.7"',  # asyncio is part of the standard library in Python 3.7 and later
    ],
    # Additional metadata
    author="Hieu a Dung",
    author_email="hieuhp04@gmail.com",
    description="A short description of your project",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Minhdung163/Vysledky_ws",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)