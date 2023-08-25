#setup.py
from setuptools import setup, find_packages

setup(
    name='cmd-gpt',
    packages=[package for package in find_packages() if package.startswith("cmd_gpt")],
    version='0.0.1',
    description='Command line deployment agent using LLM',
    url='',
    author='Jieyu Lin (Eric)',
    install_requires=[
        '',
    ],  
    extras_require={
        'test': ['pytest']
    }
)