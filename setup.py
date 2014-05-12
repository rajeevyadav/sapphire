from setuptools import setup, find_packages


setup(name='hisparc-sapphire',
      version='0.9.10',
      packages=find_packages(),
      url='http://github.com/hisparc/sapphire/',
      bugtrack_url='http://github.com/HiSPARC/sapphire/issues',
      license='GPLv3',
      author='David Fokkema',
      author_email='davidf@nikhef.nl',
      maintainer='HiSPARC',
      maintainer_email='beheer@hisparc.nl',
      description='A framework for the HiSPARC experiment',
      long_description=open('README.rst').read(),
      keywords=['HiSPARC', 'Nikhef', 'cosmic rays'],
      classifiers=['Intended Audience :: Science/Research',
                   'Intended Audience :: Education',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Education',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'],
      scripts=['sapphire/corsika/store_corsika_data',
               'sapphire/corsika/qsub_corsika',
               'sapphire/corsika/qsub_store_corsika_data'],
      package_data={'sapphire': ['corsika/LICENSE',
                                 'tests/analysis/DIR-testdata.h5',
                                 'tests/corsika/DAT000000',
                                 'tests/simulations/testdata.h5']},
      install_requires=['numpy', 'scipy', 'tables>=3.0.0', 'progressbar>=2.3',
                        'mock'],
      test_suite="sapphire.tests",)
