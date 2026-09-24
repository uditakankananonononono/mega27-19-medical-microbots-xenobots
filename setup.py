from setuptools import setup, find_packages
setup(name="microbots", version="0.1.0",
      description="MEGA27-19 medical microbots/xenobots computational design + control",
      packages=find_packages(include=["microbots*"]), python_requires=">=3.9", entry_points={"console_scripts": ["microbot-design=microbots.cli:main"]})
