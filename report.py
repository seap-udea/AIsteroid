
# coding: utf-8

# # AIsteroid
# [http://bit.ly/aisteroid](http://bit.ly/aisteroid)

# In[87]:


from aisteroid import *
get_ipython().run_line_magic('matplotlib', 'nbagg')


# ## Task: Compile information on the campaign

# In[88]:


if QIPY:
    CONF.SET_LIST="sets.list" ##List of image sets to compile information
    CONF.SET_LIST="sets-NEA.list" ##List of image sets to compile information
    CONF.SET_LIST="sets-jan2018.list" ##List of image sets to compile information
    CONF.CAMPAIGN="jan2018"
    CONF.VERBOSE=0
    CONF.OVERWRITE=1


# #### DO NOT TOUCH IF YOU ARE NOT SURE

# In[93]:


print0("*"*60+"\nGENERATING REPORT FOR SET LIST '%s'\n"%CONF.SET_LIST+"*"*60)

if not os.path.isfile(CONF.SET_LIST):
    error("Set list '%s' does not exist"%CONF.SET_LIST)

SET_LIST_NAME=CONF.SET_LIST.split("/")[-1].replace(".list","")
TEAMS_FILE=CONF.DATA_DIR+"sets/teams-%s.txt"%CONF.CAMPAIGN
CAMPS_FILE=CONF.DATA_DIR+"sets/campaign-%s.txt"%CONF.CAMPAIGN

CONF.REP_DIR="data/reports/"

REP_FILE=CONF.REP_DIR+SET_LIST_NAME+"-report.aia"
if os.path.isfile(REP_FILE):
    REP=pickle.load(open(REP_FILE,"rb"))
    sets=REP["sets"]
    allobjects=REP["allobjects"]
else:
    REP=dict()


# ### Read information on image sets

# In[90]:


print("Gathering information on image sets")

if not "sets" in REP.keys() or CONF.OVERWRITE:
    sets=pd.DataFrame()
    i=0
    allobjects=pd.DataFrame()
    for line in open(CONF.SET_LIST).readlines():
        if "#" in line:continue

        #Set name    
        set_name=line.strip()
        set_name=set_name.split("/")[-1].replace(".zip","")
        #if not "076" in set_name:continue
        print0("\tGetting information on image set %d '%s'"%(i,set_name))
        
        #Get the team
        out=System("grep %s %s"%(set_name,CAMPS_FILE),False)
        try:teamid=out[0].split()[0]
        except:teamid="ANONYMOUS"
        print1("\t\tTeam ID: %s"%teamid)

        out=System("grep %s %s"%(teamid,TEAMS_FILE),False)
        try:team=" ".join(out[0].split()[1:])
        except:team="ANONYMOUS"
        print1("\t\tTeam: %s"%team)

        #Read the aia file
        OUT_DIR=CONF.SCR_DIR+set_name+"/"
        if not os.path.isdir(OUT_DIR):
            print0("\t\tSet %s not yet unpacked. Skipping"%set_name)
            continue
        AIA_FILE=OUT_DIR+"%s.aia"%(set_name)
        if not os.path.isfile(AIA_FILE):
            print0("\t\tSet %s not yet analysed. Skipping"%set_name)
            continue

        AIA=pickle.load(open(AIA_FILE,"rb"))
        images=AIA["images"]
        nimgs=len(images)
        print1("\t\tNumber of images:",len(images))
        borders=AIA["borders"]
        print1("\t\tNumber of border points:",len(borders[0]))
        sources=AIA["sources"]
        print1("\t\tNumber of sources:",len(sources[sources.IMG==0]))
        objects=AIA["objects"]
        nobj=len(objects)
        print1("\t\tNumber of objects:",nobj)

        #Store information
        tset=pd.Series()

        #Basic information
        tset["set_name"]=set_name
        tset["teamid"]=teamid
        tset["team"]=team
        tset["date_ini"]=images[0]["obstime"]
        tset["date_end"]=images[-1]["obstime"]
        tset["time_ini"]=images[0]["unixtime"]
        tset["time_end"]=images[-1]["unixtime"]
        tset["duration"]=tset["time_end"]-tset["time_ini"]

        #Region covered by the image set
        ras=sources["RA"]
        des=sources["DEC"]
        tset["ra_center"]=ras.mean()
        tset["dec_center"]=des.mean()
        tset["ra_width"]=(ras.max()-ras.min())
        tset["dec_width"]=des.max()-des.min()

        #Read objects
        if nobj>0:
            obj_file=OUT_DIR+"photometry-%s.csv"%set_name
            if not os.path.isfile(obj_file):
                print1("\t\tObjects not detected yet. skipping")
                continue
            obj=pd.read_csv(obj_file)
            obj["set_name"]=set_name
            allobjects=allobjects.append(obj)

        #Append report
        sets=sets.append(tset,ignore_index=True)

        i+=1
        #if i>20:break
        #break

    #Save
    REP["sets"]=sets
    REP["allobjects"]=allobjects
    pickle.dump(REP,open(REP_FILE,"wb"))
    print0("%d image sets read"%i)
    print0("Done.")
else:
    print0("\tReport '%s' already generated"%SET_LIST_NAME)


# ### Generate ASCII table with image sets

# In[69]:


repfile=CONF.REP_DIR+SET_LIST_NAME+"-report.txt"
fr=open(repfile,"w")
bar="-"*(135+6)+"\n"
fr.write(bar)
fmt="|%-25s|%-50s|%-30s|%-30s|\n"
fr.write(fmt%("Set","Team","Date","RA,DEC"))
fr.write(bar)

for ind in sets.sort_values(by="date_ini").index:
    iset=sets.loc[ind]
    set_name=iset["set_name"]
    team="%s"%(iset["team"].strip()[:50]).encode("iso-8859-1")
    nobjs=len(np.unique(allobjects[allobjects.set_name==set_name].MOBJ.values))
    fr.write(fmt%(iset["set_name"],team,iset["date_ini"],
                  dec2sex(iset["ra_center"]/15,"string",":")+","+\
                  dec2sex(iset["dec_center"],"string",":")))
fr.write(bar)
fr.close()
out=System("cat %s"%repfile)


# ### Generate table with objects
