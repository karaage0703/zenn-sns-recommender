from setuptools import setup, find_packages

setup(
    name="zenn_sns_recommender",
    version="0.1.0",
    description="Zenn記事推薦＆SNS投稿文生成ツール",
    author="karaage",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "gradio>=4.0.0",
        "openai>=1.0.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
