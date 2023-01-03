import setuptools
 
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
 
setuptools.setup(
    name="nonebot_plugin_l4d2_server",
    version="0.0.1", 
    author="Umamusume-Agnes-Digital", 
    author_email="Z735803792@163.com", 
    description="L4D2 server related operations",
    long_description=long_description, 
    long_description_content_type="text/markdown",
    url="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server", 
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)