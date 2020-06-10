import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spotijjjy", # Replace with your own username
    version="1.0.0",
    author="Max Tarasuik",
    author_email="pip_public@tarasuik.com",
    description="Generate Spotify playlists from a few REST services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/maxtara/Spotijjjy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['spotipy'],
)