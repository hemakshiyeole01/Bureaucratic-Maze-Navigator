from setuptools import setup, find_packages

setup(
    name="bureaucratic-maze",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.111.0",
        "uvicorn[standard]>=0.30.1",
        "pydantic>=2.7.1",
        "httpx>=0.27.0",
        "openai>=1.30.1",
        "pyyaml>=6.0.1",
        "openenv-core>=0.2.0",
    ],
    python_requires=">=3.10",
)
