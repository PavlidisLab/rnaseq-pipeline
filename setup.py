from setuptools import setup

setup(name='rnaseq_pipeline',
      packages=['rnaseq_pipeline'],
      package_dir={'rnaseq_pipeline': 'scheduler'},
      install_requires=['luigi', 'bioluigi', 'PyYAML', 'requests', 'pandas'],
      dependency_links=['git+https://github.com/PavlidisLab/bioluigi.git#egg=bioluigi-0.0.0'])
