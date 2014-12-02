import platform,sys
import os,os.path
import httplib
import types
import shutil

class VersionError(Exception): pass
class URLError(Exception): pass


######################
# Platform setup
######################

major,minor,_,_,_ = sys.version_info
if major != 2 or minor < 5:
    print "Python 2.5+ required, got %d.%d" % (major,minor)
mosekver = '7'

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
                raise URLError("Failed to fetch MOSEK package '{0}'. Response {1} ({2})".format(url,r.status,r.reason))    
            print "Fetching {0} -> {1}".format(url,pkgfilename)
            with open(pkgfilename,"wb") as f:
                shutil.copyfileobj(r,f)
            print "OK"
        else:
            print "Not redownloading. Use {0}".format(pkgfilename)
    else:
        pkgfilename = os.path.join(unpackdir,pkgname)
        c.request('GET',pkgpath)
        r = c.getresponse()
        if r.status != 200:
            raise URLError("Failed to fetch MOSEK package '{0}'. Response {1} ({2})".format(url,r.status,r.reason))    
        print "Fetching {0} -> {1} ".format(url,pkgfilename)
        with open(pkgfilename,"wb") as f:
            shutil.copyfileobj(r,f)
        print "OK"
finally:
    c.close()

######################
# Unpack Mosek package
######################

pfx = 'mosek/{0}/tools/platform/{1}/'.format(mosekver,pfname)
tgtpath = os.path.join(unpackdir,"platform")
try: os.makedirs(tgtpath)
except OSError: pass

print "Unpacking..."
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
print("OK")

######################
# Call setup.py 
######################

setupmod = types.ModuleType("MosekSetup")
setupfilename = os.path.join(tgtpath,'mosek',mosekver,'tools','platform',pfname,'python','2','setup.py')
setupmod.__file__ = setupfilename
execfile(setupfilename,setupmod.__dict__)
