# -*- coding: utf-8 -*-

from setuptools import setup

setup(
        name='director',
        version='0.0.1',
        packages=['director'],
        install_requires=['Flask >= 0.10.1', 'Flask-SQLAlchemy >= 2.0',
                          'SQLAlchemy >= 0.9.9', 'requests >= 2.12.1'],
        entry_points={'console_scripts': ['director=director:main']},
        author='Tobias Schäfer',
        author_email='director@blackoxorg',
        url='https://github.com/tschaefer/director',
        description="Director. Entertainment directed by you.",
        license='BSD',
        include_package_data=True,
        zip_safe=False
)
