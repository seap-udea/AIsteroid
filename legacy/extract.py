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
# Extraction procedure
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
#RUN
#######################################################
if os.path.isfile(AIA) and not CONF.OVERWRITE:

    print("Loading astrometry results...")
    analysis=pickle.load(open(AIA,"rb"))
    images=analysis["images"]
    allsources=analysis["allsources"]
else:
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1-UNPACK THE IMAGE SET
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    setfile=CONF.SETS_DIR+CONF.SET+".zip"
    if not os.path.isfile(setfile):
        error("No set file '%s'"%setfile)
    out=System("rm -rf "+OUT_DIR)
    out=System("mkdir -p "+OUT_DIR)
    out=System("cp "+CONF.INPUT_DIR+"template/* "+OUT_DIR)
    out=System("unzip -j -o -d "+OUT_DIR+" "+setfile)
        
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #2-READ THE IMAGES
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
        im["zero"]=0
        images+=[im]
        hdul.close()
        f=open(OUT_DIR+"%s.head"%im["file"],"w")
        f.write(im["header"].tostring("\n"))
        f.close()
    if not len(images):
        print("No images provided.")
    print("\tDone.")

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #4-EXTRACTING SOURCES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("SEXtracting sources")
    for i,image in enumerate(images):
        file=image["file"]
        header=image["header"]
        #SEX COMMAND
        print("\tRunning SEXtractor over %s..."%file)
        opts=""
        opts+=" "+"-c asteroid.sex"
        cmd=CONF.SEX_DIR+"bin/sex "+opts+" "+file+".fits"
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
            image["sourcexxy_header"]=hdul[1].header
            image["sourcexxy"]=hdul[1].data
            image["xy"]=rec2arr(hdul[1].data)[:,2:5:2]
            hdul.close()
            print("\t\t%d sources saved."%len(image["sourcexxy"]))
    print("\tDone.")

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #4-COMPILING ALL SOURCES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Compiling all sources...")
    allsources=pd.DataFrame()
    for i,image in enumerate(images):
        srcxys=pd.DataFrame(image["sourcexxy"])
        alls=pd.concat([srcxys],axis=1)
        
        #Alignment attributes
        alls["IMG"]=i #In which image is this source
        alls["STAR"]=0 #Is this a star?
        alls["ALIGSET"]=0 #Alignment set

        #Detection attributes
        alls["OBJ"]=0 #To which object it belongs (detection procedure)
        alls["NIMG"]=1 #In how many images is the object present (detection procedure)
        alls["MOBJ"]=0 #To which moving object it belongs (detection procedure)
        allsources=allsources.append(alls)

    allsources.sort_values(by="MAG_BEST",ascending=True,inplace=True)
    allsources.reset_index(inplace=True)

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #5-STORING RESULTS
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Saving astrometry results...")
    analysis=dict(images=images,allsources=allsources)
    pickle.dump(analysis,open(AIA,"wb"))
    print("\tDone.")

print("Completed.")

if CONF.SUMMARY:
    print("Summary:")
    print("\tNumber of sources:",len(allsources))
    print("\tProperties recovered:",allsources.columns)
    print("\tSample:")
    print(allsources.head())
