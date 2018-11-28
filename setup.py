from setuptools import setup

setup(
    name='SoundCard',
    version='0.2.0',
    description='Play and record audio without resorting to CPython extensions',
    author='Bastian Bechtold',
    url='https://github.com/bastibe/SoundCard',
    license='BSD 3-clause',
    packages=['soundcard'],
    package_data={'soundcard': ['*.py.h']},
    install_requires=['numpy', 'cffi'],
    python_requires='>=3.6'
)
