#!/bin/bash

# make sure the script will fail hard if any error is raised
set -e

# Start tracking time
SECONDS=0

# Set the path to write temporary files
temp_dir=$(mktemp -d)

# Print help message if requested
if [ "$1" == "-h" ]; then
    echo "This script will split the sequences in a .fasta/.faa file, cluster them 
using CD-Hit at 40% sequence identity with a word length of 2, split the 
clusters into 11 groups, and rebuild a fasta file for each of those
clusters.
"

    echo "Usage: `basename $0` <input_file> [--cd-hit <cd-hit_binary_path>]"
    echo ""
    echo "Arguments:"
    echo "    <input_file>: The path to the input .fasta/.faa file."
    echo "    --cd-hit <cd-hit_binary_path>: The path to the CD-Hit binary \
(optional, will use '/usr/local/bin/cd-hit' by default)."
    echo "    -h : Display this help message."
  exit 0
fi

# Check if the required argument is provided
if [ -z "$1" ]; then
    echo "Error: Please provide a path to a .fasta/.faa formatted file as the first \
    argument."
    exit 1
fi

# Check if the file exists
if [ ! -f "$1" ]; then
    echo "Error: The file '$1' does not exist."
    exit 1
fi

# Set the default binary path if not provided
binary_path="/usr/local/bin/cd-hit"

# Check if the --cd-hit flag is provided
if [ "$2" = "--cd-hit" ]; then
    # Check if the binary path is provided
    if [ -n "$3" ]; then
        binary_path="$3"
    else
        echo "Error: Please provide a valid binary path after the --cd-hit flag."
        exit 1
    fi
fi

# Check if the binary exists
if [ ! -x "$binary_path" ]; then
    echo "Error: The CD-Hit binary '$binary_path' does not exist or is not executable."
    exit 1
fi

echo "CD-Hit binary path: $binary_path"

# Set the MD5 tool to use
if command -v md5 2>&1 >/dev/null
    then
        md5cmd="md5"
    else
    if command -v md5sum 2>&1 >/dev/null
        then
            md5cmd="md5sum"
        else
            echo "Error: No MD5 command found."
            exit 1
    fi
fi
echo "Using MD5 command: $md5cmd"


# Setup the file names for each step
input_file_basename=$(basename $1)
input_file_class=${input_file_basename%.*}

echo "Input file: $input_file_basename"
echo "Input file class: $input_file_class"

hashed_fasta_file="$temp_dir/${input_file_class}.hashed.fasta"
hashed_fasta_file_clean="$temp_dir/${input_file_class}.hashed.clean.fasta"
hashed_fasta_file_lookup="$temp_dir/${input_file_class}.hashed.lookup.fasta"

md5_lookup_file="$temp_dir/MD5_lookup.tmp"


echo "Checking for existing output files to prevent overwrites..."
# Error out if cluster files exist
for counter in {1..11}; do
    if [ -f "$counter"_"$input_file_class".fasta ]; then
        echo "Error: "$counter"_"$input_file_class".fasta already exist. Please remove \
them before running this script."
        exit 1
    fi
done


# Create empty files
echo "" > "$md5_lookup_file"
echo "" > "$hashed_fasta_file"


echo "Hashing input file headers"
# Hash fasta file
while IFS= read -r line; do
    # Check if the line starts with ">"
    if [[ $line == ">"* ]]; then
        # Extract the sequence name
        sequence_name="${line:1}"

        # Calculate the MD5 hash
        md5_hash=$(echo -n "$sequence_name" | "$md5cmd" | awk '{print $1}')

        # Replace the line with the MD5 hash
        updated_line=">$md5_hash"

        # Write the MD5 hash and source string to the file
        echo "$md5_hash $sequence_name" >> "$md5_lookup_file"

        # Write the MD5 hash to the hashed fasta file
        echo "$updated_line" >> "$hashed_fasta_file"
    else
        # Write the sequence to the hashed fasta file
        echo "$line" >> "$hashed_fasta_file"
    fi

done < "$1"

echo "Cleaning up the hashed fasta file"
# Remove unnecessary newline characters
awk '!/^>/ { printf "%s", $0; n = "\n" } 
    /^>/ { print n $0; n = "" }
    END { printf "%s", n }
    ' "$hashed_fasta_file" > "$hashed_fasta_file_clean"

# Remove ALL newline characters for sequence lookup from hash later
awk '{if ($0 !~ /^>/) {print} \
    else {printf "%s ", $0}} \
    END {print ""}' \
    "$hashed_fasta_file_clean" > "$hashed_fasta_file_lookup"


# Run CD-Hit
echo "Running CD-Hit"
# Modify the $1 variable and edit the extension to be ".cdhit.fasta"
cdhit_fasta_file="$temp_dir"/"$input_file_class.cdhit.fasta"
$binary_path \
    -c 0.4 \
    -n 2 \
    -d 100 \
    -M 0 \
    -T 0 \
    -sc 1 \
    -sf 1 \
    -i "$hashed_fasta_file" \
    -o "$cdhit_fasta_file"

# cp test-data/collar.cdhit.fasta.clstr "$cdhit_fasta_file".clstr

# Split the CD-Hit output into chunk files
awk -v temp_dir="$temp_dir" \
    '/^>Cluster .*/ \
    {filename = temp_dir "/chunk" ++i ".txt"} \
    filename {print > filename}' \
    "$cdhit_fasta_file".clstr


echo "Parsing $(ls $temp_dir/chunk*.txt | wc -l | xargs) CD-Hit clusters"

# Loop chunk files (clusters) and rebuild fasta files
counter=1
for file in $(ls "$temp_dir"/chunk* | sort -V); do
    current_file="$counter"_"$input_file_class".fasta.incomplete
    echo "writing $(wc -l < $file | xargs) hashes from \
$(basename $file) to $current_file"

    # get only hash portions of the cluster
    grep -o ">[A-Za-z0-9]*\.\.\." "$file" | cut -c 2-33 | while read -r line; do
        # get the sequence name from the hash
        while read -r line2; do
            if [[ $line2 == "$line"* ]]; then 
                echo $line2 | cut -d " " -f 2- | sed 's/^/>/' >> "$current_file"
                break
            fi
        done < "$md5_lookup_file"

        # get the sequence from the hash
        while read -r line3; do
            if [[ $line3 == ">$line"* ]]; then
                echo "$line3" | cut -d " " -f 2- >> "$current_file"
                break
            fi
        done < "$hashed_fasta_file_lookup"
        sleep 0.000001

    done

    counter=$((counter+1))
    if (( counter > 11 )); then
        counter=1
    fi

done

# Clean up
rm -rf "$temp_dir"

echo "Marking fasta files as complete and adding line breaks"
for file in *.fasta.incomplete; do
    awk '{ if ($0 ~ /^>/) { print $0 } \
    else { while (length($0) > 80) \
    { print substr($0, 1, 80); $0 = substr($0, 81) } print $0 } }' \
    "$file" > "${file%.incomplete}"

    rm "$file"
done

echo "Done! Total runtime: $SECONDS seconds"
