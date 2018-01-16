#Common
baseurl="http://iasc.hsutx.edu/iasc/international"
user="iasc"
pass="iascsearch"
pref="IASC"

#Campaign
campaign="jan2018"
i=0

#Colombia
((i++))
campset[i]="colombia"
numteams[i]=$(seq 1 21)

#Nepal
((i++))
campset[i]="nepal"
numteams[i]=$(seq 22 31)

#Poland
((i++))
campset[i]="poland"
numteams[i]=$(seq 32 41)

#Haus
((i++))
campset[i]="haus"
numteams[i]="$(seq 42 49) $(seq 107 110)"

#Nuclio
((i++))
campset[i]="nuclio"
numteams[i]=$(seq 50 69)

#Common
((i++))
campset[i]="common"
numteams[i]="$(seq 70 106) $(seq 111 111)"

nset=$i

for iset in $(seq 1 $nset)
do
    camp=${campset[$iset]}
    campname="${campset[$iset]}-$campaign"

    echo "Downloading imagesets for campset '$campname'"

    echo -n > $campname.txt
    for i in ${numteams[$iset]}
    do
    	grupo=$(printf "%02d" $i)
    	echo "Team $grupo"
    	hfile="iasc$grupo.html"
    	wget -O $hfile --user $user --password $pass $baseurl/${pref}_$grupo
    	files=$(cat $hfile |sed -e "s/<br>/\n/gi" |grep "ps1" |awk -F">" '{print $2}' |sed -e "s/<\/A//gi")
    	for file in $files
    	do
    	    echo "IASC_$grupo $file" >> $campname.txt
    	    wget --random-wait --wait=1 -nc --user $user --password $pass $baseurl/IASC_$grupo/$file
    	done
    	rm $hfile
    	stime=$(((RANDOM % 10)+1))
    	echo "Waiting $stime seconds...";sleep $stime
    done
done
