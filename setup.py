from setuptools import setup

setup(
    name='pythonaudio',
    version='0.1.0',
    description='Play and record audio without resorting to CPython extensions',
    license='BSD 3-clause',
    packages=['pythonaudio'],
    package_data={'pythonaudio': ['*.py.h']}
)
