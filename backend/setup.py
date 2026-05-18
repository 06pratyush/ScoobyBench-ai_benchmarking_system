from setuptools import setup, find_packages

setup(
    name="scoobybench",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "numpy>=1.26.0",
        "psutil>=5.9.0",
        "onnxruntime>=1.16.0",
        "pynvml>=11.5.0",
        "websockets>=12.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "scoobybench=app.main:main",
        ],
    },
)
