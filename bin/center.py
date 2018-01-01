import numpy as np
from astropy.io import fits
from sys import argv,exit
sex2dec=lambda s:np.sign(float(s.split()[0]))*(np.array([np.abs(float(x)) for x in s.split()]).dot([1.0,1/60.0,1/3600.]).sum())

#READ SOURCES
try:
    filename=argv[1]
    hdul=fits.open('%s'%filename)
except:
    print("You must provide a valid file basename")
    exit(1)

ra=hdul[0].header["OBJCTRA"]
dec=hdul[0].header["OBJCTDEC"]

radeg=sex2dec(ra)*15
decdeg=sex2dec(dec)

print("--ra %.7f --dec %.7f --radius 1"%(radeg,decdeg))
