
# coding: utf-8

# # AIsteroid
# [http://bit.ly/aisteroid](http://bit.ly/aisteroid)

# In[1]:


from aisteroid import *
get_ipython().run_line_magic('matplotlib', 'nbagg')


# ## Task: Uncompress and read the image set

# ### Choose the image set

# In[4]:


if QIPY:
    #listImages() ##See the list of imagesets
    #CONF.SET="example" ##Choose your preferred imageset
    #CONF.CFG="example" ##You choose your preferred observatory configuration (example.cfg)
    CONF.OVERWRITE=1 ##Overwrite all previous actions
    CONF.VERBOSE=1 ## Show all outputs


# #### DO NOT TOUCH IF YOU ARE NOT SURE

# In[5]:


#DO NOT MODIFY THIS LINES
print0("*"*60+"\nUNPACKING SET '%s'\n"%CONF.SET+"*"*60)

SET_FILE=CONF.SETS_DIR+CONF.SET+".zip"
if not os.path.isfile(SET_FILE):
    error("No set file '%s'"%SET_FILE)

OUT_DIR=CONF.SCR_DIR+CONF.SET+"/"
CFG=[line.rstrip('\n') for line in open(CONF.SETS_DIR+CONF.CFG+".cfg")]

PLOT_DIR=OUT_DIR+"plots/"

ELOG=open("errors.log","a")
SYSOPTS=dict(qexit=[True,ELOG])

AIA=dict()
AIA_FILE=OUT_DIR+CONF.SET+".aia"


# ### Unpack the images

# In[6]:


print0("Unpacking images of set %s"%(CONF.SET))
if not os.path.isdir(OUT_DIR) or CONF.OVERWRITE:
    out=System("rm -rf "+OUT_DIR,**SYSOPTS)
    out=System("mkdir -p "+OUT_DIR,**SYSOPTS)
    out=System("mkdir -p "+PLOT_DIR,**SYSOPTS)
    out=System("cp "+CONF.INPUT_DIR+"analysis/* "+OUT_DIR)
    out=System("unzip -j -o -d "+OUT_DIR+" "+SET_FILE,**SYSOPTS)
    pickle.dump(AIA,open(AIA_FILE,"wb"))
else:
    print0("\tAlready unpacked.")
    AIA=pickle.load(open(AIA_FILE,"rb"))

FLOG=open(OUT_DIR+"unpack.log","a")
SYSOPTS["qexit"][1]=FLOG
print0("\tDone.")


# ### Read the images

# In[14]:


images=[]

if not "images" in AIA.keys() or CONF.OVERWRITE:

    print0("Reading images")
    for img in sorted(glob.glob(OUT_DIR+"*.fits")):

        #Dictionary to store image information
        image=dict()
        image["file"]=img.split("/")[-1].replace(".fits","")

        print0("\tReading image %s"%(image["file"]))


        #Open fits image
        hdul=fits.open(img)

        #Get basic information
        image["header"]=hdul[0].header
        image["data"]=hdul[0].data

        #Example of how the information stored in the header is recovered
        image["obstime"]=hdul[0].header["DATE-OBS"]
        image["unixtime"]=date2unix(image["obstime"])
        FLOG.write(image["file"]+":"+str(image["obstime"])+":"+str(image["unixtime"])+"\n")

        #Close fits image
        hdul.close()

        #Save a plain data
        f=open(OUT_DIR+"%s.head"%image["file"],"w")
        f.write(image["header"].tostring("\n"))
        f.close()

        #Add image to list of images
        images+=[image]
        #if not CONF.QSAVE:System("rm -r %s"%img)

    print("\tDone.")
    nimgs=len(images)
    print("Number of images: %d"%nimgs)
    AIA["images"]=images
    pickle.dump(AIA,open(AIA_FILE,"wb"))
    
else:
    print("Images already read.")
    AIA=pickle.load(open(AIA_FILE,"rb"))
    images=AIA["images"]
    nimgs=len(images)
print0("\tDone.")
FLOG.flush()


# ### Show the images

# In[15]:


plotfile=PLOT_DIR+"cascade-%s.png"%CONF.SET
if CONF.QPLOT:
    plt.ioff() ##Comment to see interactive figure

    print0("Showing images in cascade")
    if not os.path.isfile(plotfile) or CONF.OVERWRITE:

        ncols=2
        nrows=int(nimgs/ncols)

        #Area of plotting
        fig,axs=plt.subplots(nrows,ncols,sharex=True,sharey=True,figsize=(7,7))

        #Common options for plotting
        imgargs=dict(cmap='gray_r',vmin=0,vmax=500)

        for i,ax in enumerate(mat2lst(axs)):
            ax.imshow(images[i]["data"],**imgargs)
            ax.axis("off")
            otime=images[i]["header"]["DATE-OBS"]
            ax.set_title(images[i]["file"]+"\n"+"Time:"+otime,fontsize=8,position=(0.5,1.0))

        fig.tight_layout()
        waterMark(axs[0,1])
        fig.savefig(plotfile)
    else:
        if CONF.QPLOT:print0("\tImage '%s' already generated."%plotfile)
    print0("\tDone.")
Image(filename=plotfile)


# ### Detect image defects

# In[33]:


print0("Detecting borders and image defects")

if not "borders" in AIA.keys() or CONF.OVERWRITE:

    rsamp=CONF.BORDERPREC
    csamp=CONF.BORDERPREC
    borders=[]
    for i,image in enumerate(images):
    
        print1("\tDetecting borders in image %d"%i)
        #Sweep rows
        qdetect=1
        border=[]
        data=image["data"]
        nrows,ncols=data.shape
        for row in range(rsamp,nrows,rsamp):
            line=data[row,:]
            for col in range(csamp,ncols,csamp):
                vstd=line[col:col+csamp].std()
                if vstd<1:
                    if qdetect:
                        border+=[[col-csamp,row]]
                        qdetect=0
                else:
                    if not qdetect:
                        border+=[[col+csamp,row]]
                        qdetect=1
        border+=[[row,col]]

        #Sweep columns
        qdetect=1
        for col in range(csamp,ncols,csamp):
            column=data[:,col]
            for row in range(rsamp,nrows,rsamp):
                vstd=column[row:row+csamp].std()
                if vstd<1:
                    if qdetect:
                        border+=[[col,row-rsamp]]
                        qdetect=0
                else:
                    if not qdetect:
                        border+=[[col,row+rsamp]]
                        qdetect=1
        border+=[[row,col]]
        border=np.array(border)
        print1("\tNumber of border points:",len(border))
        FLOG.write("Border points in image %d: %d\n"%(i,len(border)))

        borders+=[border]
        
    AIA["borders"]=borders
    pickle.dump(AIA,open(AIA_FILE,"wb"))
else:
    print("Borders already detected.")
    borders=AIA["borders"]

print("\tDone.")
FLOG.flush()


# ### Showing borders and defects

# In[34]:


plotfile=PLOT_DIR+"borders-%s.png"%CONF.SET

if CONF.QPLOT:
    plt.ion() ##Comment to see interactive figure

    print0("Showing borders and defects of images")
    if not os.path.isfile(plotfile) or CONF.OVERWRITE:

        ncols=2
        nrows=int(nimgs/ncols)

        #Area of plotting
        fig,axs=plt.subplots(nrows,ncols,sharex=True,sharey=True,figsize=(7,7))

        #Common options for plotting
        imgargs=dict(cmap='gray_r',vmin=0,vmax=500)

        for i,ax in enumerate(mat2lst(axs)):
            border=borders[i]
            ax.imshow(images[i]["data"],**imgargs)
            ax.plot(border[:,0],border[:,1],'ro',ms=0.5)
            ax.axis("off")
            otime=images[i]["header"]["DATE-OBS"]
            ax.set_title(images[i]["file"]+"\n"+"Time:"+otime,fontsize=8,position=(0.5,1.0))
            
        fig.tight_layout()
        waterMark(axs[0,1])
        fig.savefig(plotfile)
    else:
        if CONF.QPLOT:print0("\tImage '%s' already generated."%plotfile)
    print0("\tDone.")
Image(filename=plotfile)


# ### Blink all image

# In[7]:


plotfile="%s/blinkall-%s.gif"%(PLOT_DIR,CONF.SET)
if CONF.QPLOT:
    plt.ioff() ##Comment to see interactive figure

    print0("Blink images (all)")
    if (not os.path.isfile(plotfile) or CONF.OVERWRITE) and CONF.QPLOT:

        #Basic figure
        fig=plt.figure(figsize=(8,8))
        imgargs=dict(cmap='gray_r',vmin=0,vmax=700)
        im=plt.imshow(images[0]["data"],animated=True,**imgargs)
        tm=plt.title("Set %s, Image 0: "%CONF.SET+images[0]["obstime"],fontsize=10)
        waterMark(fig.gca())
        plt.axis("off")
        fig.tight_layout()

        def updatefig(i):
            iimg=i%nimgs
            im.set_array(images[iimg]["data"])
            tm.set_text("Set %s, Image %d: "%(CONF.SET,iimg)+images[iimg]["obstime"])
            return im,

        #Create animation
        ani=animation.FuncAnimation(fig,updatefig,frames=range(nimgs),
                                    interval=1000,repeat_delay=1000,
                                    repeat=True,blit=True)
        saveAnim(ani,PLOT_DIR,plotfile)
    else:
        if CONF.QPLOT:print0("\tImage '%s' already generated."%plotfile)
    print0("\tDone.")
Image(filename=plotfile)


# In[8]:


plotfile="%s/blink-%s.gif"%(PLOT_DIR,CONF.SET)
if CONF.QPLOT:
    plt.ioff() ##Comment to see interactive figure

    print0("Blink images (sections)")
    if (not os.path.isfile(plotfile) or CONF.OVERWRITE) and CONF.QPLOT:    

        data=images[0]["data"]
        nrows,ncols=data.shape
        drows=int(nrows/3)
        dcols=int(ncols/3)
        ratio=(1.0*drows)/dcols

        fig=plt.figure(figsize=(8,8*ratio*9),)

        axs=[]
        axs+=[fig.add_subplot(10,1,1)]
        axs+=[fig.add_subplot(10,1,2)]
        for i in range(8):axs+=[fig.add_subplot(10,1,3+i,sharex=axs[1],sharey=axs[1])]


        ax=axs[0]
        imgargs=dict(cmap='gray_r',vmin=0,vmax=700)
        ims00=ax.imshow(data,animated=True,**imgargs)
        ax.axis("off")
        ax.set_adjustable('box-forced')
        ax.text(0.98,0.98,"All",color='b',transform=ax.transAxes,ha='right',va='top')

        n=1
        ims=[]
        txs=[]
        for i in range(3):
            im=[]
            tx=[]
            for j in range(3):
                irow=i*drows
                icol=j*dcols
                subimg=data[irow:irow+drows,icol:icol+dcols]

                axs[0].add_patch(pat.Rectangle([icol,irow],dcols,drows,color='r',fc='None'))
                axs[0].text(icol+dcols/2,irow+drows/2,"%d,%d"%(i,j),color='b',ha='center',va='center')

                ax=axs[n]
                im+=[ax.imshow(subimg,animated=True,**imgargs)]
                tx+=[ax.text(0.02,0.98,"Image 0",color='r',transform=ax.transAxes,ha='left',va='top')]
                ax.text(0.98,0.98,"%d,%d"%(i,j),color='b',transform=ax.transAxes,ha='right',va='top')
                ax.axis("off")
                ax.set_xlim((0,dcols))
                ax.set_ylim((drows,0))
                ax.set_adjustable('box-forced')
                n+=1
            ims+=[im]
            txs+=[tx]
        fig.tight_layout()

        def updatefig(i):
            iimg=i%nimgs
            data=images[iimg]["data"]
            ims00.set_array(data)
            for i in range(3):
                for j in range(3):
                    irow=i*drows
                    icol=j*dcols
                    subimg=data[irow:irow+drows,icol:icol+dcols]
                    ims[i][j].set_array(subimg)
                    txs[i][j].set_text("Image %d"%iimg)
            return ims00,

        #Create animation
        ani=animation.FuncAnimation(fig,updatefig,frames=range(nimgs),
                                    interval=1000,repeat_delay=1000,
                                    repeat=True,blit=True)
        saveAnim(ani,PLOT_DIR,plotfile)
    else:
        print0("\tImage '%s' already generated."%plotfile)
    print0("\tDone.")    
Image(filename=plotfile)


# In[35]:


print("Task completed.")
FLOG.close()


# In[42]:


CONF.SET="/home/astrometry/iasc/data/sets/ps1-20180108_3_set013.zip"


# In[43]:


CONF.SET.split("/")[-1].replace(".zip","")

