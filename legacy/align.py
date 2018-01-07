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
#LOCAL CONFIGURATION
#######################################################
#Output directory
OUT_DIR=CONF.SCR_DIR+CONF.SET+"/"

#File to pickle analysis results
AIA=OUT_DIR+"analysis.aia"

#Observatory configuration file
CFG=[line.rstrip('\n') for line in open(CONF.SETS_DIR+CONF.CFG+".cfg")]

#######################################################
#LOADING PREVIOUS RESULTS
#######################################################
if not os.path.isfile(AIA):
    error("You have not performed the extraction procedure.")

print("Loading results...")
analysis=pickle.load(open(AIA,"rb"))
images=analysis["images"];nimgs=len(images)
allsources=analysis["allsources"]

#######################################################
#ALIGN
#######################################################
if images[1]["transform"]!=None and not CONF.OVERWRITE:
    print("Alignment completed")
else:
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1-FIND ALIGNMENT PARAMETERS
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Finding alignment transformation")
    print("\tReference image:",images[0]["file"])

    images[0]["qalign"]=1
    for i,image in enumerate(images[1:]):
        s=images[0]["data"]
        t=images[i+1]["data"]
        image["qalign"]=0

        print("\tTransformation for image ",image["file"])
        try:
            tr,(ta,sa)=aal.find_transforms(t,s)
            image["qalign"]=1
            print("\t\tAstroalign")
        except:
            tr,(ta,sa)=forceAlignment(allsources,i+1,i)
            image["qalign"]=0
            print("\t\tTraditional")

        image["transform"]=tr

        #Measure alignment
        ta,sa=matchSources(allsources[allsources.IMG==(i+1)][["X_IMAGE","Y_IMAGE"]],
                           allsources[allsources.IMG==i][["X_IMAGE","Y_IMAGE"]])
        sp=[]
        for j in range(ta.shape[0]):sp+=tr(ta[j,:]).tolist()
        sp=np.array(sp)
        print("\t\tAverage distance before alignment:",np.abs(sa-ta).mean())
        print("\t\tAverage distance after alignment:",np.abs(sa-sp).mean())

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #2-ALIGN POSITIONS
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Aligning source positions")
    for i,image in enumerate(images):

        file=image["file"]
        print("\tAligning image ",image["file"])
        data=rec2arr(image["sourcexxy"])
        xy=data[:,1:3]

        #By default no transformation
        xya=xy

        #Astroalign
        if image["qalign"]:
            if i>0:
                tr=image["transform"]
                xya=[]
                for j in range(xy.shape[0]):xya+=tr(xy[j,:]).tolist()
                xya=np.array(xya)

        #Traditional alignment
        else:
            xya=[]
            if image["qalign"]:
                for j in range(xy.shape[0]):xya+=tr(xy[j,:]).tolist()
            else:
                for j in range(xy.shape[0]):
                    xyr=xy[j,:]
                    for ia in range(i,0,-1):
                        tr=images[ia]["transform"]
                        xyr=tr(xyr).tolist()
                    xya+=xyr
            xya=np.array(xya)

        image["sourcexxy_aligned"]=xya

        if i>0:
            #Measure alignment
            ta,sa=matchSources(pd.DataFrame(rec2arr(images[i]["sourcexxy"])[:,1:3],
                                            columns=["X_IMAGE","Y_IMAGE"]),
                               pd.DataFrame(rec2arr(images[0]["sourcexxy"])[:,1:3],
                                            columns=["X_IMAGE","Y_IMAGE"]))
            print("\t\tAverage distance before alignment:",np.abs(sa-ta).mean())
            ta,sa=matchSources(pd.DataFrame(images[i]["sourcexxy_aligned"],
                                            columns=["X_IMAGE","Y_IMAGE"]),
                               pd.DataFrame(images[0]["sourcexxy_aligned"],
                                            columns=["X_IMAGE","Y_IMAGE"]))
            print("\t\tAverage distance after alignment:",np.abs(sa-ta).mean())

    print("\tDone.")

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #3-ADDING ALIGNED DATA TO ALL SOURCES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Adding aligned data to all sources...")
    print("Compiling all sources...")
    allsources=pd.DataFrame()
    for i,image in enumerate(images):
        srcxys=pd.DataFrame(image["sourcexxy"])
        srcals=pd.DataFrame(image["sourcexxy_aligned"],columns=["X_ALIGN","Y_ALIGN"])
        alls=pd.concat([srcxys,srcals],axis=1)
        
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
    #4-STORING RESULTS
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Saving alignment results...")
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
