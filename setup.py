from distutils.core import setup

setup(name="vmo",
      packages = ['vmo','vmo.VMO'],
      version="0.2",
      description="vmo - Variable Markov Oracle in Python",
      author="Cheng-i Wang",
      author_email='chw160@ucsd.edu',
      url='https://github.com/wangsix/vmo',
      long_description = 'vmo is a Python library for time series and symbolic sequence analysis/synthesis in the family of software built around the Factor Oracle and Variable Markov Oracle algorithms. One of the main innovations in vmo is using functions related to Information Dynamics to determine oracle structure and query-matching algorithms.',
      )