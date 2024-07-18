from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="microgrid-backend",
    description="Backend for Microgrid Planner",
    packages=find_packages(),
    install_requires=requirements
)
