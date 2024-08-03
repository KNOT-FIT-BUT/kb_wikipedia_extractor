#!/bin/bash

array[0]="core"
array[1]="person"
array[3]="country"
array[4]="settlement"

for i in "${array[@]}"
do
	out=`python testing/${i}_tests.py 2>&1`
	tail=`echo "$out" | tail -n 1`
	if [[ $tail -eq "OK" ]]; then
		echo "OK	[${i}]"
	else
		echo "FAIL	[${i}]"
		echo "$out"
	fi
done
