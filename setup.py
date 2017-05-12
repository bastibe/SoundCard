from setuptools import setup

if sys.platform == 'darwin':
    dependencies = ['numpy', 'cffi', 'resampy']
else:
    dependencies = ['numpy', 'cffi']

setup(
    name='pythonaudio',
    version='0.1.0',
    description='Play and record audio without resorting to CPython extensions',
    license='BSD 3-clause',
    packages=['pythonaudio'],
    package_data={'pythonaudio': ['*.py.h']},
    install_requires=dependencies
)
