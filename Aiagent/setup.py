from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    install_requires = [line.strip() for line in f.readlines()]

setup(
    name="dev_assistant",
    version="1.0",
    packages=find_packages(),
    install_requires=install_requires,
    author="Your Name",
    author_email="your@email.com",
    description="AI-powered developer assistant",
)
