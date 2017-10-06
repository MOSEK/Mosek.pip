# NOTE to whoever happens to look in this file: I had to cheat a bit
# to get the installer to work with PIP. Since the 'build' action
# effectively builds both python source and binary libraries (by
# downloading and unpacking the binary distribution)

import distutils.command.build
import os
import os.path
import platform
import re
import shutil
import sys

import setuptools.command.egg_info
import setuptools.command.install
from setuptools import setup


class VersionError(Exception):
    pass


class URLError(Exception):
    pass


with open(os.path.join(os.path.dirname('__file__'), 'PKG-INFO'), 'rt') as f:
    data = f.read()
    regex = re.compile(r'^Version: (?P<version_number>(\d+\.)+(\d+\b))',
                       re.MULTILINE)
    o = regex.search(data)
    if o is not None:
        vn = o.groupdict()['version_number']
        vn = vn.split('.')
        mosekmajorver = vn[0]
        mosekminorver = vn[1]
        mosekrevision = vn[2]
        state = 'stable'
    else:
        raise VersionError('No version entry in PKG-INFO')

######################
# Platform setup
######################

libs = {
    'win64x86': {
        '7.0': [
            'mosek64_7_0.dll', 'mosekxx7_0.dll', 'mosekscopt7_0.dll',
            'libiomp5md.dll'
        ],
        '7.1': [
            'mosek64_7_1.dll', 'mosekxx7_1.dll', 'mosekscopt7_1.dll',
            'libiomp5md.dll'
        ],
        '8.0': [
            'mosek64_8_0.dll', 'mosekxx8_0.dll', 'mosekscopt8_0.dll',
            'libiomp5md.dll', 'cilkrts20.dll'
        ],
        '8.1': [
            'mosek64_8_1.dll', 'mosekxx8_1.dll', 'mosekscopt8_1.dll',
            'libiomp5md.dll', 'cilkrts20.dll'
        ],
    },
    'win34x86': {
        '7.0': [
            'mosek7_0.dll', 'mosekxx7_0.dll', 'mosekscopt7_0.dll',
            'libiomp5md.dll'
        ],
        '7.1': [
            'mosek7_1.dll', 'mosekxx7_1.dll', 'mosekscopt7_1.dll',
            'libiomp5md.dll'
        ],
        '8.0': [
            'mosek8_0.dll', 'mosekxx8_0.dll', 'mosekscopt8_0.dll',
            'libiomp5md.dll', 'cilkrts20.dll'
        ],
        '8.1': [
            'mosek8_1.dll', 'mosekxx8_1.dll', 'mosekscopt8_1.dll',
            'libiomp5md.dll', 'cilkrts20.dll'
        ],
    },
    'linux64x86': {
        '7.0': [
            'libmosek64.so.7.0', 'libmosekxx7_0.so', 'libmosekscopt7_0.so',
            'libiomp5.so'
        ],
        '7.1': [
            'libmosek64.so.7.1', 'libmosekxx7_1.so', 'libmosekscopt7_1.so',
            'libiomp5.so'
        ],
        '8.0': [
            'libmosek64.so.8.0', 'libmosekxx8_0.so', 'libmosekscopt8_0.so',
            'libiomp5.so', 'libcilkrts.so.5'
        ],
        '8.1': [
            'libmosek64.so.8.1', 'libmosekxx8_1.so', 'libmosekscopt8_1.so',
            'libiomp5.so', 'libcilkrts.so.5'
        ],
    },
    'linux32x86': {
        '7.0': [
            'libmosek.so.7.0', 'libmosekxx7_0.so', 'libmosekscopt7_0.so',
            'libiomp5.so'
        ],
        '7.1': [
            'libmosek.so.7.1', 'libmosekxx7_1.so', 'libmosekscopt7_1.so',
            'libiomp5.so'
        ],
    },
    'osx64x86': {
        '7.0': [
            'libmosek64.7.0.dylib', 'libmosekxx7_0.dylib',
            'libmosekscopt7_0.dylib', 'libiomp5.dylib'
        ],
        '7.1': [
            'libmosek64.7.1.dylib', 'libmosekxx7_1.dylib',
            'libmosekscopt7_1.dylib', 'libiomp5.dylib'
        ],
        '8.0': [
            'libmosek64.8.0.dylib', 'libmosekxx8_0.dylib',
            'libmosekscopt8_0.dylib', 'libcilkrts.5.dylib'
        ],
        '8.1': [
            'libmosek64.8.1.dylib', 'libmosekxx8.1.dylib',
            'libmosekscopt8.1.dylib', 'libcilkrts.5.dylib'
        ],
    },
}

licensepdfd = {
    '7.0': ['mosek', '7', 'license.pdf'],
    '7.1': ['mosek', '7', 'license.pdf'],
    '8.0': ['mosek', '8', 'doc', 'licensing.pdf'],
    '8.1': ['mosek', '8', 'doc', 'licensing.pdf'],
}

pkgnames = {
    'win64x86': 'mosektoolswin64x86.zip',
    'win34x86': 'mosektoolswin32x86.zip',
    'linux64x86': 'mosektoolslinux64x86.tar.bz2',
    'linux32x86': 'mosektoolslinux32x86.tar.bz2',
    'osx64x86': 'mosektoolsosx64x86.tar.bz2'
}

mskverkey = '{0}.{1}'.format(mosekmajorver, mosekminorver)

major, minor, _, _, _ = sys.version_info

is_64bits = platform.architecture()[0] == '64bit'
pf = platform.system()

if pf == 'Windows':
    if is_64bits:
        pfname = "win64x86"
        pkgname = 'mosektoolswin64x86.zip'
    else:
        pfname = "win32x86"
        pkgname = 'mosektoolswin32x86.zip'
elif pf == 'Linux':
    if is_64bits:
        pfname = "linux64x86"
    else:
        pfname = "linux32x86"
        pkgname = 'mosektoolslinux32x86.tar.bz2'
elif pf == 'Darwin':
    pfname = "osx64x86"
    pkgname = 'mosektoolsosx64x86.tar.bz2'
else:
    raise VersionError("Unsupported platform {0}".format(pf))

pkgname = pkgnames[pfname]
moseklibs = libs[pfname][mskverkey]
moseklibs = set(moseklibs)

pkgpath = '/{state}/{0}.{1}.0.{2}/{3}'.format(
    mosekmajorver, mosekminorver, mosekrevision, pkgname, state=state)
unpackdir = os.path.abspath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src'))
distroplatformpfx = 'mosek/{0}/tools/platform/{1}'.format(mosekmajorver,
                                                          pfname)

######################
# Get mosek package
######################


def _pre_install():
    """
    Fetch MOSEK distribution and unpack the python module structure
    """
    # Download the newest distro
    pkgfilename = os.path.join(unpackdir, pkgname)

        
    
    if not os.path.exists(pkgfilename):
        url = "http://download.mosek.com" + pkgpath

        if sys.version_info.major == 2:
            import urllib
            urllib.urlretrieve(url, pkgfilename)
        elif sys.version_info.major == 3:
            import urllib.request
            urllib.request.urlretrieve(url, pkgfilename)

    licensepdf = '/'.join(licensepdfd[mskverkey])
    pypfx = '{0}/python/{1}/mosek'.format(distroplatformpfx, major)

    if os.path.splitext(pkgname)[-1] == '.zip':
        import zipfile

        with zipfile.ZipFile(pkgfilename) as zf:
            for tmem in zf.infolist():
                if tmem.filename.startswith(pypfx):
                    zf.extract(tmem,
                               os.path.dirname(tmem.filename[len(pypfx):]))
                elif os.path.basename(tmem.filename) in moseklibs:
                    zf.extract(tmem, unpackdir)
                elif tmem.filename == licensepdf:
                    zf.extract(tmem, unpackdir)
    else:
        import tarfile

        with tarfile.open(pkgfilename) as tf:
            for tmem in tf:
                if not tmem.isfile():
                    continue
                basename = os.path.basename(tmem.name)
                if (tmem.name == licensepdf) or (tmem.name.startswith(pypfx)
                                                 ) or (basename in moseklibs):
                    tf.extract(tmem, unpackdir)


def _post_install(sitedir):
    """
    Unpack and install the necessary binary libraries and the
    license. Create the mosekorigin module.
    """

    # Copy python modules
    try:
        shutil.rmtree(os.path.join(sitedir, 'mosek'))
    except:
        pass

    libsrcdir = os.path.join(unpackdir, 'mosek', mosekmajorver, 'tools',
                             'platform', pfname, 'bin')

    shutil.copytree(
        os.path.join('src', 'mosek', mosekmajorver, 'tools', 'platform',
                     pfname, 'python', str(major), 'mosek'),
        os.path.join(sitedir, 'mosek'))

    tgtpath = os.path.join(sitedir, 'mosek')
    #try: os.makedirs(tgtpath)
    #except OSError: pass

    for l in moseklibs:
        shutil.copyfile(os.path.join(libsrcdir, l), os.path.join(tgtpath, l))

    with open(os.path.join(sitedir, 'mosek', 'mosekorigin.py'), 'wt') as f:
        f.write('import os\n')
        f.write('__mosekinstpath__ = os.path.dirname(__file__)\n')
        f.write('\n')

    shutil.copy(
        os.path.join('src', *licensepdfd[mskverkey]),
        os.path.join(sitedir, 'mosek'))

    print("""
*** MOSEK for Python ***
Please read through the MOSEK software license before using MOSEK:
     {0}
To use MOSEK for optimization a license file is required. Free
academic licenses, commercial trial licenses and full licenses can be
obtained at http://mosek.com.
""".format(os.path.join(sitedir, *licensepdfd[mskverkey])))


class build(distutils.command.build.build):
    def run(self):
        self.execute(_pre_install, (), msg="Fetch and unpack MOSEK distro")
        distutils.command.build.build.run(self)


class install(setuptools.command.install.install):
    def run(self):
        setuptools.command.install.install.run(self)
        self.execute(
            _post_install, (self.install_lib, ),
            msg="Install binary libraries")


packages = ['mosek', 'mosek.fusion']

setup(
    name='Mosek',
    cmdclass={'build': build,
              'install': install},
    version='{0}.{1}.{2}'.format(mosekmajorver, mosekminorver, mosekrevision),
    #packages     = packages,
    #package_dir  = { 'mosek'        : os.path.join('src','mosek',mosekmajorver,'tools','platform',pfname,'python',str(major),'mosek') },
    install_requires=['numpy>=1.4'],
    author='Mosek ApS',
    author_email="support@mosek.com",
    description='Mosek/Python APIs',
    long_description='Interface for MOSEK',
    license="See %s in the MOSEK distribution" % licensepdfd[mskverkey][-1],
    url='http://www.mosek.com', )
