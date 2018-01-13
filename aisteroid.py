#######################################################
#           _____     _                 _     _       #
#     /\   |_   _|   | |               (_)   | |      # 
#    /  \    | |  ___| |_ ___ _ __ ___  _  __| |      #
#   / /\ \   | | / __| __/ _ \ '__/ _ \| |/ _` |      #
#  / ____ \ _| |_\__ \ ||  __/ | | (_) | | (_| |      #
# /_/    \_\_____|___/\__\___|_|  \___/|_|\__,_|      #
# Artificial Intelligence in the Search for Asteroids #
# Jorge I. Zuluaga [)] 2017                           #
# http://bit.ly/aisteroid                             #
#######################################################
# Common procedures
#######################################################

#############################################################
#MODULES
#############################################################
#ASTROPY
from astropy.io import fits
from astropy.modeling import models, fitting
from astropy.modeling.models import custom_model
from astropy.coordinates import Angle
from scipy.optimize import minimize

#ASTROALIGN
import astroalign as aal
from astroquery.vizier import Vizier
from skimage.transform import SimilarityTransform

#SYSTEM
import pickle,os,time,glob,collections,warnings,pprint
from datetime import datetime
from sys import argv,stdout,stderr,exit
import numpy as np
from collections import OrderedDict
import pandas as pd
from os import system

#IPython
from IPython.display import HTML, Image
import IPython.core.autocall as autocall

#############################################################
#CORE ROUTINES
#############################################################
class ExitClass(autocall.IPyAutocall):
    """ Supposingly an autcall class """
    def __call__(self):
        exit()

def in_ipynb():
    try:
        cfg = get_ipython().config 
        return True
    except NameError:
        return False

def error(msg,code=2,stream=stderr):
    print(msg,file=stderr)
    exit(code)

class dictObj(object):
    def __init__(self,dic={}):self.__dict__.update(dic)
    def __add__(self,other):
        self.__dict__.update(other.__dict__)
        return self

def loadConf(filename):
    d=dict()
    conf=dictObj()
    if os.path.lexists(filename):
        exec(open(filename).read(),{},d)
        conf+=dictObj(d)
        qfile=True
    else:
        error("Configuration file '%s' does not found."%filename)
    return conf

def loadArgv(default):
    d=default
    if QIPY or len(argv)==1:return dictObj(d)
    conf=dictObj()
    try:
        config=";".join(argv[1:]).replace("--","")
        exec(config,{},d)
        conf+=dictObj(d)
    except:
        error("Badformed options:",argv[1:])
    return conf

QIPY=False
if in_ipynb():
    QIPY=True
if not QIPY:
    def Image(url="",filename="",f=""):pass
    def get_ipython():
        foo=dictObj(dict())
        foo.run_line_magic=lambda x,y:x
        return foo

#GRAPHICAL
if not QIPY:
    from matplotlib import use
    use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as pat
from mpl_toolkits.mplot3d import Axes3D

#Pretty printer
PP=pprint.PrettyPrinter(indent=2).pprint

#############################################################
#COMMON ACTIONS
#############################################################
#AVOID WARNINGS
warnings.filterwarnings('ignore')

#LOAD CONFIGURATION
CONF=loadConf("aisteroid.cfg")

#LOAD ARGV
"""
Example:
  python script.py --file=1 "SET='example2'" var=3
"""
CONF=loadArgv(CONF.__dict__)

#############################################################
#DIRECTORIES
#############################################################
CONF.SETS_DIR=CONF.DATA_DIR+"sets/"
CONF.REP_DIR=CONF.DATA_DIR+"reports/"
CONF.IMAGE_DIR="doc/"
CONF.INPUT_DIR="util/"

#############################################################
#CONSTANTS
#############################################################
#Geometrical
DEG=np.pi/180
RAD=1/DEG

#
ARCSEC=1./3600
ARCMIN=60*ARCSEC

#Physical
MINUTE=60.0
HOUR=60*MINUTE
DAY=24*HOUR

MM=1e-3
MICRA=1e-6

#############################################################
#MACROS
#############################################################
#Convert from sexagesimal to decimal
#Example: sex2dec("23 03 45")
sex2dec=lambda s:np.sign(float(s.split()[0]))*(np.array([np.abs(float(x)) for x in s.split()]).dot([1.0,1/60.0,1/3600.]).sum())

#Convert a matrix of axes into a list
mat2lst=lambda M:M.reshape(1,M.shape[0]*M.shape[1])[0].tolist()

def print0(*args):
    if CONF.VERBOSE>=0:print(*args)
def print1(*args):
    if CONF.VERBOSE>=1:print(*args)
def print2(*args):
    if CONF.VERBOSE>=2:print(*args)
def print3(*args):
    if CONF.VERBOSE>=3:print(*args)

#############################################################
#ROUTINES
#############################################################
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

def dec2sex(d):
    s=np.sign(d)
    d=np.abs(d)
    dg=int(d)
    mm=(d-dg)*60
    mg=int(mm)
    sg=(mm-mg)*60
    return s*dg,mg,sg

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

def System(cmd,verbose=True,qexit=(False,None)):
    out=[]
    for path in _run(cmd):
        try:
            if verbose:print(path.decode("utf-8"))
            out+=[path.decode("utf-8")]
        except:
            out+=[(path[0],path[1].decode("utf-8"))]
            pass
    if qexit[0] and out[-1][0]>0:
        errcode="Error:\n"+out[-1][1]
        try:
            qexit[1].write("Error excuting:\n\t%s\n"%cmd)
            qexit[1].write(errcode)
            qexit[1].close()
            print("Writing error")
        except:pass
        error(errcode)
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
    
def forceAlignment(sources,si,ti):
    
    #Select bright sources
    s=sources[sources.IMG==si][sources.MAG_BEST<-10][["X_IMAGE","Y_IMAGE"]]
    t=sources[sources.IMG==ti][sources.MAG_BEST<-10][["X_IMAGE","Y_IMAGE"]]
    
    #Match sources
    sa,ta=matchSources(s,t)

    tr=SimilarityTransform()
    status=tr.estimate(sa,ta)
    return tr,(sa,ta)

def matchSources(si,ti,
                 risol=100,radius=10,
                 x="X_IMAGE",y="Y_IMAGE"):
    
    #Remove close sources
    sc=pd.DataFrame.copy(si)
    indr=[]
    for ind in sc.index:
        objs=sc.loc[ind]
        ds=((sc[x]-objs[x])**2+(sc[y]-objs[y])**2).\
            apply(np.sqrt).sort_values()
        cond=(ds<risol)&(ds>0)
        if cond.sum()>0:
            indr+=[sc[cond].index[0]]
    sc=sc.drop(indr)

    #Find matches
    sa=[];st=[];
    for i,inds in enumerate(sc.index):
        objs=sc.loc[inds]
        ds=((ti[x]-objs[x])**2+(ti[y]-objs[y])**2).\
            apply(np.sqrt).sort_values()
        cond=ds<radius
        if cond.sum()>0:
            indt=ti[cond].index[0]
            sa+=[inds]
            st+=[indt]
    sa=sc.loc[sa][[x,y]].values
    ta=ti.loc[st][[x,y]].values

    return sa,ta

def isolateSources(sources,radius=10):
    sc=pd.DataFrame.copy(sources)
    indr=[]
    inda=pd.Series(sc.index.values,index=sc.index)
    i=0
    while i<len(inda):
        ind=inda.iat[i]
        objs=sc.loc[ind]
        ds=((sc.X_IMAGE-objs.X_IMAGE)**2+(sc.Y_IMAGE-objs.Y_IMAGE)**2).\
            apply(np.sqrt).sort_values()
        cond=(ds<radius)&(ds>0)
        if cond.sum()>0:
            indr=sc[cond].index
            sc.drop(indr,inplace=True)
            inda.drop(indr,inplace=True)
        i+=1
    return sc

def waterMark(ax):
    ax.text(0.99,0.99,"http://bit.ly/aisteroid",
            fontsize=8,color='b',
            ha='right',va='top',rotation=90,transform=ax.transAxes)

def distanceSets(x,set1,set2,ix,iy):
    """
    Calculate the distance between two sets of objects stored in
    pandas dataframes (set1,set2) with coordinates named "ix" and
    "iy". The size of the sets could be different.

    The routine compute the minimum distance from each objects in set1
    to all objects of set2.  The total distance is the sum of all
    computed distances.
    """
    dx=x[0]*np.cos(x[1])
    dy=x[0]*np.sin(x[1])
    ds=np.array([((set1.loc[ind,ix]+dx-set2.loc[:,ix])**2+\
                  (set1.loc[ind,iy]+dy-set2.loc[:,iy])**2).apply(np.sqrt).sort_values().iat[0] for ind in set1.index[:]])
    return ds.sum()

def matchSets(set1,set2,ix,iy):
    """
    Find the index of objects in set2 which are closest to objects in set1
    """
    im=np.array([((set1.loc[ind,ix]-set2.loc[:,ix])**2+\
                  (set1.loc[ind,iy]-set2.loc[:,iy])**2).apply(np.sqrt).idxmin() for ind in set1.index[:]])
    return im

def translation2D(tr,r):
    dx=tr[0]*np.cos(tr[1])
    dy=tr[0]*np.sin(tr[1])
    return [r[0]+dx,r[1]+dy]

def SEXtract(imgdir,imgfile,**options):
    print2("\tRunning SEXtractor over %s..."%imgfile)
        
    #Configuration 
    default=OrderedDict(
        CATALOG_NAME="asteroid.cat",
        CATALOG_TYPE="FITS_1.0",
        FILTER_NAME="asteroid.conv",
    )
    default.update(options)

    if "DETECT_THRESH" in default.keys():
        if default["DETECT_THRESH"]<0:del default["DETECT_THRESH"]

    confile=imgdir+"/asteroid.sex"

    #Save configuration file
    f=open(confile,"w")
    for item in default.items():f.write(str(item[0])+"\t"+str(item[1])+"\n")
    f.close()

    #Run SEXtractor
    opts=""
    opts+=" "+"-c asteroid.sex"
    cmd=CONF.SEX_DIR+"bin/sex "+opts+" "+imgfile+".fits"
    sys="cd "+imgdir+";"+cmd
    out=System(sys)

    #Process output
    if out[-1][0]!=0:
        print("\t\tError processing image",file=stderr)
        error(out[-1][1])
    else:
        output=out[-1][1]
        #STORE RESULTS
        out=System("cd "+imgdir+";cp "+default["CATALOG_NAME"]+" %s.cat"%imgfile,
                   False)
        hdul=fits.open(imgdir+"%s.cat"%imgfile)
        header=hdul[1].header
        data=hdul[1].data
        hdul.close()
        nsources=len(data)
    return output,header,data,nsources

def listImages():
    out=System("for i in $(ls "+CONF.SETS_DIR+"*.zip);do echo -n $(basename $i |cut -f 1 -d'.');echo -n ', ';done")

def saveAnim(ani,directory,animfile,nimg=4):
    out=System("rm -rf %s/.blink*"%directory)
    out=System("rm -rf .blink*")
    ani.save(directory+'.blink.html')
    cmd="convert -delay 100 $(find %s -name '.blink*.png' -o -name 'frame*.png' |sort |head -n %d) %s"%(directory,nimg,animfile)
    out=System(cmd)
    out=System("rm -rf %s/.blink*"%directory)

if __name__=="__main__":

    """
      $PYTHON aisteroid.py option=1 
    """
    #========================================
    #LIST AVAILABLE IMAGE SETS
    #========================================
    if "listimages" in CONF.__dict__.keys():
        print0("Available image sets")
        i=0
        listimg=glob.glob("%s/*.zip"%CONF.SETS_DIR)
        for imageset in listimg:
            print0("\t"+os.path.basename(imageset))
            if i>CONF.NUM_SETS:
                print0("\t...")
                break
            i+=1
        print0("%d image sets available."%len(listimg))
