from setuptools import setup, find_packages

setup(name='rnaseq_pipeline',
      packages=find_packages(),
      install_requires=['luigi', 'bioluigi', 'PyYAML', 'requests', 'pandas', 'Flask'])
