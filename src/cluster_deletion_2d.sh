#!/bin/bash
set -e
set -o pipefail

# Check if cd-hit-2d is installed
if ! command -v cd-hit-2d &> /dev/null; then
    echo "Error: cd-hit-2d is not installed or not on PATH."
    exit 1
fi

mkdir -p tmp

# Clear tmp/tmp.fasta if it exists
if [ -f tmp/tmp.fasta ]; then
    rm tmp/tmp.fasta
fi

# Check if $1 is assigned
if [ -z "$1" ]; then
    echo "Usage: ./2d_cluster_deletion.sh <target_directory>"
    echo "This script will run cd-hit-2d @ 40%, wc=2 on each file in the given <target_directory>."
    echo "The outputs will be generated in the current working directory with the suffix '_removed_2d_40pct'."
    exit 1
fi

# Check if $1 is a valid directory
if [ ! -d "$1" ]; then
    echo "Error: $1 is not a valid directory."
    exit 1
fi

# Get an array of each file in the directory given by $1
fs=($(ls "$1"))

for f1 in ${fs[@]}; do
    f1_path="$1/$f1"

    for f2 in ${fs[@]}; do
        f2_path="$1/$f2"

        if [ "$f1" != "$f2" ]; then
            cat "$f2_path" >> tmp/tmp.fasta
            echo "added $f2 to database"
        else
        	echo "skipping $f1"
        fi;
    done;

    echo "Running cd-hit-2d on $f1";
    cd-hit-2d -c 0.4 -i tmp/tmp.fasta -i2 "$f1_path" -o $f1"_removed_2d_40pct" -M 0 -T 0
    rm tmp/tmp.fasta

    echo "Done with $f1"
    echo "---------------------------------"

done

echo "Cleaning up..."
rm -r tmp
echo "All done!"
