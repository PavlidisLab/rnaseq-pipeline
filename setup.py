from setuptools import setup, find_packages

setup(name='rnaseq_pipeline',
      packages=find_packages(),
      install_requires=['luigi', 'bioluigi', 'PyYAML', 'requests', 'pandas', 'multiqc'],
      dependency_links=['git+https://github.com/PavlidisLab/bioluigi.git#egg=bioluigi-0.0.0'])
