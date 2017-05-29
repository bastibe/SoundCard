from setuptools import setup

setup(
    name='pythonaudio',
    version='0.1.0',
    description='Play and record audio without resorting to CPython extensions',
    author='Bastian Bechtold',
    url='https://github.com/bastibe/Python-Audio',
    license='BSD 3-clause',
    packages=['pythonaudio'],
    package_data={'pythonaudio': ['*.py.h']},
    install_requires=['numpy', 'cffi']
)
