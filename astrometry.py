
# coding: utf-8

# # AIsteroid
# [http://bit.ly/aisteroid](http://bit.ly/aisteroid)

# In[1]:


from aisteroid import *
get_ipython().run_line_magic('matplotlib', 'nbagg')


# ## Task: Perform astrometry of images

# ### Choose the image set

# In[2]:


if QIPY:
    #listImages() ##See the list of imagesets
    #CONF.SET="example" ##Choose your preferred imageset
    #CONF.CFG="example" ##You choose your preferred observatory configuration (example.cfg)
    CONF.OVERWRITE=1 ##Overwrite all previous actions
    CONF.VERBOSE=1 ## Show all outputs


# #### DO NOT TOUCH IF YOU ARE NOT SURE

# In[12]:


#DO NOT MODIFY THIS LINES
print0("*"*60+"\nASTROMETRY OF IMAGE SET'%s'\n"%CONF.SET+"*"*60)
OUT_DIR=CONF.SCR_DIR+CONF.SET+"/"
CFG=[line.rstrip('\n') for line in open(CONF.SETS_DIR+CONF.CFG+".cfg")]
AIA=dict()
AIA_FILE=OUT_DIR+CONF.SET+".aia"
SET_FILE=CONF.SETS_DIR+CONF.SET+".zip"
PLOT_DIR=OUT_DIR+"plots/"
FLOG=open(OUT_DIR+"astrometry.log","a")
SYSOPTS=dict(qexit=[True,FLOG])
if not os.path.isfile(AIA_FILE):
    error("Set '%s' has not been unpacked"%CONF.SET)
else:
    System("cp "+CONF.INPUT_DIR+"analysis/* "+OUT_DIR)
    AIA=pickle.load(open(AIA_FILE,"rb"))
    images=AIA["images"]
    sources=AIA["sources"]
    borders=AIA["borders"]
    nimgs=len(images)


# ### Telescope and camera (detector) properties

# In[4]:


print0("Telescope & CCD Properties:")
if not "detector" in AIA.keys() or CONF.OVERWRITE:
    #Telescope and camera (detector) properties
    detector=dictObj(dict())
    detector.FOCAL=Config(CFG,"FocalLength") #mm
    detector.PW=Config(CFG,"PixelWide") #mm
    detector.PH=Config(CFG,"PixelHigh") #mm
    detector.SIZEX=images[0]["header"]["NAXIS1"]
    detector.SIZEY=images[0]["header"]["NAXIS2"]
    detector.PWD=np.arctan(detector.PW/detector.FOCAL)*RAD
    detector.PHD=np.arctan(detector.PW/detector.FOCAL)*RAD
    detector.PXSIZE=(detector.PWD+detector.PHD)/2
    
    
    AIA["detector"]=detector
    pickle.dump(AIA,open(AIA_FILE,"wb"))
else:
    print("\tDetector properties already extracted")
    AIA=pickle.load(open(AIA_FILE,"rb"))
    detector=AIA["detector"]

print0("\tFocal lenght (mm) :",detector.FOCAL)
print0("\tPixel size (x mm,y mm) :",detector.PW,detector.PH)
print0("\tImage size (x px,y px) :",detector.SIZEX,detector.SIZEY)
print0("\tPixel size (arcsec):",detector.PXSIZE/ARCSEC)
print0("\tCamera field (x deg,y deg) :",detector.SIZEX*detector.PWD,detector.SIZEY*detector.PHD)
print("\tDone.")


# ### Astrometry using astromery.net

# In[11]:


x="X_IMAGE"
y="Y_IMAGE"
cs=[x,y]

for i,image in enumerate(images):

    file=image["file"]
    header=image["header"]

    # Get bright stars
    imgsources=sources[sources.IMG==i]
    border=borders[i]    
    
    #Choose the first NREFSTARS far from defects
    nbright=0
    indbright=[]
    for ind in imgsources.index:
        dmin=(np.sqrt((imgsources.loc[ind,x]-border[:,0])**2+                      (imgsources.loc[ind,y]-border[:,1])**2)).min()
        if dmin<2*CONF.RADIUS:continue
        indbright+=[ind]
        nbright+=1
        if nbright>=CONF.NREFSTARS:break

    bright=imgsources.loc[indbright]
    sources.loc[indbright,"STAR"]=1
    nbright=len(bright)

    print("\t\tNumber of selected bright stars:",len(bright))
    
    # Read fits and replace with bright stars
    img=OUT_DIR+file+".fits"
    hdul=fits.open(img)
    data=hdul[0].data
    data=np.zeros_like(data)
    for ind in bright.index:
        data[int(bright.loc[ind,"X_IMAGE"]),int(bright.loc[ind,"Y_IMAGE"])]=255
    hdul[0].data=data
    hdul.writeto(OUT_DIR+"this-%d.fits"%i,overwrite=True)
    hdul.close()
    
    #GET COORDINATES
    ra=sex2dec(header["OBJCTRA"])*15
    dec=sex2dec(header["OBJCTDEC"])

    #ASTROMETRY.NET COMMAND
    print("Running astrometry over %s..."%file)
    opts=""
    opts+=" "+"--use-sextractor --sextractor-path "+CONF.SEX_DIR+"bin/sex"
    opts+=" "+"--no-plots"
    opts+=" "+"--ra %.7f --dec %.7f --radius 1"%(ra,dec)
    opts+=" "+"--guess-scale --overwrite"
    cmd=CONF.AST_DIR+"bin/solve-field "+opts+" "+"this-%d.fits"%i
    sys="cd "+OUT_DIR+";"+cmd
    out=System(sys,True)
    
    print("\tAstrometry processing successful")
    #break
    
print("Done.")


# In[41]:


print0("Task completed.")
FLOG.close()

