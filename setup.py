from setuptools import setup, find_packages

setup(name='rnaseq_pipeline',
      version='2.1.12',
      description='RNA-Seq pipeline for the Pavlidis Lab',
      license='Public Domain',
      long_description='file: README.md',
      long_description_content_type='text/markdown',
      url='https://github.com/pavlidisLab/rnaseq-pipeline',
      author='Guillaume Poirier-Morency',
      author_email='poirigui@msl.ubc.ca',
      classifiers=['License :: Public Domain'],
      packages=find_packages(),
      include_package_data=True,
      install_requires=['luigi', 'python-daemon<3.0.0', 'bioluigi>=0.2.1', 'requests', 'pandas'],
      extras_require={
          'gsheet': ['google-api-python-client', 'google-auth-httplib2', 'google-auth-oauthlib', 'pyxdg'],
          'webviewer': ['Flask', 'gunicorn']},
      scripts=['scripts/luigi-wrapper', 'scripts/submit-experiments-from-gsheet', 'scripts/submit-experiment'])
