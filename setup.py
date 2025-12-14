"""Setup script for Auto Subtitle Generator"""
from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="autosub-generator",
    version="2.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Automatically generate and translate video subtitles using Whisper AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aryadinata07/autoSubtitle",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "autosub=generate_subtitle:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [".env.example"],
    },
)
