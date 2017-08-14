This is a cross-platform MOSEK installer for Python PIP supporting Python 2.7+ and Python 3.3+. 

To install the latest revision of the package do
```
pip install --user git+http://github.com/MOSEK/Mosek.pip
```
If you wish to install the MOSEK 7,1, you need to install the 7.1 specific branch:
```
pip install --user git+http://github.com/MOSEK/Mosek.pip@7.1
```

Specific releases can be installed as 
```
pip install --user https://github.com/MOSEK/Mosek.pip/archive/7.1.45.tar.gz
```

The links can be used with both Python 2 and 3.

If you are installing using Miniconda, PyEnv or another locally installed Python, you should leave out the `--user` argument.
