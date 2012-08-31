#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

###################### DO NOT TOUCH THIS (HEAD TO THE SECOND PART) ######################

import os
import sys

try:
    import DistUtilsExtra.auto
except ImportError:
    print >> sys.stderr, 'To build uberwriter you need https://launchpad.net/python-distutils-extra'
    sys.exit(1)
assert DistUtilsExtra.auto.__version__ >= '2.18', 'needs DistUtilsExtra.auto >= 2.18'

def update_config(values = {}):

    oldvalues = {}
    try:
        fin = file('uberwriter_lib/uberwriterconfig.py', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:
            fields = line.split(' = ') # Separate variable from value
            if fields[0] in values:
                oldvalues[fields[0]] = fields[1].strip()
                line = "%s = %s\n" % (fields[0], values[fields[0]])
            fout.write(line)

        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find uberwriter_lib/uberwriterconfig.py")
        sys.exit(1)
    return oldvalues


def update_desktop_file(datadir):

    try:
        fin = file('uberwriter.desktop.in', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:            
            if 'Icon=' in line:
                line = "Icon=%s\n" % (datadir + 'media/uberwriter.svg')
            fout.write(line)
        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find uberwriter.desktop.in")
        sys.exit(1)


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        values = {'__uberwriter_data_directory__': "'%s'" % (self.prefix + '/share/uberwriter/'),
                  '__version__': "'%s'" % self.distribution.get_version()}
        previous_values = update_config(values)
        update_desktop_file(self.prefix + '/share/uberwriter/')
        DistUtilsExtra.auto.install_auto.run(self)
        update_config(previous_values)


        
##################################################################################
###################### YOU SHOULD MODIFY ONLY WHAT IS BELOW ######################
##################################################################################

DistUtilsExtra.auto.setup(
    name='uberwriter',
    version='0.1',
    license='GPL-3',
    author='Wolf Vollprecht',
    author_email='w.vollprecht@gmail.com',
    description='A beautiful, simple and distraction free markdown editor.',
    long_description="UberWriter, beautiful distraction free writing \
 With UberWriter you get only one thing: An empty textbox, that is to \
 fill with your ideas. There are no settings, you don't have to choose a \
 font, it is only for writing.You can use markdown for all your markup \
 needs. PDF, RTF and HTML are generated with pandoc. For PDF generation it \
 is also required that you choose to install the texlive-luatex package.",
    url='https://launchpad.com/uberwriter',
    cmdclass={'install': InstallAndUpdateDataDirectory},
    package_dir = {
        'gtkspellcheck': 'uberwriter_lib/thirdparty/gtkspellcheck',
        'pylocales': 'uberwriter_lib/thirdparty/pylocales'
    },
    packages=[
        "gtkspellcheck",
        "pylocales"
    ],
    package_data={'pylocales' : ['locales.db']}
    )