from setuptools import setup, find_packages

setup(
    name="cruxrec",
    version="0.1.0",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(),
    install_requires=[
        "certifi",
        "charset-normalizer",
        "idna",
        "PyYAML",
        "requests",
        "urllib3",
        "yt-dlp",
    ],
    entry_points={
        "console_scripts": [
            "cruxrec=cruxrec.cli:main",
        ]
    },
    author="Artyom Shandrkov",
    author_email="artyom.shandrakov@gmail.com",
    description="A command-line tool to summarize YouTube videos using AI.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AShandrakov/CruxRec",
    python_requires=">=3.7",
)
