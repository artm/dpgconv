#!/usr/bin/env python

from distutils.core import setup

setup(name='dpgconv',
	version='10.1',
	description='Transcode video files to DPG format suitable for Nintendo DS',
	author='Anton Romanov',
	author_email='theli@ukr.net',
	url='http://theli.is-a-geek.org/blog/static/dpgconv',
	license='GNU General Public License v2.0',
    scripts=['dpgconv'],
    classifiers=['Topic :: Multimedia :: Video :: Conversion']
    )

