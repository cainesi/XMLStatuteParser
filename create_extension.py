#$Id$
#$Revision$
#$Date$

from distutils.core import setup, Extension
import platform, sys

#can check sys.prefix to see where modules are being installed
#run this script with parameter "build" to test build
#run this script with parameter "install" to install the module

#setup.py file for the monte carlo tax basis optimizer


module1 = Extension('lineparse',
                    define_macros = [('PYTHON_EXTENSION', '1')], #this sets a flag on the compiler to include the python module specific code
                    #libraries = libs,
                    #include_dirs = ['/usr/local/include'],
                    #library_dirs = ['/usr/local/lib'],
                    extra_compile_args = ["-O3","-Wno-strict-prototypes"],
#                    extra_compile_args = ["-O3","-Wno-missing-prototypes"],
                    sources = ['lineparse.c'])

setup (name = 'lineparse',
       version = '1.0',
       description = 'This package contains one module for doing Monte Carlo optimizations of sets of income tax rates.',
#       author = 'Ian Caines',
#       author_email = 'ian.caines@gmail.com',
#       url = 'None',
#       long_description = '''
#Placeholder.
#''',
       ext_modules = [module1])
