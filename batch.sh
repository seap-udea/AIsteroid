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
# Batch execution
#######################################################
COMMON="VERBOSE=1"

if [ "x$1" != "x" ];then
    set=$1
else
    set=sets.list
fi

for file in $(cat $set |grep -v "#")
do
    #Get SET name
    set=$(basename $file |awk -F".zip" '{print $1}')
    echo
    echo "*****************************************************"
    echo "Processing set '$set'"
    echo "*****************************************************"
    echo 

    #Unpack
    python3.5 unpack.py "SET='$set'" $COMMON OVERWRITE=0 QPLOT=1

    #Extract
    python3.5 extract.py "SET='$set'" $COMMON OVERWRITE=0 DETECT_THRESH=3 QPLOT=1

    #Detect
    python3.5 detect.py "SET='$set'" $COMMON OVERWRITE=0 QPLOT=1

    #Astrometria
    python3.5 astrometria.py "SET='$set'" $COMMON OVERWRITE=0 QPLOT=1

    #Photometry
    python3.5 photometry.py "SET='$set'" $COMMON OVERWRITE=0 QPLOT=1
done
