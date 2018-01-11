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
# Alignment procedure
#######################################################
from aisteroid import *

#######################################################
#AUXILIAR VARIABLES
#######################################################
OUT_DIR=CONF.SCR_DIR+CONF.SET+"/"
AIA=OUT_DIR+"analysis.aia"
CFG=[line.rstrip('\n') for line in open(CONF.SETS_DIR+CONF.CFG+".cfg")]
MPCCODE=Config(CFG,"MPCCode")
OBSERVER=Config(CFG,"Observer")
TELESCOPE=Config(CFG,"Telescope")[0]
ISTEP=1

VPRINT0("*"*60)
VPRINT0("Asteroid detection in set '%s'"%CONF.SET)
VPRINT0("*"*60)

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#UNPACK THE IMAGE SET
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Unpacking images"%ISTEP);ISTEP+=1
setfile=CONF.SETS_DIR+CONF.SET+".zip"
if not os.path.isfile(setfile):
    error("No set file '%s'"%setfile)
out=System("rm -rf "+OUT_DIR,CONF.VERBOSE)
out=System("mkdir -p "+OUT_DIR,CONF.VERBOSE)
out=System("cp "+CONF.INPUT_DIR+"template/* "+OUT_DIR,CONF.VERBOSE)
out=System("unzip -j -o -d "+OUT_DIR+" "+setfile,CONF.VERBOSE)
if out[-1][0]==0:VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#READ THE IMAGES
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Reading images"%ISTEP);ISTEP+=1
images=[]
for image in sorted(glob.glob(OUT_DIR+"*.fits")):
    VPRINT1("\tReading image "+image)
    hdul=fits.open(image)
    im=dict()
    im["file"]=image.split("/")[-1].replace(".fits","")
    im["header"]=hdul[0].header
    im["data"]=hdul[0].data
    im["obstime"]=hdul[0].header["DATE-OBS"]
    im["unixtime"]=date2unix(im["obstime"])
    images+=[im]
    hdul.close()
nimgs=len(images)
if not nimgs:error("No images provided.")
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#DETECTOR PROPERTIES
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Detector properties"%ISTEP);ISTEP+=1
VPRINT1("Telescope & CCD Properties:")
FOCAL=Config(CFG,"FocalLength") #mm
PW=Config(CFG,"PixelWide") #mm
PH=Config(CFG,"PixelHigh") #mm
SIZEX=images[0]["header"]["NAXIS1"]
SIZEY=images[0]["header"]["NAXIS2"]
PWD=np.arctan(PW/FOCAL)*RAD
PHD=np.arctan(PW/FOCAL)*RAD
PXSIZE=(PWD+PHD)/2
VPRINT1("\tFocal lenght (mm) :",FOCAL)
VPRINT1("\tPixel size (x mm,y mm) :",PW,PH)
VPRINT1("\tImage size (x px,y px) :",SIZEX,SIZEY)
VPRINT1("\tPixel size (arcsec):",PXSIZE/ARCSEC)
VPRINT1("\tCamera field (x deg,y deg) :",SIZEX*PWD,SIZEY*PHD)
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#EXTRACTING SOURCES
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Extracting sources"%ISTEP);ISTEP+=1
for i,image in enumerate(images):
    file=image["file"]
    header=image["header"]

    #SEXtract
    VPRINT1("\tRunning SEXtractor over %s..."%file)
    output,header,data,nsources=SEXtract(OUT_DIR,file)
    hdul=fits.open(OUT_DIR+"%s.cat"%file)
    image["sourcexxy_header"]=hdul[1].header
    image["sourcexxy"]=hdul[1].data
    hdul.close()
    NSOURCES=len(image["sourcexxy"])
    VPRINT1("\t\t%d sources saved."%NSOURCES)
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#COMPILING SOURCES INFORMATION
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Compiling source information"%ISTEP);ISTEP+=1
allsources=pd.DataFrame()
for i,image in enumerate(images):
    srcxys=pd.DataFrame(image["sourcexxy"])
    alls=pd.concat([srcxys],axis=1)

    #Aligned coordinates
    alls["T"]=image["unixtime"]
    alls["X_ALIGN"]=0.0
    alls["Y_ALIGN"]=0.0
    
    #Astrometry
    alls["RA"]=0.0
    alls["DEC"]=0.0
    alls["ERR_RA"]=0.0
    alls["ERR_DEC"]=0.0
        
    #Alignment attributes
    alls["IMG"]=i #In which image is this source
    alls["STAR"]=0 #Is this a star?

    #Detection attributes
    alls["OBJ"]=0 #To which object it belongs (detection procedure)
    alls["NIMG"]=1 #In how many images is the object present (detection procedure)
    alls["MOBJ"]=0 #To which moving object it belongs (detection procedure)

    #Photometric attributes
    alls["MAG_ASTRO"]=0.0
    alls["ERR_MAG_ASTRO"]=0.0
    
    allsources=allsources.append(alls)

allsources.sort_values(by="MAG_BEST",ascending=True,inplace=True)
allsources.reset_index(inplace=True)

for i,image in enumerate(images):
    image["xy"]=allsources[allsources.IMG==i][["X_IMAGE","Y_IMAGE"]].values

VPRINT0("\tAll sources:",len(allsources.index))
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#FIND ALIGNMENT PARAMETERS
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Alignment"%ISTEP);ISTEP+=1
VPRINT1("\tReference image:",images[0]["file"])

#Reference image is not aligned
allsources.loc[allsources.IMG==0,"X_ALIGN"]=allsources[allsources.IMG==0]["X_IMAGE"]
allsources.loc[allsources.IMG==0,"Y_ALIGN"]=allsources[allsources.IMG==0]["Y_IMAGE"]

columns=["X_IMAGE","Y_IMAGE"]
for i,image in enumerate(images[1:]):

    VPRINT1("\tAligning image:",images[i]["file"])
    imsources=allsources[allsources.IMG==(i+1)]
    
    #Align
    tr,(ta,sa)=forceAlignment(allsources,i+1,i)
    image["transform"]=tr

    #Align all coordinates
    xy=imsources[columns].values
    xya=[]
    for j in range(xy.shape[0]):
        xyr=xy[j,:]
        for ia in range(i+1,0,-1):
            tr=images[ia]["transform"]
            xyr=tr(xyr).tolist()
        xya+=xyr
    xya=np.array(xya)
    imsources[["X_ALIGN","Y_ALIGN"]]=pd.DataFrame(xya,columns=["X_ALIGN","Y_ALIGN"],index=imsources.index)
    allsources.loc[allsources.IMG==(i+1),["X_ALIGN","Y_ALIGN"]]=imsources
    
VPRINT0("\tDone.")

#############################################################
#1-FIND POTENTIAL MOVING OBJECTS
#############################################################
VPRINT0("Step %s:Potential moving objects"%ISTEP);ISTEP+=1
VPRINT1("\tSearching RADIUS (pixels, arcsec):",CONF.RADIUS,CONF.RADIUS*PXSIZE/ARCSEC)
RADIUS=CONF.RADIUS

iobj=1
for i,ind in enumerate(allsources.index):
    obj=allsources.loc[ind]
    x=obj.X_ALIGN;y=obj.Y_ALIGN
    if obj.NIMG>1:continue

    #COMPUTE THE EUCLIDEAN DISTANCE TO ALL OBJECTS NOT FOUND YET
    cond=allsources.NIMG==1
    searchobjs=allsources[cond]
    ds=((x-searchobjs.X_ALIGN)**2+(y-searchobjs.Y_ALIGN)**2).apply(np.sqrt)

    #IN HOW MANY IMAGES THE OBJECT IS PRESENT
    cond=ds<RADIUS
    inds=searchobjs[cond].index
    nimg=len(allsources.ix[inds])
    allsources.loc[inds,"NIMG"]=nimg

    #ASSIGN OBJECT NUMBER
    if nimg==4:
        allsources.loc[inds,"OBJ"]=iobj
        iobj+=1

moving=allsources[allsources.NIMG<2]
rest=allsources[allsources.NIMG>=2]
VPRINT0("\tNumber of potentially moving objects: ",len(moving))
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#DETECT OBJECTS
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Detect objects"%ISTEP);ISTEP+=1

xmin=allsources["X_ALIGN"].min()
xmax=allsources["X_ALIGN"].max()
ymin=allsources["Y_ALIGN"].min()
ymax=allsources["Y_ALIGN"].max()

#////////////////////////////////////////
#PREPARATION
#////////////////////////////////////////
#Numbers
nimgs=len(images)
nmax=nimgs-3
ix="X_ALIGN"
iy="Y_ALIGN"

#Layers and times
ninds=[]
layers=[]
dts=np.zeros((nimgs,nimgs))
for i in range(nimgs):
    image=images[i]
    layers+=[moving[moving.IMG==i].sort_values(by=['X_ALIGN','Y_ALIGN'])]
    ninds+=[len(layers[-1])]
    for j in range(len(images)):
        dts[i,j]=images[j]["unixtime"]-images[i]["unixtime"]

#Ranges
xmax=max(allsources.X_ALIGN);xmin=min(allsources.X_ALIGN)
ymax=max(allsources.Y_ALIGN);ymin=min(allsources.Y_ALIGN)
        
ntot=ninds[0]*(ninds[1]+ninds[2])+ninds[1]*(ninds[2]+ninds[3])+ninds[2]*ninds[3]
VPRINT1("Estimate number of rulers:",ntot)
VPRINT1("Times between images:")

#////////////////////////////////////////
#RULER DETECTION
#////////////////////////////////////////
dobj=[]
mobj=1
for ind in moving.index:moving.loc[ind,"MOBJ"]=0
for i in range(nimgs):
    VPRINT1("Layer %d:"%i)
    ref=layers[i]
    VPRINT1("\tNumber of sources:",len(ref))
    for j in range(i+1,nimgs):
        if i==j:continue
        VPRINT1("\tKick layer %d:"%j)
        kic=layers[j]
        VPRINT1("\t\tNumber of sources:",len(kic))
        dt=dts[i,j]
        VPRINT1("\t\tTime between layers:",dt)
        
        #Create rulers
        for indr in ref.index[:]:
            if moving.loc[indr,"MOBJ"]>0:continue
            rulers=[]
            for indk in kic.index:
                if moving.loc[indk,"MOBJ"]>0:continue
                vx=(kic.loc[indk,ix]-ref.loc[indr,ix])/dt
                vy=(kic.loc[indk,iy]-ref.loc[indr,iy])/dt

                #If contiguous object is too close it may be an error
                d=np.sqrt((vx*dt)**2+(vy*dt)**2)
                if d<10*CONF.RADIUS:continue
                
                ruler=[]
                for k in range(nimgs):
                    ruler+=[[images[k]["unixtime"],
                             ref.loc[indr,ix]+vx*dts[i,k],
                             ref.loc[indr,iy]+vy*dts[i,k],
                             ref.loc[indr,"MAG_ASTRO"]]]
                ruler=np.array(ruler)
                if ((ruler[:,1]>xmax)|(ruler[:,1]<xmin)).sum()>nmax or                    ((ruler[:,2]>ymax)|(ruler[:,2]<ymin)).sum()>nmax:
                    continue

                rulers+=[ruler]

                #Match
                hits=np.zeros(4)
                objs=-1*np.ones(4)
                for k in range(nimgs):
                    if k==i:
                        hits[k]=1
                        objs[k]=indr
                    if k==j:
                        hits[k]=1    
                        objs[k]=indk
                    else:
                        ds=((ruler[k,1]-moving.loc[(moving.IMG==k)&(moving.MOBJ==0),ix])**2+(ruler[k,2]-moving.loc[(moving.IMG==k)&(moving.MOBJ==0),iy])**2).apply(np.sqrt)
                        if ds.min()<CONF.RADIUS:
                            hits[k]=1
                            objs[k]=ds.idxmin()
                if hits.sum()>=3:
                    VPRINT1("\t\t\tObject %d detected"%mobj)
                    VPRINT1("\t\t\tObject indexes:",objs)
                    
                    #Plot line
                    points=[]
                    mags=[]
                    xs=[]
                    ys=[]
                    impoints=[]
                    for ind in objs:
                        if ind<0:continue
                        points+=[moving.loc[ind,[ix,iy]].values]
                        impoints+=[moving.loc[ind,"IMG"]]
                        mags+=[moving.loc[ind,"MAG_BEST"]]
                        xs+=[moving.loc[ind,"X_IMAGE"]]
                        ys+=[moving.loc[ind,"Y_IMAGE"]]
                        VPRINT1("\t\t\t\tMag %d = %.1f"%(ind,mags[-1]))
                    
                    points=np.array(points)
                    magvar=np.array(mags).std()
                    xvar=np.array(xs).std()
                    yvar=np.array(ys).std()
                    
                    VPRINT1("\t\t\t\tCoordinate variance (%.2f) = "%CONF.RADIUS,xvar,yvar)
                    if xvar<CONF.RADIUS or yvar<CONF.RADIUS:
                        VPRINT1("\t\t\t\t***Object rejected by coordinate variance***")
                        continue

                    VPRINT1("\t\t\t\tMag variance = %.2f"%(magvar))
                    if magvar>CONF.MAGVAR:
                        VPRINT1("\t\t\t\t***Object rejected by magnitude variance***")
                        continue
       
                    VPRINT0("\tObject %d detected"%mobj)
                    moving.loc[objs[objs>0].tolist(),"MOBJ"]=mobj

                    mobj+=1
                
#Compile information about detected objects 
indxs=moving[moving.MOBJ>0].index
mobjs=np.unique(moving.MOBJ.values)
nobj=len(mobjs[mobjs>0])

VPRINT0("\tNumber of detected objects:",nobj)
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#ANNOTATED
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Annotated blinking image"%ISTEP);ISTEP+=1
import time
animfile="%s/detection-%s.gif"%(OUT_DIR,CONF.SET)
VPRINT1("\tAnnotated ('%s')"%animfile)

#Figure
fig=plt.figure(figsize=(8,8))

#Show first image
imgargs=dict(cmap='gray_r',vmin=0,vmax=700)
im=plt.imshow(images[0]["data"],animated=True,**imgargs)

#Title
tm=plt.title("Set %s, Image 0: "%CONF.SET+images[0]["obstime"],fontsize=10)

#Water mark
waterMark(fig.gca())

#Show detected objects
for mobj in range(1,nobj+1):
    cond=moving.loc[indxs].MOBJ==mobj
    inds=moving.loc[indxs].index[cond]
    idobj="%s%04d"%("OBJ",mobj)
    n=1
    for ind in inds:
        obj=allsources.loc[ind]
        plt.plot(obj.X_IMAGE-1,obj.Y_IMAGE-1,'ro',ms=10,mfc='None',alpha=0.2)
        if n==1:
            plt.text(obj.X_IMAGE+5,obj.Y_IMAGE+5,"%s"%idobj,color='r',fontsize=6)
        n+=1

#Basic decoration
plt.axis("off")
fig.tight_layout()

#Update figure
def updatefig(i):
    #Select image
    iimg=i%nimgs
    im.set_array(images[iimg]["data"])
    tm.set_text("Set %s, Image %d: "%(CONF.SET,iimg)+images[iimg]["obstime"])
    return im,


#Create animation
ani=animation.FuncAnimation(fig,updatefig,frames=range(nimgs),
                            interval=1000,repeat_delay=1000,
                            repeat=True,blit=True)

#Save animattion
out=System("rm -rf %s/blink*"%OUT_DIR)
ani.save(OUT_DIR+'blink.html')
time.sleep(1)
out=System("convert -delay 100 $(find %s -name 'blink*.png' -o -name 'frame*.png' |grep -v '04' |sort) %s"%(OUT_DIR,animfile))
out=System("rm -rf blink*")

VPRINT0("\tDone.")
