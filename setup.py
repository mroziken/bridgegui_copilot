from setuptools import setup
setup(
    name="Bridge GUI copilot",
    author="Michal Mrozik",
    author_email="michal.mrozik@gmail.com",
    url="https://github.com/mroziken/bridgegui_copilot",
    packages=["bridgegui"],
    entry_points={
        "gui_scripts": ["bridgegui=bridgegui.__main__:main"]
    },
    package_data={
        "bridgegui": ["images/*.png"]
    },
    install_requires=["pyzmq>=15.4","PyQt5>=5.7", "openai>=0.10.2", "python-dotenv>=0.10.3", "langchain>=0.1.0", "langchain-openai>=0.1.0"],
    test_suite="tests",
)
