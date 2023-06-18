import pathlib
from setuptools import setup
from tes_reader import __version__ as version

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()

setup(
    name="elder-scrolls",
    version=version,
    description="A module to read and edit TES (The Elder Scrolls) files.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/sinan-ozel/elder-scrolls",
    author="Sinan Ozel",
    license="Creative Commons Zero v1.0 Universal",
    packages=['elder_scrolls'],
)