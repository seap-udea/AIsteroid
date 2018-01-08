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
VPRINT0("Asteroid detection in set %s"%CONF.SET)
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
    f=open(OUT_DIR+"%s.head"%im["file"],"w")
    f.write(im["header"].tostring("\n"))
    f.close()
    nimgs=len(images)
if not len(images):
    error("No images provided.")
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#ANIMATE
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Blinking image"%ISTEP);ISTEP+=1
animfile="%s/%s.gif"%(OUT_DIR,CONF.SET)
VPRINT1("\tNot annotated ('%s')"%animfile)

#Figure
fig=plt.figure(figsize=(8,8))

#Show first image
imgargs=dict(cmap='gray_r',vmin=0,vmax=700)
im=plt.imshow(images[0]["data"],animated=True,**imgargs)

#Title
tm=plt.title("Set %s, Image 0: "%CONF.SET+images[0]["obstime"],fontsize=10)

#Water mark
waterMark(fig.gca())

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

#Save animation
out=System("rm -rf %s/blink*"%OUT_DIR)
ani.save(OUT_DIR+'blink.html')
time.sleep(1)
out=System("convert -delay 100 $(find %s -name 'blink*.png' -o -name 'frame*.png' |grep -v '04' |sort) %s"%(OUT_DIR,animfile))
out=System("rm -rf blink*")

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
    #SEX COMMAND
    VPRINT1("\tRunning SEXtractor over %s..."%file)
    opts=""
    opts+=" "+"-c asteroid.sex"
    cmd=CONF.SEX_DIR+"bin/sex "+opts+" "+file+".fits"
    sys="cd "+OUT_DIR+";"+cmd
    out=System(sys)
    if out[-1][0]!=0:
        VPRINT1("\t\tError processing image")
        VPRINT1(out[-1][1])
    else:
        VPRINT1("\t\tExtraction successful")
        #STORE RESULTS
        image["sex_output"]=out[-1][1]
        System("cd "+OUT_DIR+";cp asteroid.cat %s.cat"%file,False)
        hdul=fits.open(OUT_DIR+"%s.cat"%file)
        image["sourcexxy_header"]=hdul[1].header
        image["sourcexxy"]=hdul[1].data
        hdul.close()
        NSOURCES=len(image["sourcexxy"])
        VPRINT1("\t\t%d sources saved."%NSOURCES)
VPRINT0("\tNumber of sources:",NSOURCES)
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
#SHOW THE SOURCES
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
VPRINT0("Step %s:Map of sources"%ISTEP);ISTEP+=1
#Which image do you want the sources be shown?
iimg=1
image=images[iimg]

fig,axs=plt.subplots(1,1,sharex=True,sharey=True,figsize=(7,7))
ax=axs
imgargs=dict(cmap='gray_r',vmin=0,vmax=500)
ax.imshow(image["data"],**imgargs)       
ax.axis("off")
itime=image["header"]["DATE-OBS"]
ax.set_title(image["file"]+"\n"+"Time:"+itime,fontsize=8,position=(0.5,1.0))

#Show the sources
ax.plot(images[0]["xy"][:,0]-1,images[0]["xy"][:,1]-1,'b+',ms=10,mfc='None')
ax.plot(image["xy"][:,0]-1,image["xy"][:,1]-1,'ro',ms=3,mfc='None')

fig.tight_layout()
fig.savefig(OUT_DIR+"sources-%d.png"%iimg)
VPRINT0("\tDone.")

# **NOTES ON IMAGE**: Red circles show the sources in the selected images. Blue crosses are the sources detected in the first image. You may notice that there are sources in one image that were not detected in the other one.  Additionally if you make a zoom in in any area of the images you will see that the sources positions among images differ by a few pixels.  These are errors in the pointing of the telescope.

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
    
    #Measure initial misalignment
    ta,sa=matchSources(imsources[columns],
                       allsources[allsources.IMG==i][columns])
    mab=np.abs(sa-ta).mean()
    VPRINT1("\t\tAverage distance before alignment:",mab)

    #Align
    tr,(ta,sa)=forceAlignment(allsources,i+1,i)
    image["transform"]=tr

    #Measure misalignment after procedure
    sp=[]
    for j in range(ta.shape[0]):sp+=tr(ta[j,:]).tolist()
    sp=np.array(sp)
    maa=np.abs(sa-sp).mean()
    VPRINT1("\t\tAverage distance after alignment:",maa)
    VPRINT1("\t\tYou improved the alignment by a factor of ",mab/maa)
    
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
    
    #Measure alignment
    VPRINT1("\t\tChecking alignment in the whole image:")

    ta,sa=matchSources(allsources[allsources.IMG==(i+1)],allsources[allsources.IMG==0])
    VPRINT1("\t\t\tAverage distance before alignment:",np.abs(sa-ta).mean())

    ta,sa=matchSources(pd.DataFrame(allsources.loc[allsources.IMG==(i+1),["X_ALIGN","Y_ALIGN"]].values,columns=columns),
                       pd.DataFrame(allsources.loc[allsources.IMG==0,["X_ALIGN","Y_ALIGN"]].values,columns=columns))
    VPRINT1("\t\t\tAverage distance after alignment:",np.abs(sa-ta).mean())

VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#RESULT OF THE ALIGNMENT PROCEDURE
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Plot results of alignment"%ISTEP);ISTEP+=1
# Figure
fig,axs=plt.subplots(3,2,sharex=True,sharey=True,figsize=(8,12))

dx=SIZEX/10
dy=SIZEY/10

#Show the misaligned sources
images[0]["xy_aligned"]=allsources.loc[allsources.IMG==0,["X_ALIGN","Y_ALIGN"]].values
for i,image in enumerate(images[1:]):
    iimg=i+1
    imsource=allsources[allsources.IMG==(i+1)]
    image["xy"]=imsource[["X_IMAGE","Y_IMAGE"]].values
    image["xy_aligned"]=imsource[["X_ALIGN","Y_ALIGN"]].values
    
    xcen=image["xy"][:,0].mean()
    ycen=image["xy"][:,1].mean()
    
    ax=axs[i,0]
    ax.plot(images[0]["xy"][:,0]-1,images[0]["xy"][:,1]-1,'b+',ms=10,mfc='None')
    ax.plot(image["xy"][:,0]-1,image["xy"][:,1]-1,'ro',ms=3,mfc='None')

    ax.set_title("Original")
    ax.set_ylabel("Image %d"%iimg)

    ax=axs[i,1]
    ax.set_title("Aligned")
    ax.plot(images[0]["xy_aligned"][:,0]-1,images[0]["xy_aligned"][:,1]-1,'b+',ms=10,mfc='None')
    ax.plot(image["xy_aligned"][:,0]-1,image["xy_aligned"][:,1]-1,'ro',ms=3,mfc='None')
    
#Zoom in the center
ax.set_xlim((xcen-dx,xcen+dx))
ax.set_ylim((ycen-dy,ycen+dy))

for ax in mat2lst(axs):
    ax.set_xticks([])
    ax.set_yticks([])

fig.tight_layout()
fig.savefig(OUT_DIR+"alignment-%d.png"%iimg)
VPRINT0("\tDone.")

# **NOTES ON IMAGE**: Red circles show the sources in the corresponding images, blue crosses are the sources detected in the first image.

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#BUILD DATABASE OF CLOSE SOURCES
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Astrometry"%ISTEP);ISTEP+=1
VPRINT1("Looking for star in the field covered by the images...")
rmin=allsources["ALPHA_J2000"].min()
rmax=allsources["ALPHA_J2000"].max()
dmin=allsources["DELTA_J2000"].min()
dmax=allsources["DELTA_J2000"].max()
rmean=(rmin+rmax)/2;dr=(rmax-rmin)/2
dmean=(dmin+dmax)/2;dd=(dmax-dmin)/2
ra=dec2sex(rmean/15)
dec=dec2sex(dmean)
ras="%d %d %.2f"%(int(ra[0]),int(ra[1]),ra[2])
des="%d %d %.2f"%(int(dec[0]),int(dec[1]),dec[2])
radius=np.sqrt(dr**2+dd**2)

columns=['_RAJ2000','_DEJ2000','R1mag']
v=Vizier(columns=columns)
v.ROW_LIMIT=-1
#radius=Angle(radius,"deg"),
result=v.query_region("%s %s"%(ras,des),
                      width=Angle(2*dr,"deg"),height=Angle(2*dd,"deg"),
                      catalog='USNOB1')[0]
cond=result["R1mag"]>0
stars=pd.DataFrame(rec2arr(result[cond]),
                   columns=["ALPHA_J2000","DELTA_J2000","Rmag"])
VPRINT0("\tNumber of reference stars found:",len(stars))
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#SHOW THE STARS IN THE FIELD
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
VPRINT0("Step %s:Stars in the field"%ISTEP);ISTEP+=1
iimg=0
imgsources=allsources[allsources.IMG==iimg][allsources.MAG_BEST<-12]
fig,axs=plt.subplots(1,1,sharex=True,sharey=True,figsize=(7,7))
ax=axs

#Show the sources
ax.plot(imgsources["ALPHA_J2000"],imgsources["DELTA_J2000"],'ro',ms=5,mfc='None')
ax.plot(stars["ALPHA_J2000"],stars["DELTA_J2000"],'b*',ms=5)

fig.tight_layout()
fig.savefig(OUT_DIR+"stars.png")
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#MATCH IMAGE AND STAR DATABASE
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Matching stars"%ISTEP);ISTEP+=1
a="ALPHA_J2000"
d="DELTA_J2000"

for i,image in enumerate(images):
    file=image["file"]
    imgsources=allsources[allsources.IMG==i]
    bright=imgsources[imgsources.MAG_BEST<-14]
    nbright=len(bright)

    #Comparing set of sources
    VPRINT1("\tMatching for image %s"%file)    
    VPRINT1("\t\tNumber of selected bright stars:",len(bright))
    VPRINT1("\t\tPresent average distance to stars:",distanceSets([0,0],bright,stars,a,d)/nbright/ARCSEC)
        
    #Find optimal translation
    solution=minimize(distanceSets,[0,0],method='Nelder-Mead',tol=1e-6,args=(bright,stars,a,d))
    image["translation"]=solution.x

    VPRINT1("\t\tMatching parameters:",image["translation"])
    VPRINT1("\t\tImproved average distance:",distanceSets(image["translation"],bright,stars,a,d)/nbright/ARCSEC)
    
    #Translate position of stars
    bright[[a,d]]=[translation2D(image["translation"],[alpha,delta])                                 for alpha,delta in zip(bright[a],bright[d])]

    #Match bright sources and stars
    stars_ind=matchSets(bright,stars,a,d)
    zeros=stars.loc[stars_ind,"Rmag"].values-bright["MAG_BEST"].values
    image["zeropoint"]=zeros.mean()
    image["zerostd"]=zeros.std()
    
    #Aligning positions
    VPRINT1("\t\tAligning")    
    tr=SimilarityTransform()
    status=tr.estimate(bright[[a,d]].values,stars.loc[stars_ind,[a,d]].values)
    VPRINT1("\t\t\tSuccess:",status)
    image["astrometry"]=tr
    
    #Alligning all sources
    xy=imgsources[[a,d]].values
    xya=[]
    for j in range(xy.shape[0]):
        xyr=xy[j,:]
        xyr=translation2D(image["translation"],xyr)
        xyr=image["astrometry"](xyr).tolist()
        xya+=xyr
    xya=np.array(xya)
    
    imgsources[["RA","DEC"]]=pd.DataFrame(xya,columns=["RA","DEC"],index=imgsources.index)
    allsources.loc[allsources.IMG==i,["RA","DEC"]]=imgsources
    
    #Photometric properties
    allsources.loc[allsources.IMG==i,["MAG_ASTRO"]]=imgsources["MAG_BEST"]+image["zeropoint"]
    allsources.loc[allsources.IMG==i,["ERR_MAG_ASTRO"]]=(imgsources["MAGERR_BEST"]**2+image["zerostd"]**2).apply(np.sqrt)
    
    #Last verification
    imgsources=allsources[allsources.IMG==i]
    bright=imgsources[imgsources.MAG_BEST<-14]
    nstars=stars.rename(columns={"ALPHA_J2000":"RA","DELTA_J2000":"DEC"})
    VPRINT1("\t\tAverage distance to stars after astrometry:",distanceSets([0,0],bright,nstars,"RA","DEC")/nbright/ARCSEC)

VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#PLOT IMAGE MATCH
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Plot star matching"%ISTEP);ISTEP+=1

npx=int(len(images)/2)

fig,axs=plt.subplots(npx,2,sharex=True,sharey=True,figsize=(2*4,4*npx))
axl=mat2lst(axs)

for i,image in enumerate(images):

    imgsources=allsources[allsources.IMG==i]
    bright=imgsources[imgsources.MAG_BEST<-14]
    
    #Show the sources
    axl[i].plot(stars.loc[stars.index[:]]["ALPHA_J2000"],stars.loc[stars.index[:]]["DELTA_J2000"],'b*',ms=5)
    axl[i].plot(bright.loc[bright.index[:]]["RA"],bright.loc[bright.index[:]]["DEC"],'ro',ms=5,mfc='None')
    
    axl[i].set_title("Image %d"%i)
    axl[i].set_xticks([])
    axl[i].set_yticks([]) 
    #break
    
fig.tight_layout()
fig.savefig(OUT_DIR+"stars-%d.png"%i)

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
VPRINT1("\tNumber of potentially moving objects: ",len(moving))
VPRINT0("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#SHOW THE PTENTIAL MOVING OBJECTS
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
VPRINT0("Step %s:Potential moving objects plot"%ISTEP);ISTEP+=1
#Which image do you want the sources be shown?
iimg=0
image=images[iimg]

fig,axs=plt.subplots(1,1,sharex=True,sharey=True,figsize=(7,7))
ax=axs
imgargs=dict(cmap='gray_r',vmin=0,vmax=500)
ax.imshow(image["data"],**imgargs)       
ax.axis("off")
time=image["header"]["DATE-OBS"]
ax.set_title(image["file"]+"\n"+"Time:"+time,fontsize=8,position=(0.5,1.0))

#Show the sources
gray=plt.get_cmap('gray')
ax.plot(rest["X_IMAGE"]-1,rest["Y_IMAGE"],'o',color=gray(0.7),ms=5,alpha=1)
ax.plot(rest["X_IMAGE"]-1,rest["Y_IMAGE"],'o',color=gray(0.7),ms=5,alpha=1)
ax.plot(moving["X_IMAGE"]-1,moving["Y_IMAGE"],'bo',ms=10,mfc='None',alpha=0.2)
ax.plot(moving["X_IMAGE"]-1,moving["Y_IMAGE"],'b+',ms=5,mfc='None',alpha=0.2)

fig.tight_layout()
fig.savefig(OUT_DIR+"moving.png")
VPRINT0("\tDone.")

# **NOTES**: Objects in rest have been masked (gray circles) to highlight the moving objects which are in the center of the blue circles.

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#DETECT OBJECTS
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Detect objects"%ISTEP);ISTEP+=1

#////////////////////////////////////////
#LAYERS PLOT
#////////////////////////////////////////
plt.ion()
fig3d = plt.figure(figsize=(10,10))
ax3d = fig3d.add_subplot(111, projection='3d')

xmin=allsources["X_ALIGN"].min()
xmax=allsources["X_ALIGN"].max()
ymin=allsources["Y_ALIGN"].min()
ymax=allsources["Y_ALIGN"].max()

xs=np.linspace(xmin,xmax,10)
ys=np.linspace(ymin,ymax,10)
X,Y=np.meshgrid(xs,ys)

colors=['r','b','g','y']
nimg=len(images)
for i,image in enumerate(images):
    objects=moving[moving.IMG==i][["X_ALIGN","Y_ALIGN"]].values
    Z=i*np.ones_like(X)
    ax3d.plot_wireframe(X,Y,Z,lw=0.5,color=colors[i%nimg],alpha=0.1)
    ax3d.plot(objects[:,0],objects[:,1],i,'o',color=colors[i%nimg],ms=1.5)

ax3d.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
ax3d.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
ax3d.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

ax3d.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
ax3d.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
ax3d.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))

ax3d.set_xticks([])
ax3d.set_yticks([])
ax3d.set_zticks([])

ax3d.set_zlim((-4,4))
ax3d.view_init(5,30)


# **NOTES**: Colors are, red for image 0, blue for image 1, green for image 2 and yellow for image 3.

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
    #i=1 #Starts in the second image
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
            #indr=987 #Normal
            #indr=1166 #Starts in the second image
            #indr=744 #Skips second 
            #VPRINT1("Object %d (%d)"%(indr,moving.loc[indr,"MOBJ"]))
            #VPRINT1("\t\tObject position:",ref.loc[indr,[ix,iy]].values)
            if moving.loc[indr,"MOBJ"]>0:continue
            rulers=[]
            for indk in kic.index:
                if moving.loc[indk,"MOBJ"]>0:continue
                #indk=1057 #Normal
                #indk=947
                #indk=822 #Skips second
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
                #VPRINT1(ruler)
                    
                #matchRuler(ruler,moving,i,j)
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
                    VPRINT1("\t\t\tMagnitudes:")
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
                    if magvar>0.2:
                        VPRINT1("\t\t\t\t***Object rejected by magnitude variance***")
                        continue
                             
                    moving.loc[objs[objs>0].tolist(),"MOBJ"]=mobj

                    #Plot a line
                    ax3d.plot(points[:,0],points[:,1],impoints,'ko-',lw=0.5,ms=5,mfc='None')
            
                    mobj+=1

#////////////////////////////////////////
#SAVE LAYER PLOT
#////////////////////////////////////////
fig3d.savefig(OUT_DIR+"objects3d.png",bbox_inches='tight',pad_inches = 0,transparent = True)
                
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

#############################################################
#PERFORM PHOTOMETRY ON DETECTED OBJECTS
#############################################################
VPRINT0("Step %s:Photometry"%ISTEP);ISTEP+=1
columns=moving.columns.tolist()+["IDOBJ","IDIMG","DATE"
                                     "SNR","FWHM",
                                     "X_PSF","Y_PSF",
                                     "MAG_MEAN","MAG_MIN","MAG_MAX","MAG_RANGE","MAG_VAR",
                                     "SNR_MEAN","SNR_MIN","SNR_MAX","SNR_RANGE","SNR_VAR"]
objects=pd.DataFrame(columns=columns)

for mobj in range(1,nobj+1):

    #Get sources corresponding to object mobj
    cond=moving.loc[indxs].MOBJ==mobj
    inds=moving.loc[indxs].index[cond]

    #Create an index for this object
    idobj="%04d"%(mobj)

    VPRINT1("\tObject %s:"%idobj)
    n=1
    mags=[]
    snrs=[]
    for ind in inds:

        #Get object information
        objp=allsources.loc[ind]
        iimg=int(objp.IMG)
        image=images[iimg]
        READOUT=image["header"]["HIERARCH CELL.READNOISE"]

        idimg=idobj+"."+str(n)
        objp["IDIMG"]=idimg
        objp["IDOBJ"]=idobj

        VPRINT1("\t\tPSF fitting for image of object OBJ%s"%idimg)
        n+=1

        #DATE
        obstime=images[iimg]["obstime"]
        exptime=float(images[iimg]["header"]["EXPTIME"])
        parts=obstime.split(".")
        dt=datetime.strptime(parts[0],"%Y-%m-%dT%H:%M:%S")
        fday=(dt.hour+dt.minute/60.0+(dt.second+exptime/2+int(parts[1])/1e6)/3600.0)/24.0
        fday=("%.6f"%fday).replace("0.","")
        objp["DATE"]=dt.strftime("%Y %m %d.")+fday

        #GET DATA IMAGE
        data=rec2arr(images[iimg]["data"])
        x=int(objp.X_IMAGE)
        y=int(objp.Y_IMAGE)
        VPRINT1("\t\t\tExpected position:",x,y)
        
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #2D PSH FIT
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        dx=10 #Error in photometry
        dy=10 #Error in photometry
        ws=5  #Number of errors to select for fitting
        xs=np.arange(x-ws*dx,x+ws*dx,1)
        pxs=data[y,x-ws*dx:x+ws*dx,0]
        ys=np.arange(y-ws*dy,y+ws*dy,1)
        pys=data[y-ws*dy:y+ws*dy,x,0]

        sigmax2=10 #Estimated error in X
        sigmay2=10 #Estimated error in y
        meanx=x
        meany=y
        X,Y=np.meshgrid(xs,ys)
        P=data[y-ws*dy:y+ws*dy,x-ws*dx:x+ws*dx,0]

        def gaussianLevel2(tx,ty,level=0.0,amplitude=1.0,
                           meanx=meanx,meany=meany,
                           sigmax2=sigmax2,sigmay2=sigmay2):
            g=amplitude*np.exp(-0.5*((tx-meanx)**2/sigmax2+(ty-meany)**2/sigmay2))
            f=g+level
            return f

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #FIT RESULTS
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        g_init=custom_model(gaussianLevel2)()
        fit=fitting.SLSQPLSQFitter()
        g=fit(g_init,X,Y,P,verblevel=0)
        #VPRINT1("\t\tResults (level,amplitude,meanx,meany,sigmax,sigmay):\n\t\t\t%s"%str(g.parameters))

        xc=g.meanx.value
        yc=g.meany.value
        sigmam=np.sqrt(g.sigmax2.value+g.sigmay2.value)
        amplitude=g.amplitude.value
        level=g.level.value
        objp["FWHM"]=2.355*sigmam
        objp["X_PSF"]=xc
        objp["Y_PSF"]=yc

        VPRINT1("\t\t\tPSF position:",xc,yc)
        VPRINT1("\t\t\tFWHM:",objp.FWHM)
        
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #COMPUTE SNR
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        title="Object %d, %s, %s"%(ind,idimg,obstime)

        try:
            ws=5
            x=int(g.meanx.value)
            y=int(g.meany.value)
            dx=int(np.sqrt(g.sigmax2.value))
            dy=int(np.sqrt(g.sigmay2.value))
            xs=np.arange(x-ws*dx,x+ws*dx,1)
            ys=np.arange(y-ws*dy,y+ws*dy,1)
            X,Y=np.meshgrid(xs,ys)
            P=data[y-ws*dy:y+ws*dy,x-ws*dx:x+ws*dx,0]
            Pth=gaussianLevel2(X,Y,
                               level=g.level.value,amplitude=g.amplitude.value,
                               meanx=g.meanx.value,meany=g.meany.value,
                               sigmax2=g.sigmax2.value,sigmay2=g.sigmay2.value)
            D=P-Pth
            noise=D.std()
            objp["SNR"]=g.amplitude.value/noise
            VPRINT1("\t\t\tSNR = ",objp.SNR)
            VPRINT1("\t\t\tMAG = %.1f +/- %.2f"%(objp.MAG_ASTRO,objp.ERR_MAG_ASTRO))
        except:
            objp.SNR=-1.0
        mags+=[objp.MAG_ASTRO]
        snrs+=[objp.SNR]
        
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #PLOT 2D FIT
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        if CONF.PHOTOPLOT and objp.SNR>0:
            plt.ioff()
            fig = plt.figure()
            ax3d = fig.add_subplot(111, projection='3d')
            ax3d.plot_wireframe(X,Y,P,lw=0.5)
            ngrid=50
            Xs,Ys=np.meshgrid(np.linspace(xs[0],xs[-1],ngrid),
                              np.linspace(ys[0],ys[-1],ngrid))
            Zs=gaussianLevel2(Xs,Ys,
                              level=g.level.value,amplitude=g.amplitude.value,
                              meanx=g.meanx.value,meany=g.meany.value,
                              sigmax2=g.sigmax2.value,sigmay2=g.sigmay2.value)
            ax3d.plot_surface(Xs,Ys,Zs,cmap='hsv',alpha=0.2)
            ax3d.set_title(title,position=(0.5,1.05),fontsize=10)
            fig.savefig(OUT_DIR+"psf2d-%s.png"%idimg)

            #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
            #1D PLOT OF PSF FITTING
            #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
            xs=np.arange(x-ws*dx,x+ws*dx,1)
            pxs=data[y,x-ws*dx:x+ws*dx,0]
            pxts=level+amplitude*np.exp(-0.5*((xs-x)**2/g.sigmax2.value))
            rxs=pxs-pxts

            ys=np.arange(y-ws*dy,y+ws*dy,1)
            pys=data[y-ws*dy:y+ws*dy,x,0]
            pyts=level+amplitude*np.exp(-0.5*((ys-y)**2/g.sigmay2.value))
            rys=pys-pyts

            xt=np.linspace(xs[0],xs[-1],100)
            pt=level+amplitude*np.exp(-0.5*((xt-x)**2/g.sigmax2.value))

            fig,axs=plt.subplots(2,1,sharex=True,gridspec_kw={'height_ratios':[2,1]})
            ax=axs[0]
            ax.plot((xs-x)/np.sqrt(g.sigmax2.value),pxs,'ko')
            ax.plot((ys-y)/np.sqrt(g.sigmay2.value),pys,'ko')
            ax.plot((xt-x)/np.sqrt(g.sigmax2.value),pt,'r-')
            ax.set_xlim((-ws,+ws))
            ax.set_ylim((min(pxs.min(),pys.min()),max(pxs.max(),pys.max())))
            ax.axvspan(-objp.FWHM/2/sigmam,+objp.FWHM/2/sigmam,color='b',alpha=0.2)
            ax.axhspan(0,level,color='k',alpha=0.2)
            ax.set_xticks([])
            legend=""
            legend+="SNR = %.2f\n"%objp.SNR
            legend+="FWHM (arcsec) = %.2f\n"%(objp.FWHM*PXSIZE/ARCSEC)
            legend+="MAG = %+.1f\n"%(objp.MAG_ASTRO)
            ax.text(0.95,0.95,legend,
                    ha='right',va='top',transform=ax.transAxes,color='k',fontsize=12)
            ax.set_ylabel("Counts")
            ax.set_title("Object %s"%idimg)
            waterMark(ax)

            ax=axs[1]
            ax.plot((xs-x)/np.sqrt(g.sigmax2.value),rxs,'ko')
            ax.plot((ys-y)/np.sqrt(g.sigmay2.value),rys,'ko')
            ax.set_ylim((-level,level))
            ax.axhspan(-noise,noise,color='k',alpha=0.2)
            ax.set_ylabel("Residual (count)")

            fig.tight_layout()
            fig.subplots_adjust(hspace=0)
            fig.savefig(OUT_DIR+"psf1d-%s.png"%idimg)

        #ADD OBJECT
        objects=objects.append(objp,ignore_index=True)

        #break
    mags=np.array(mags)
    snrs=np.array(snrs)
    
    #Storing object properties
    objects.loc[objects.IDOBJ==idobj,"MAG_MIN"]=mags.min()
    objects.loc[objects.IDOBJ==idobj,"MAG_MAX"]=mags.max()
    objects.loc[objects.IDOBJ==idobj,"MAG_RANGE"]=mags.max()-mags.min()
    objects.loc[objects.IDOBJ==idobj,"MAG_MEAN"]=mags.mean()
    objects.loc[objects.IDOBJ==idobj,"MAG_VAR"]=mags.std()

    objects.loc[objects.IDOBJ==idobj,"SNR_MIN"]=snrs.min()
    objects.loc[objects.IDOBJ==idobj,"SNR_MAX"]=snrs.max()
    objects.loc[objects.IDOBJ==idobj,"SNR_RANGE"]=snrs.max()-snrs.min()
    objects.loc[objects.IDOBJ==idobj,"SNR_MEAN"]=snrs.mean()
    objects.loc[objects.IDOBJ==idobj,"SNR_VAR"]=snrs.std()

    VPRINT1("\t\tMag: [%.1f,%.1f:%.1f] %.1f +/- %.2f"%(mags.min(),mags.max(),
                                                     mags.max()-mags.min(),
                                                     mags.mean(),mags.std()))
    VPRINT1("\t\tSNR: [%.1f,%.1f:%.1f] %.1f +/- %.2f"%(snrs.min(),snrs.max(),
                                                     snrs.max()-snrs.min(),
                                                     snrs.mean(),snrs.std()))

objects.to_csv(OUT_DIR+"objects-%s.csv"%CONF.SET,index=False)
VPRINT0("\tDone.")


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#SELECT OBJECTS
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
VPRINT0("Step %s:Select objects"%ISTEP);ISTEP+=1
selfile=OUT_DIR+"select-%s.txt"%CONF.SET
f=open(selfile,"w")
VPRINT1("Generating selection report...")

typo="C"
mago="R"
lines=""
header="%-5s|%-68s|%-10s|%-10s|%-10s|\n"%("ID","REPORT","SNR_MIN","SNR_MAX","MAG_RANGE")
f.write(header)
f.write("-"*len(header)+"\n")
for ind in objects.index:
    objp=objects.loc[ind]
    parts=str(objp.IDIMG).split(".")
    idimg="%04d.%1d"%(int(parts[0]),int(parts[1]))
    idobj="%s%s"%(CONF.TEAM,objp.IDOBJ)
    VPRINT1("\tReport for image %s"%idimg)
    
    mag=objp.MAG_ASTRO
    ras=dec2sex(objp.RA/15)
    decs=dec2sex(objp.DEC)
    
    entry="%3s%1s%02d %02d %6.3f%02d %02d %5.2f%13.1f%2s%9s"%        (typo,
         objp.DATE,
         int(ras[0]),int(ras[1]),ras[2],
         int(decs[0]),int(decs[1]),decs[2],
         mag,
         mago,
         MPCCODE
        )

    line="%-5s|%-68s|%-10.2f|%-10.2f|%-10.2f|\n"%        (objp.IDOBJ,
         entry,
         objp.SNR_MIN,
         objp.SNR_MAX,
         objp.MAG_RANGE
        )
    lines+=line

if len(objects.index)==0:
    f.write("NO MOVING OBJECTS DETECTED\n\n")
else:
    f.write(lines)
f.close()
out=System("cat "+selfile)
VPRINT0("\tDone.")
