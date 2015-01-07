import platform,sys,re
import os,os.path
import httplib
import types
import shutil
import subprocess

class VersionError(Exception): pass
class URLError(Exception): pass

mosekver = '7'

######################
# Platform setup
######################

major,minor,_,_,_ = sys.version_info
if (major != 2 or minor < 5) and major != 3:
    print("Python 2.5+ required, got %d.%d" % (major,minor))

is_64bits = sys.maxsize > 2**32
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
        pkgname = 'mosektoolslinux64x86.tar.bz2'
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

if dldir is not None and not os.path.isdir(dldir):
    dldir = None

pkgpath     = '/stable/{0}/{1}'.format(mosekver,pkgname)
unpackdir   = os.path.abspath(os.path.dirname(__file__))


######################
# Get mosek package
######################

c = httplib.HTTPConnection('download.mosek.com')
try:
    url = "http://download.mosek.com"+pkgpath

    if dldir is not None:    
        c.request('GET',pkgpath+'.sha512')
        r = c.getresponse()
        if r.status != 200:
            raise URLError("Failed to fetch MOSEK package '{0}.sha512'. Response {1} ({2})".format(url,r.status,r.reason))    
        sha512 = r.read()[:128]
                
        pkgfilename = os.path.join(dldir,sha512+'_'+pkgname)
        if not os.path.exists(pkgfilename):
            c.request('GET',pkgpath)
            r = c.getresponse()
            if r.status != 200:
                raise(URLError("Failed to fetch MOSEK package '{0}'. Response {1} ({2})".format(url,r.status,r.reason)))
            print("Fetching {0} -> {1}".format(url,pkgfilename))
            with open(pkgfilename,"wb") as f:
                shutil.copyfileobj(r,f)
            print("OK")
        else:
            print("Not redownloading. Use {0}".format(pkgfilename))
    else: # download to local directory
        pkgfilename = os.path.join(unpackdir,pkgname)
        if not os.path.isfile(pkgfilename):
            c.request('GET',pkgpath)
            r = c.getresponse()
            if r.status != 200:
                raise URLError("Failed to fetch MOSEK package '{0}'. Response {1} ({2})".format(url,r.status,r.reason))    
            print("Fetching {0} -> {1} ".format(url,pkgfilename))
            with open(pkgfilename,"wb") as f:
                shutil.copyfileobj(r,f)
            print("OK")
finally:
    c.close()

######################
# Unpack Mosek package
######################

def getMosekVersion(tgtpath):
    with open(os.path.join(tgtpath,'mosek',mosekver,'tools','platform',pfname,'h','mosek.h')) as f:
        mosekh = f.read()
    major    = None
    minor    = None
    build    = None
    revision = None
    for o in re.finditer(r'#define MSK_VERSION_(MAJOR|MINOR|BUILD|REVISION)\s+([0-9]+)',mosekh):
        if   o.group(1) == 'MAJOR':    major = int(o.group(2))
        elif o.group(1) == 'MINOR':    minor = int(o.group(2))
        elif o.group(1) == 'BUILD':    build = int(o.group(2))
        elif o.group(1) == 'REVISION': revision = int(o.group(2))
    assert major is not None and minor is not None and build is not None and revision is not None
                                                    
    return major,minor,build,revision


# NOTE: It appears that the setup.py script is loaded twice during
# setup. This means that downloading and unpacking may already have
# happened one: If we see that the 'platform' directory has been
# created, we skip all the unpacking steps.

pfx = 'mosek/{0}/tools/platform/{1}/'.format(mosekver,pfname)
tgtpath = os.path.join(unpackdir,"platform")
if not os.path.isdir(tgtpath):
    try: os.makedirs(tgtpath)
    except OSError: pass

    print("Unpacking...")
    if os.path.splitext(pkgname)[-1] == '.zip':
        import zipfile
        with zipfile.ZipFile(pkgfilename) as zf:
            for tmem in zf.infolist():
                if tmem.filename.startswith(pfx) or tmem.filename == 'mosek/{0}/license.pdf'.format(mosekver):
                    zf.extract(tmem,tgtpath)
    else:    
        import tarfile

        with tarfile.open(pkgfilename) as tf:
            for tmem in tf:            
                if tmem.isfile() and (tmem.name.startswith(pfx) or tmem.name == 'mosek/{0}/license.pdf'.format(mosekver)):
                    tf.extract(tmem,tgtpath)

    if not os.path.isdir(os.path.join(unpackdir,'python')):
        shutil.move(os.path.join(tgtpath,'mosek',mosekver,'tools','platform',pfname,'python',str(major),'mosek'),unpackdir)
    print("OK")


    ######################
    # Figure out version info and lib names
    ######################

    mskmajorver, mskminorver,_,_ = getMosekVersion(tgtpath)

    if   pf == 'Windows':
        if is_64bits:
            moseklibs = [ 'mosek64_{0}_{1}.dll'.format(mskmajorver,mskminorver), 
                          'mosekxx{0}_{1}.dll'.format(mskmajorver,mskminorver), 
                          'libiomp5md.dll',
                          'mosekscopt{0}_{1}.dll'.format(mskmajorver,mskminorver) ]
        else:
            moseklibs = [ 'mosek{0}_{1}.dll'.format(mskmajorver,mskminorver), 
                          'mosekxx{0}_{1}.dll'.format(mskmajorver,mskminorver), 
                          'libiomp5md.dll',
                          'mosekscopt{0}_{1}.dll'.format(mskmajorver,mskminorver) ]
    elif pf == 'Linux':
        if is_64bits:
            moseklibs = [ 'libmosek64.so.{0}.{1}'.format(mskmajorver,mskminorver),
                          'libiomp5.so', 
                          'libmosekxx{0}_{1}.so'.format(mskmajorver,mskminorver),
                          'libmosekscopt{0}_{1}.so'.format(mskmajorver,mskminorver)]
        else:
            moseklibs = [ 'libmosek.so.{0}.{1}'.format(mskmajorver,mskminorver), 
                          'libiomp5.so', 
                          'libmosekxx{0}_{1}.so'.format(mskmajorver,mskminorver),
                          'libmosekscopt{0}_{1}.so'.format(mskmajorver,mskminorver)]
    elif pf == 'Darwin':
        moseklibs     = [ 'libmosek64.{0}.{1}.dylib'.format(mskmajorver,mskminorver), 
                          'libiomp5.dylib',
                          'libmosekxx{0}_{1}.dylib'.format(mskmajorver,mskminorver),
                          'libmosekscopt{0}_{1}.dylib'.format(mskmajorver,mskminorver) ]
    else:
        raise VersionError("Unsupported platform {0}".format(pf))

    for lib in moseklibs:
        shutil.move(os.path.join(tgtpath,'mosek',mosekver,'tools','platform',pfname,'bin',lib),os.path.join(unpackdir,'mosek'))
else:
    mskmajorver, mskminorver,_,_ = getMosekVersion(tgtpath)



######################
# Call setup.py 
######################

from setuptools import setup, find_packages
import platform,sys
import os,os.path

setup( name='Mosek',
       version      = '{0}.{1}'.format(mskmajorver,mskminorver),
       packages     = [ 'mosek', 'mosek.fusion' ],
       
       package_data = { '' : ['*.so','*.dll','*.dylib','libmosek*' ] },
       
       install_requires = ['numpy>=1.4','python>=2.5'], 

       # Metadata
       author       = 'Mosek ApS',
       author_email = "support@mosek.com",
       description  = 'Mosek/Python APIs',
       long_description = 'Interface for MOSEK',
       license      = "See license.pdf in the MOSEK distribution",
       url          = 'http://www.mosek.com',
       keywords     = 'mosek optimization',
       )
