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
# Detection procedure
#######################################################
from aisteroid import *

#######################################################
#LOCAL CONFIGURATION
#######################################################
#Output directory
OUT_DIR=CONF.SCR_DIR+CONF.SET+"/"

#File to pickle analysis results
AIA=OUT_DIR+"analysis.aia"

#Observatory configuration file
CFG=[line.rstrip('\n') for line in open(CONF.SETS_DIR+CONF.CFG+".cfg")]

#######################################################
#LOADING DETECTION RESULTS
#######################################################
if not os.path.isfile(AIA):
    error("You have not performed the astrometry on this set.")

print("Loading astrometry results...")
analysis=pickle.load(open(AIA,"rb"))
images=analysis["images"]
allsources=analysis["allsources"]
nimgs=len(images)

#######################################################
#CCD PROPERTIES
#######################################################
print("Telescope & CCD Properties:")
FOCAL=Config(CFG,"FocalLength") #mm
PW=Config(CFG,"PixelWide") #mm
PH=Config(CFG,"PixelHigh") #mm
SIZEX=images[0]["header"]["NAXIS1"]
SIZEY=images[0]["header"]["NAXIS2"]
PWD=np.arctan(PW/FOCAL)*RAD
PHD=np.arctan(PW/FOCAL)*RAD
PXSIZE=(PWD+PHD)/2
print("\tFocal lenght (mm) :",FOCAL)
print("\tPixel size (x mm,y mm) :",PW,PH)
print("\tImage size (x px,y px) :",SIZEX,SIZEY)
print("\tPixel size (arcsec):",PXSIZE/ARCSEC)
print("\tCamera field (x deg,y deg) :",SIZEX*PWD,SIZEY*PHD)

#######################################################
#DETECTING
#######################################################
if "indxs" in analysis.keys() and not CONF.OVERWRITE:
    print("Loading detection results...")
    indxs=analysis["indxs"]
    nobj=len(np.unique(allsources.loc[indxs].MOBJ.values))
    print("\tObjects load: ",nobj)
    print("\tObjects index: ",indxs)
else:
    #############################################################
    #1-FIND POTENTIAL MOVING OBJECTS
    #############################################################
    print("Find potential moving objects...")
    print("\tSearching RADIUS (pixels, arcsec):",CONF.RADIUS,CONF.RADIUS*PXSIZE/ARCSEC)
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
        cond=ds<2*RADIUS
        inds=searchobjs[cond].index
        nimg=len(allsources.ix[inds])
        allsources.loc[inds,"NIMG"]=nimg

        #ASSIGN OBJECT NUMBER
        if nimg==4:
            allsources.loc[inds,"OBJ"]=iobj
            iobj+=1

    moving=allsources[allsources.NIMG<2]
    print("\tNumber of potentially moving objects: ",len(moving))

    #############################################################
    #3-DETECT MOVING OBJECTS
    #############################################################
    print("Find moving objects...")
    layers=[]
    for i in range(len(images)):
        layers+=[moving[moving.IMG==i].sort_values(by=['X_ALIGN','Y_ALIGN'])]

    #Ranges
    xmax=max(allsources.X_ALIGN);xmin=min(allsources.X_ALIGN)
    ymax=max(allsources.Y_ALIGN);ymin=min(allsources.Y_ALIGN)

    #First level of crossing
    dt1=(images[1]["unixtime"]-images[0]["unixtime"])
    dt2=(images[2]["unixtime"]-images[1]["unixtime"])
    dt3=(images[3]["unixtime"]-images[1]["unixtime"])

    nobj=0
    indxs=[]
    mobj=1
    for indl in layers[0].index:
        objl=layers[0].loc[indl]

        nout=0;nfar=0;nfou=0;ntot=0
        for indu in layers[1].index:
            ntot+=1
            obju=layers[1].loc[indu]

            #Compute speed
            vr=(obju.X_ALIGN-objl.X_ALIGN)/dt1
            vd=(obju.Y_ALIGN-objl.Y_ALIGN)/dt1

            #Check distance to close object
            d=np.sqrt((vr*dt1)**2+(vd*dt1)**2)
            if d<2*RADIUS:
                #If close object is too close continue
                continue

            #Extrapolate to next layer (Layer 2)
            xn=obju.X_ALIGN+vr*dt2
            yn=obju.Y_ALIGN+vd*dt2

            #Check if extrapolated position is beyond searching region
            if xn>xmax or xn<xmin or yn>ymax or yn<ymin:
                nout+=1
                continue

            #Search for close objects in the next layer (Layer 2)
            cond=((layers[2].Y_ALIGN-yn)**2+
                  (layers[2].X_ALIGN-xn)**2).apply(np.sqrt).sort_values()<RADIUS
            exts=layers[2][cond]
            if len(exts)==0:
                #No close objects in the following layer
                nfar+=1
                continue

            dmin=((exts.Y_ALIGN-yn)**2+(exts.X_ALIGN-xn)**2).apply(np.sqrt).iat[0]
            idmin1=exts.index[0]

            #Extrapolate to next layer (Layer 3)
            xu=obju.X_ALIGN+vr*dt3
            yu=obju.Y_ALIGN+vd*dt3

            #Check if extrapolated position is beyond searching region
            if xu>xmax or xu<xmin or yu>ymax or yu<ymin:
                nout+=1
                continue

            #Search for close objects in the next layer (Layer 3)
            cond=((layers[3].Y_ALIGN-yu)**2+
                  (layers[3].X_ALIGN-xu)**2).apply(np.sqrt).sort_values()<RADIUS
            exts=layers[3][cond]
            if len(exts)==0:
                nfar+=1
                continue

            dmin=((exts.Y_ALIGN-yu)**2+(exts.X_ALIGN-xu)**2).apply(np.sqrt).iat[0]
            idmin2=exts.index[0]

            if dmin<RADIUS:
                nfou+=1
                nobj+=1
                nindx=[indl,indu,idmin1,idmin2]
                indxs+=nindx
                allsources.loc[nindx,"MOBJ"]=mobj
                mobj+=1

    print("\t%d objects found"%nobj)
    print("\tObjects:",indxs)

    print("Pickling moving analysis...")
    analysis["indxs"]=indxs
    pickle.dump(analysis,open(AIA,"wb"))
    
#############################################################
#CREATING ANIMATIONS
#############################################################
print("Creating animation for '%s'..."%CONF.SET)

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#NOT ANNOTATED
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
animfile="%s/%s.gif"%(OUT_DIR,CONF.SET)
print("\tNot annotated ('%s')"%animfile)

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
print("\tDone.")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#ANNOTATED
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
animfile="%s/detection-%s.gif"%(OUT_DIR,CONF.SET)
print("\tAnnotated ('%s')"%animfile)

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
    cond=allsources.loc[indxs].MOBJ==mobj
    inds=allsources.loc[indxs].index[cond]
    idobj="%s%04d"%("OBJ",mobj)
    n=1
    for ind in inds:
        obj=allsources.loc[ind]
        plt.plot(obj.X_IMAGE,obj.Y_IMAGE,'ro',ms=10,mfc='None',alpha=0.2)
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
print("\tDone.")
