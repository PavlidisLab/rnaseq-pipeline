from setuptools import setup, find_packages

setup(name='rnaseq_pipeline',
      version='2.1.1',
      description='RNA-Seq pipeline for the Pavlidis Lab',
      license='Public Domain',
      long_description='file: README.md',
      author='Guillaume Poirier-Morency',
      author_email='poirigui@msl.ubc.ca',
      classifiers=['License :: Public Domain'],
      packages=find_packages(),
      install_requires=['luigi', 'bioluigi', 'PyYAML', 'requests', 'pandas==1.1.4'],
      extras_require={
          'gsheet': ['google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib', 'pyxdg'],
          'webviewer': ['Flask']},
      scripts=['luigi-wrapper', 'scripts/submit-experiments-from-gsheet'])
