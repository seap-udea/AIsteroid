"""
Classical algorithm for extraction and identification of moving objects in an image set
"""
from aisteroid import *

#############################################################
#BASIC CONFIGURATION
#############################################################
#SET="ps1-20170914_4_set096"
#SET="ps1-20170914_11_set176"
SET="ps1-20170913_1_set142"

OUT_DIR=SCR_DIR+SET+"/"
AIA=OUT_DIR+"analysis.aia"
CFG=SET.split("-")[0]+".cfg"
cfg=[line.rstrip('\n') for line in open(SETS_DIR+CFG)]
MPCCODE=Config(cfg,"MPCCode")
TEAM="NEA"

RADIUS=3

#############################################################
#1-EXTRACT SOURCES
#############################################################
if os.path.isfile(AIA):# and 0:
    print("Loading pickled analysis results...")
    analysis=pickle.load(open(AIA,"rb"))
    images=analysis["images"]
    allsources=analysis["allsources"]
else:
    print("Analysing images...")
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1.1-UNPACK THE IMAGE SET
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    out=System("rm -rf "+OUT_DIR)
    out=System("mkdir -p "+OUT_DIR)
    out=System("cp "+INPUT_DIR+"template/* "+OUT_DIR)
    out=System("unzip -j -o -d "+OUT_DIR+" "+SETS_DIR+SET+".zip")

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1.2-READ THE IMAGES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    images=[]
    print("Reading images")
    for image in sorted(glob.glob(OUT_DIR+"*.fits")):
        print("\tReading image "+image)
        hdul=fits.open(image)
        im=dict()
        im["file"]=image.split("/")[-1].replace(".fits","")
        im["header"]=hdul[0].header
        im["data"]=hdul[0].data
        im["obstime"]=hdul[0].header["DATE-OBS"]
        im["unixtime"]=date2unix(im["obstime"])
        im["transform"]=None
        images+=[im]
        hdul.close()
        f=open(OUT_DIR+"%s.head"%im["file"],"w")
        f.write(im["header"].tostring("\n"))
        f.close()

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1.3-ALIGN THE IMAGES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Aligning images")
    print("\tReference image:",images[0]["file"])
    for i,image in enumerate(images[1:]):
        print("\tAlign image ",image["file"])
        tr,(s,t)=aal.find_transform(images[0]["data"],images[i+1]["data"])
        image["transform"]=tr.inverse

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1.4-SEXTRACT SOURCES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    """
    print("SEXtracting sources")
    for i,image in enumerate(images):
        file=image["file"]
        header=image["header"]

        #SEX COMMAND
        print("\tRunning SEXtractor over %s..."%file)
        opts=""
        opts+=" "+"-c asteroid.sex"
        cmd=SEX_DIR+"bin/sex "+opts+" "+file+".fits"
        sys="cd "+OUT_DIR+";"+cmd
        out=System(sys)
        if out[-1][0]!=0:
            print("\t\tError processing image")
            print(out[-1][1])
        else:
            print("\t\tExtraction successful")
            #STORE RESULTS
            image["sex_output"]=out[-1][1]
            System("cd "+OUT_DIR+";cp asteroid.cat %s.cat"%file,False)
            hdul=fits.open(OUT_DIR+"%s.cat"%file)
            image["catalogue_header"]=hdul[1].header
            image["catalogue"]=hdul[1].data

            #Transform
            data=rec2arr(image["catalogue"])
            xy=data[:,2:5:2]
            if i>0:
                tr=image["transform"]
                xya=[]
                for j in range(xy.shape[0]):xya+=tr(xy[j,:]).tolist()
                xya=np.array(xya)
            else:xya=xy
            image["catalogue_aligned"]=xya

            #WRITING XY FITS FILE FOR ASTROMETRY.NET
            hdul[1].data["X_IMAGE"]=xya[:,0]
            hdul[1].data["Y_IMAGE"]=xya[:,1]
            hdul.writeto(OUT_DIR+"%s.xyls"%image["file"],overwrite=True)
            hdul.close()

    print("Done.")
    """

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1.5-PERFORMING ASTROMETRY
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Astrometry analysis...")
    for i,image in enumerate(images):
        file=image["file"]
        header=image["header"]

        #GET COORDINATES
        ra=sex2dec(header["OBJCTRA"])*15
        dec=sex2dec(header["OBJCTDEC"])

        #ASTROMETRY.NET COMMAND
        print("\tRunning astrometry over %s..."%file)
        opts=""
        opts+=" "+"--use-sextractor --sextractor-path "+SEX_DIR+"bin/sex"
        opts+=" "+"--no-plots"
        opts+=" "+"--ra %.7f --dec %.7f --radius 1"%(ra,dec)
        opts+=" "+"--guess-scale --overwrite"
        cmd=AST_DIR+"bin/solve-field "+opts+" "+file+".fits"
        sys="cd "+OUT_DIR+";"+cmd
        out=System(sys,False)
        if out[-1][0]!=0:
            print("\t\tError processing image")
            print(out[-1][1])
        else:
            print("\t\tAstrometry processing successful")
            #STORE RESULTS
            image["astro_output"]="\n".join(out[:-1])

            #SOURCE XY AND MAG
            hdul=fits.open(OUT_DIR+"%s.axy"%file)
            image["objects_header"]=hdul[1].header
            image["objects"]=hdul[1].data
            hdul.close()

            #TRANSFORM
            data=rec2arr(image["objects"])
            xy=data[:,:2]
            if i>0:
                tr=image["transform"]
                xya=[]
                for j in range(xy.shape[0]):xya+=tr(xy[j,:]).tolist()
                xya=np.array(xya)
            else:xya=xy
            image["objects_aligned"]=xya

            #SOURCES RA,DEC
            cmd=AST_DIR+"bin/wcs-xy2rd -X 'X_IMAGE' -Y 'Y_IMAGE' -w %s.wcs -i %s.axy -o %s.ard"%(file,file,file)
            sys="cd "+OUT_DIR+";"+cmd
            out=System(sys,False)

            hdul=fits.open(OUT_DIR+"%s.ard"%file)
            image["objectsrd_header"]=hdul[1].header
            image["objectsrd"]=hdul[1].data
            hdul.close()

            #STARS X,Y
            hdul=fits.open(OUT_DIR+"%s-indx.xyls"%file)
            image["stars_header"]=hdul[1].header
            image["stars"]=hdul[1].data
            hdul.close()

            #STARS RA,DEC
            hdul=fits.open(OUT_DIR+"%s.rdls"%file)
            image["starsrd_header"]=hdul[1].header
            image["stars"]=hdul[1].data
            hdul.close()

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1.5-COMPILING ALL SOURCES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Compiling all sources...")
    allsources=pd.DataFrame()
    for i,image in enumerate(images):
        objs=pd.DataFrame(image["objects"])
        alig=pd.DataFrame(image["objects_aligned"],columns=["X_ALIGN","Y_ALIGN"])
        ords=pd.DataFrame(image["objectsrd"])
        alls=pd.concat([objs,alig,ords],axis=1)
        alls["IMG"]=i #In which image is the source
        alls["OBJ"]=0 #To which object it belongs
        alls["NIMG"]=1 #In how many images is the object present
        alls["MOBJ"]=0 #To which moving object it belongs
        allsources=allsources.append(alls)
    allsources.sort_values(by="MAG_AUTO",inplace=True)
    allsources.reset_index(inplace=True)
    print("\tTotal number of sources:",len(allsources))

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1.6-STORING RESULTS
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Pickling image analysis...")
    analysis=dict(images=images,allsources=allsources)
    pickle.dump(analysis,open(AIA,"wb"))

if "indxs" in analysis.keys():
    indxs=analysis["indxs"]
    nobj=len(np.unique(allsources.loc[indxs].MOBJ.values))
else:
    #############################################################
    #2-FIND POTENTIAL MOVING OBJECTS
    #############################################################
    print("Find potential moving objects...")
    print("\tSearch RADIUS (pixels):",RADIUS)

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
#4-CREATE ANIMATION WITH ANNOTATION
#############################################################
print("Creating animation for '%s'..."%SET)

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#4.1-NO ANNOTATED
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
animfile="%s/%s.gif"%(OUT_DIR,SET)
print("\tNo annotated ('%s')"%animfile)

fig=plt.figure(figsize=(8,8))
imgargs=dict(cmap='gray_r',vmin=0,vmax=700)
im=plt.imshow(images[0]["data"],animated=True,**imgargs)
tm=plt.title("Set %s, Image 0: "%SET+images[0]["obstime"],fontsize=10)

plt.axis("off")
fig.tight_layout()

def updatefig(i):
    iimg=i%4
    im.set_array(images[iimg]["data"])
    tm.set_text("Set %s, Image %d: "%(SET,iimg)+images[i%4]["obstime"])
    return im,

ani=animation.FuncAnimation(fig,updatefig,frames=[0,1,2,3],interval=1000,repeat_delay=1000,repeat=True,blit=True)

out=System("rm -rf %s/blink*"%OUT_DIR)
ani.save(OUT_DIR+'blink.html')
time.sleep(1)
out=System("convert -delay 100 $(find %s -name 'blink*.png' |grep -v '04' |sort) %s"%(OUT_DIR,animfile))

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#4.1-ANNOTATED
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
animfile="%s/detection-%s.gif"%(OUT_DIR,SET)
print("\tAnnotated ('%s')"%animfile)

fig=plt.figure(figsize=(8,8))
imgargs=dict(cmap='gray_r',vmin=0,vmax=700)
im=plt.imshow(images[0]["data"],animated=True,**imgargs)
tm=plt.title("Set %s, Image 0: "%SET+images[0]["obstime"],fontsize=10)
plt.text(0.99,0.99,"http://bit.ly/aisteroid",fontsize=8,color='b',
         ha='right',va='top',rotation=90,transform=fig.gca().transAxes)

for mobj in range(1,nobj+1):
    cond=allsources.loc[indxs].MOBJ==mobj
    inds=allsources.loc[indxs].index[cond]
    idobj="%s%04d"%(TEAM,mobj)
    n=1
    for ind in inds:
        obj=allsources.loc[ind]
        plt.plot(obj.X_IMAGE,obj.Y_IMAGE,'ro',ms=10,mfc='None',alpha=0.2)
        if n==1:
            plt.text(obj.X_IMAGE+5,obj.Y_IMAGE+5,"%s"%idobj,color='r',fontsize=6)
        n+=1

plt.axis("off")
fig.tight_layout()

def updatefig(i):
    iimg=i%4
    im.set_array(images[iimg]["data"])
    tm.set_text("Set %s, Image %d: "%(SET,iimg)+images[i%4]["obstime"])
    return im,

ani=animation.FuncAnimation(fig,updatefig,frames=[0,1,2,3],interval=1000,repeat_delay=1000,repeat=True,blit=True)

out=System("rm -rf %s/blink*"%OUT_DIR)
ani.save(OUT_DIR+'blink.html')
time.sleep(1)
out=System("convert -delay 100 $(find %s -name 'blink*.png' |grep -v '04' |sort) %s"%(OUT_DIR,animfile))
print("Done.")
