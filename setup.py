from __future__ import print_function
from setuptools import setup
from setuptools.command.test import test as TestCommand
import os
import sys
from codecs import open

version = '0.0.1'

here = os.path.abspath(os.path.dirname(__file__))


with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()

with open('HISTORY.rst', 'r', 'utf-8') as f:
    history = f.read()


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(name='poller',
      version=version,
      url='https://github.com/thiezn/netMon-poller',
      author='Mathijs Mortimer',
      tests_require=['pytest', 'pytest-asyncio'],
      install_requires=[],
      cmdclass={'test': PyTest},
      description='Distributed Network Monitoring Poller',
      keywords='network monitoring latency bandwidth',
      long_description=readme + '\n\n' + history,
      include_package_data=True,
      zip_safe=False,
      platforms='any',
      test_suite='poller.test.test_poller',
      classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'Operating System :: Unix',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        ],
      extras_require={'testing': ['poller']},
      author_email='mathijs@mortimer.nl',
      packages=['poller'])
