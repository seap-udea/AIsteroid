campaign="colombia-jan2018"
echo -n > $campaign.txt
for i in $(seq 1 21)
do
    echo "Team $i"
    grupo=$(printf "%02d" $i)
    hfile="iasc$grupo.html"
    wget -O $hfile --user iasc --password iascsearch http://iasc.hsutx.edu/iasc/international/IASC_$grupo
    files=$(cat $hfile |sed -e "s/<br>/\n/gi" |grep "ps1" |awk -F">" '{print $2}' |sed -e "s/<\/A//gi")
    for file in $files
    do
	echo "IASC_$grupo $file" >> $campaign.txt
	wget -nc --user iasc --password iascsearch http://iasc.hsutx.edu/iasc/international/IASC_$grupo/$file
    done
    rm $hfile
done
