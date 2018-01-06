IFS=","
for i in $(ls -m REPORT*)
do 
    fname=$(echo $i |tr -d '\n')
    name=$(echo $i |awk '{print $4}' |cut -f 1 -d. |tr -d '[:space:]')
    echo "Name: REPORT-$name"
    echo "Original: $fname"
    cp "$fname" REPORT-$name.txt
done
