from setuptools import setup, find_packages

setup(name='rnaseq_pipeline',
      version='1.3.2',
      description='RNA-Seq pipeline for the Pavlidis Lab',
      long_description='file: README.md',
      author='Guillaume Poirier-Morency',
      author_email='poirigui@msl.ubc.ca',
      packages=find_packages(),
      install_requires=['luigi', 'bioluigi', 'PyYAML', 'requests', 'pandas', 'Flask'])
