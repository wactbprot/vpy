"""setup.py based on
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vpy',
    version='0.1.0',
    description='Analysis of measurement results stored in couchdb documents',
    long_description=long_description,
    url='https://github.com/wactbprot/vpy',
    author='Wact B. Prot',
    author_email='wactbprot@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: vaclab team',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='Analysis, Uncertainty, Measurands, Vacuum, Pressure',
    packages=find_packages(exclude=['docs',
                                    'tests',
                                    'test_doc',
                                    ]),
    install_requires=['couchdb',
                      'coloredlogs',
                      'numpy',
                      'scipy',
                      'sympy',
                      'matplotlib',
                      'sphinx',
                      'sphinx_rtd_theme',
                      ],
    extras_require={
        'dev': ['sphinx',
                'sphinx_rtd_theme',
                'autopep8',
                ],
    },
    package_data={
        'sample': ['test_doc'],
    },
    # entry_points={
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
)
