import setuptools
 
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
 
setuptools.setup(
    name="nonebot-plugin-l4d2-server",
    version="0.0.8", 
    author="Umamusume-Agnes-Digital", 
    author_email="Z735803792@163.com", 
    description="L4D2 server related operations plugin for NoneBot",
    long_description=long_description, 
    long_description_content_type="text/markdown",
    url="https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server",
    packages=["nonebot_plugin_l4d2_server"],
    project_urls={
        "Bug Tracker": "https://github.com/Umamusume-Agnes-Digital/nonebot_plugin_l4d2_server/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6,<4.0',
    install_requires=[
        "nonebot2>=2.0.0b1,<3.0.0",
        "nonebot-adapter-onebot>=2.1.0,<3.0.0",
        "requests",
        ],
)