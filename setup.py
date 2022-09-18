import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# get version from __init__.py
with open("raw2fits/__init__.py", "r") as fh:
    for line in fh:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break

setuptools.setup(
    name="raw2fits",
    version=version,
    author="Jamie Chang",
    author_email="jamiechang917@gmail.com",
    description="Convert raw images to fits",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jamiechang917/raw2fits",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    python_requires='>=3.6',
    license="MIT",
)