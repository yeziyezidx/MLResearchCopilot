from setuptools import setup, find_packages

setup(
    name="ml-research-copilot",
    version="0.1.0",
    description="智能研究辅助系统 - 帮助用户进行文献综合分析和研究问题解答",
    author="ML Research Team",
    author_email="research@example.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        "flask>=2.3.0",
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "sqlalchemy>=2.0.0",
        "pytest>=7.0.0",
        "python-dateutil>=2.8.0",
    ],
    entry_points={
        "console_scripts": [
            "ml-research-copilot=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
