import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rear",
    version="0.1.2",
    author="Contextualist",
    description="Remote Archiver: safely collect output files into archives on network filesystem",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Contextualist/rear",
    packages=setuptools.find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "filelock >= 3.3.2",
        "trio",
    ],
    tests_require = [
        "pytest",
        "pytest-trio",
    ],
    entry_points = {
        "console_scripts": ["rear-scavenger=rear.scavenger:main"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Trio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Archiving",
        "Topic :: System :: Distributed Computing",
        "Topic :: Utilities",
    ],
)
