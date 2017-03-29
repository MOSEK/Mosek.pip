# NOTE to whoever happens to look in this file: I had to cheat a bit
# to get the installer to work with PIP. Since the 'build' action
# effectively builds both python source and binary libraries (by
# downloading and unpacking the binary distribution)

import setuptools.command.install
import setuptools.command.egg_info
import distutils.command.build
from   setuptools import setup
import platform,sys
import os,os.path
import shutil
import re

class VersionError(Exception): pass
class URLError(Exception): pass

with open(os.path.join(os.path.dirname('__file__'),'PKG-INFO'),'rt') as f:
    data = f.read()
    regex = re.compile(r'^Version:\s*([0-9]+)\.([0-9]+)\.(?:([ab])?([0-9]+))',re.MULTILINE)
    o = regex.search(data)
    if o is not None:
        mosekmajorver = o.group(1)
        mosekminorver = o.group(2)
        letter        = o.group(3)
        mosekrevision = o.group(4)
        state         = 'stable'

        if letter is not None:
            if   letter == 'a':
                state = 'alpha'
            elif letter == 'b':
                state = 'beta'
    else:
        raise VersionError('No version entry in PKG-INFO')


######################
# Platform setup
######################

libs = { 
    'win64x86' : {
        '7.0' : [ 'mosek64_7_0.dll','mosekxx7_0.dll', 'mosekscopt7_0.dll', 'libiomp5md.dll' ],
        '7.1' : [ 'mosek64_7_1.dll','mosekxx7_1.dll', 'mosekscopt7_1.dll', 'libiomp5md.dll' ],
        '8.0' : [ 'mosek64_8_0.dll','mosekxx8_0.dll', 'mosekscopt8_0.dll', 'libiomp5md.dll','cilkrts20.dll' ] },
    'win34x86' : {
        '7.0' : [ 'mosek7_0.dll','mosekxx7_0.dll', 'mosekscopt7_0.dll', 'libiomp5md.dll' ],
        '7.1' : [ 'mosek7_1.dll','mosekxx7_1.dll', 'mosekscopt7_1.dll', 'libiomp5md.dll' ],
        '8.0' : [ 'mosek8_0.dll','mosekxx8_0.dll', 'mosekscopt8_0.dll', 'libiomp5md.dll','cilkrts20.dll' ], },
    'linux64x86' : {
        '7.0' : [ 'libmosek64.so.7.0', 'libmosekxx7_0.so', 'libmosekscopt7_0.so','libiomp5.so' ],
        '7.1' : [ 'libmosek64.so.7.1', 'libmosekxx7_1.so', 'libmosekscopt7_1.so','libiomp5.so' ],
        '8.0' : [ 'libmosek64.so.8.0', 'libmosekxx8_0.so', 'libmosekscopt8_0.so','libiomp5.so','libcilkrts.so.5' ] },
    'linux32x86' : {
        '7.0' : [ 'libmosek.so.7.0', 'libmosekxx7_0.so', 'libmosekscopt7_0.so','libiomp5.so' ],
        '7.1' : [ 'libmosek.so.7.1', 'libmosekxx7_1.so', 'libmosekscopt7_1.so','libiomp5.so' ] },
    'osx64x86' : {
        '7.0' : [ 'libmosek64.7.0.dylib', 'libmosekxx7_0.dylib', 'libmosekscopt7_0.dylib','libiomp5.dylib' ],
        '7.1' : [ 'libmosek64.7.1.dylib', 'libmosekxx7_1.dylib', 'libmosekscopt7_1.dylib','libiomp5.dylib' ],
        '8.0' : [ 'libmosek64.8.0.dylib', 'libmosekxx8_0.dylib', 'libmosekscopt8_0.dylib','libcilkrts.5.dylib' ] },
}

licensepdfd = {
    '7.0' : ['mosek','7','license.pdf'],
    '7.1' : ['mosek','7','license.pdf'],
    '8.0' : ['mosek','8','doc','licensing.pdf'],
}


pkgnames = {
    'win64x86'   : 'mosektoolswin64x86.zip',
    'win34x86'   : 'mosektoolswin32x86.zip',
    'linux64x86' : 'mosektoolslinux64x86.tar.bz2',
    'linux32x86' : 'mosektoolslinux32x86.tar.bz2',
    'osx64x86'   : 'mosektoolsosx64x86.tar.bz2' }

mskverkey = '{0}.{1}'.format(mosekmajorver,mosekminorver)

major,minor,_,_,_ = sys.version_info
if (major != 2 or minor < 5) and (major != 3 or minor < 3):
    print("Python 2.5+ required, got %d.%d" % (major,minor))

import ctypes
is_64bits = 8 == ctypes.sizeof(ctypes.c_void_p) # figure out if python is 32bit or 64bit
pf        = platform.system()

if   pf == 'Windows':
    if is_64bits:
        pfname = "win64x86"
        pkgname = 'mosektoolswin64x86.zip'
    else:
        pfname = "win32x86"
        pkgname = 'mosektoolswin32x86.zip'
    dldir = os.environ.get('TEMP')
elif pf == 'Linux':
    if is_64bits:
        pfname = "linux64x86"
    else:
        pfname = "linux32x86"
        pkgname = 'mosektoolslinux32x86.tar.bz2'
    dldir = '{0}/Downloads'.format(os.environ['HOME']) # appears to be standart
elif pf == 'Darwin':
    pfname = "osx64x86"
    pkgname = 'mosektoolsosx64x86.tar.bz2'
    dldir = '{0}/Downloads'.format(os.environ['HOME'])
else:
    raise VersionError("Unsupported platform {0}".format(pf))

pkgname = pkgnames[pfname]
moseklibs = libs[pfname][mskverkey]

if dldir is not None and not os.path.isdir(dldir):
    dldir = None

pkgpath     = '/{state}/{0}.{1}.0.{2}/{3}'.format(mosekmajorver,mosekminorver,mosekrevision,pkgname,state=state)
unpackdir   = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)),'src'))
distroplatformpfx = 'mosek/{0}/tools/platform/{1}'.format(mosekmajorver,pfname)

######################
# Get mosek package
######################

def _pre_install():
    """
    Fetch MOSEK distribution and unpack the python module structure
    """
    # Download the newest distro
    if dldir is not None:
        pkgfilename = os.path.join(dldir,'Mosek-{0}.{1}.{2}-'.format(mosekmajorver,mosekminorver,mosekrevision)+pkgname)
    else: # download to local directory
        pkgfilename = os.path.join(unpackdir,pkgname)

        
    
    if not os.path.exists(pkgfilename):
        url = "http://download.mosek.com" + pkgpath

        try:
            # python 2
            import httplib
            c = httplib.HTTPConnection('download.mosek.com')
            try:
                c.request('GET',pkgpath)
                r = c.getresponse()
                if r.status != 200:
                    raise URLError("Failed to fetch MOSEK package '{0}'. Response {1} ({2})".format(url,r.status,r.reason))
                with open(pkgfilename,"wb") as f:
                    shutil.copyfileobj(r,f)
            finally:
                c.close()

        except ImportError:
            # python 3
            import urllib.request
            urllib.request.urlretrieve(url, pkgfilename)


    licensepdf = '/'.join(licensepdfd[mskverkey])
    pypfx = '{0}/python/{1}/mosek'.format(distroplatformpfx,major)

    if os.path.splitext(pkgname)[-1] == '.zip':
        import zipfile
        with zipfile.ZipFile(pkgfilename) as zf:
            for tmem in zf.infolist():
                if tmem.filename.startswith(pypfx):
                    zf.extract(tmem,os.path.dirname(tmem.filename[len(pypfx):]))
                elif os.path.basename(tmem.filename) in moseklibs:
                    zf.extract(tmem,unpackdir)
                elif tmem.filename == licensepdf:
                    zf.extract(tmem,unpackdir)
    else:
        import tarfile

        with tarfile.open(pkgfilename) as tf:
            for tmem in tf:
                if (tmem.isfile() and (tmem.name.startswith(pypfx))) or \
                   os.path.basename(tmem.name) in moseklibs or \
                   tmem.name == licensepdf:
                    tf.extract(tmem,unpackdir)

def _post_install(sitedir):
    """
    Unpack and install the necessary binary libraries and the
    license. Create the mosekorigin module.
    """

    # Copy python modules
    try: shutil.rmtree(os.path.join(sitedir,'mosek'))
    except: pass

    libsrcdir = os.path.join(unpackdir,'mosek',mosekmajorver,'tools','platform',pfname,'bin')

    shutil.copytree(os.path.join('src','mosek',mosekmajorver,'tools','platform',pfname,'python',str(major),'mosek'),
                    os.path.join(sitedir,'mosek'))

    tgtpath = os.path.join(sitedir,'mosek')
    #try: os.makedirs(tgtpath)
    #except OSError: pass

    for l in moseklibs:
        shutil.copyfile(os.path.join(libsrcdir,l),os.path.join(tgtpath,l))

    with open(os.path.join(sitedir,'mosek','mosekorigin.py'),'wt') as f:
        f.write('__mosekinstpath__ = """{0}"""\n'.format(os.path.join(sitedir,'mosek')))
    shutil.copy(os.path.join('src',*licensepdfd[mskverkey]),
                os.path.join(sitedir,'mosek'))
    print("""
*** MOSEK for Python ***
Please read through the MOSEK software license before using MOSEK:
     {0}
To use MOSEK for optimization a license file is required. Free
academic licenses, commercial trial licenses and full licenses can be
obtained at http://mosek.com.
""".format(os.path.join(sitedir,*licensepdfd[mskverkey])))

class build(distutils.command.build.build):
    def run(self):
        self.execute(_pre_install,(), msg="Fetch and unpack MOSEK distro")
        distutils.command.build.build.run(self)

class install(setuptools.command.install.install):
    def run(self):
        setuptools.command.install.install.run(self)
        self.execute(_post_install,
                     (self.install_lib,),
                     msg="Install binary libraries")

packages = [ 'mosek','mosek.fusion' ]


setup( name='Mosek',
       cmdclass     = { 'build'   : build,
                        'install' : install},
       version      = '{0}.{1}.{2}'.format(mosekmajorver,mosekminorver,mosekrevision),
       #packages     = packages,
       #package_dir  = { 'mosek'        : os.path.join('src','mosek',mosekmajorver,'tools','platform',pfname,'python',str(major),'mosek') },
       install_requires = ['numpy>=1.4' ],
       author       = 'Mosek ApS',
       author_email = "support@mosek.com",
       description  = 'Mosek/Python APIs',
       long_description = 'Interface for MOSEK',
       license      = "See %s in the MOSEK distribution" % licensepdfd[mskverkey][-1],
       url          = 'http://www.mosek.com',
       )
