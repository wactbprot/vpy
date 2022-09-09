"""setup.py based on
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='vpy',
      version='0.2.0',
      description='Analysis of measurement results stored in CouchDB documents.',
      long_description=long_description,
      url='https://gitlab1.ptb.de/vaclab/vpy',
      author='Thomas Bock, Matthias Bernien',
      author_email='thomas.bock@ptb.de, matthias.bernien@ptb.de',
      license='MIT',
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: vaclab team',
                   'License :: OSI Approved :: MIT License',
                   'Programming Language :: Python :: 3.8',
                   'Programming Language :: Python :: 3.9'],
      keywords='Analysis, Uncertainty, Vacuum, Pressure',
      packages=find_packages(exclude=['docs',
                                      'tests',
                                      'test_doc',
                                      'htmlcov']),
      extras_require={'dev': ['sphinx',
                              'sphinx_rtd_theme',
                              'autopep8',
                              'PyUnitReport']})
