#############################################################
#DIRECTORIES
#############################################################
HOME_DIR="/home/jzuluaga/Astrometry/AIsteroid"
DATA_DIR="data/"
SETS_DIR=DATA_DIR+"sets/"
REP_DIR=DATA_DIR+"reports/"
IMAGE_DIR="images/"
SCR_DIR="scratch/"
INPUT_DIR="input/"
AST_DIR="/home/astrometry/astrometry/"
SEX_DIR="/home/astrometry/sextractor/"

#############################################################
#MODULES
#############################################################
import pickle,os,time
from datetime import datetime
from sys import argv
import numpy as np
import astroalign as aal
from matplotlib import use
use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
from astropy.io import fits
from astropy.modeling import models, fitting
from astropy.modeling.models import custom_model
import glob
from collections import OrderedDict
import collections
import pandas as pd
from os import system
import warnings
warnings.filterwarnings('ignore')

#############################################################
#ROUTINES AND MACROS
#############################################################
#MACROS
DEG=np.pi/180
RAD=1/DEG
ARCSEC=1./3600
ARCMIN=60*ARCSEC
MINUTE=60.0
HOUR=60*MINUTE
DAY=24*HOUR

#Get configuration line from a list  
#Example: Config(cfg,"Latitude")
Config=lambda c,x:[s for s in c if x in s]
def Config(c,x):
    vs=[]
    for t in [s for s in c if x in s]:
        vs+=[t.split("=")[1]]
    if len(vs)==1:
        try:vs=float(vs[0])
        except:vs=vs[0]
    return vs

#Convert from sexagesimal to decimal
#Example: sex2dec("23 03 45")
sex2dec=lambda s:np.sign(float(s.split()[0]))*(np.array([np.abs(float(x)) for x in s.split()]).dot([1.0,1/60.0,1/3600.]).sum())

def dec2sex(d):
    s=np.sign(d)
    d=np.abs(d)
    dg=int(d)
    mm=(d-dg)*60
    mg=int(mm)
    sg=(mm-mg)*60
    return s*dg,mg,sg


#Convert a matrix of axes into a list
mat2lst=lambda M:M.reshape(1,sum(M.shape))[0].tolist()

#Intelligent Shell script execution
def _run(cmd):
    import sys,subprocess
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    while True:
        line = p.stdout.readline().rstrip()
        if not line:
            break
        yield line
    (output,error)=p.communicate()
    yield p.returncode,error

def System(cmd,verbose=True):
    out=[]
    for path in _run(cmd):
        try:
            if verbose:print(path.decode("utf-8"))
            out+=[path.decode("utf-8")]
        except:
            out+=[(path[0],path[1].decode("utf-8"))]
            pass
    return out

#Convert a record array (mixed type) in a double arrays
#Example: a = np.recarray((1,), dtype=[('x', int), ('y', float), ('z', int)]); 
#a['x']=1;a['y']=2.3;a['z']=4
#a=rec2arr(a)
def rec2arr(a):
    a=np.array(a)
    dt = a.dtype
    dt = dt.descr
    nt=[]
    for t in dt:
        t = (t[0], 'float64')
        nt+=[t]
    dt = np.dtype(nt)
    a = a.astype(dt)
    a=a.view(np.float).reshape(a.shape + (-1,))
    return a

def date2unix(datet):
    #datet="2017-09-14T09:54:45.670299"
    sec=float(datet.split(":")[-1])
    import time,ciso8601
    ts=ciso8601.parse_datetime(datet)
    unix=time.mktime(ts.timetuple())+(sec-int(sec))
    return unix
    
def imageProps(image,cfg):
    #Angular size of each pixel
    F=Config(cfg,"FocalLength") #Microns
    pxx=Config(cfg,"PixelWide") #Microns
    pxdx=np.arctan(pxx/F)*RAD
    sizex=image["header"]["NAXIS1"]
    pxy=Config(cfg,"PixelHigh") #Microns
    sizey=image["header"]["NAXIS2"]
    pxdy=np.arctan(pxy/F)*RAD
    pxsize=(pxdx+pxdy)/2
    #print("Image properties:")
    #print("\tPixel size (micras): %f x %f"%(pxx,pxy))
    #print("\tPixel size (arcsec): %f x %f"%(pxdx/ARCSEC,pxdy/ARCSEC))
    #print("\tCCD Field (deg): %f x %f"%(sizex*pxdx,sizey*pxdy))
    #print("\tAverage pixel size (arcsec):",pxsize/ARCSEC)
    return pxdx,pxdy,sizex,sizey
