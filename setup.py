from setuptools import setup, find_packages

setup(name='rnaseq_pipeline',
      version='2.0.0',
      description='RNA-Seq pipeline for the Pavlidis Lab',
      long_description='file: README.md',
      author='Guillaume Poirier-Morency',
      author_email='poirigui@msl.ubc.ca',
      packages=find_packages(),
      install_requires=['luigi', 'bioluigi', 'PyYAML', 'requests', 'pandas'],
      extras_require={
          'gsheet': ['google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib', 'pyxdg'],
          'webviewer': ['Flask']},
      scripts=['luigi-wrapper', 'scripts/submit-experiments-from-gsheet'])
