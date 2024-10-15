#!/bin/bash

# make sure the script will fail hard if any error is raised
set -e

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
    echo "    --cd-hit <cd-hit_binary_path>: The path to the CD-Hit binary (optional, \
    will use '/usr/bin/cd-hit' by default)."
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
binary_path="/usr/bin/cd-hit"

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


# Hash fasta file
# Modify the $1 variable and edit the extension to be ".hashed.fasta"
hashed_fasta_file="${1%.*}.hashed.fasta"

# Open the file
while IFS= read -r line; do
    # Check if the line starts with ">"
    if [[ $line == ">"* ]]; then
        # Extract the sequence name
        sequence_name="${line:1}"

        # Calculate the MD5 hash
        md5_hash=$(echo -n "$sequence_name" | md5sum | awk '{print $1}')

        # Replace the line with the MD5 hash
        line=">$md5_hash"

        # Write the MD5 hash and source string to the file
        echo "$md5_hash $sequence_name" >> MD5_lookup.tmp

        # Write the MD5 hash to the hashed fasta file
        echo "$md5_hash" >> "$hashed_fasta_file"
    else
        # Write the sequence to the hashed fasta file
        echo "$line" >> "$hashed_fasta_file"
    fi

done < "$1"


# Run CD-Hit
# Modify the $1 variable and edit the extension to be ".cdhit.fasta"
cdhit_fasta_file="${1%.*}.cdhit.fasta"
$binary_path \
    -c 0.4 \
    -n 2 \
    -M 0 \
    -T 0 \
    -sc 1 \
    -sf 1 \
    -i "$hashed_fasta_file" \
    -o "$cdhit_fasta_file"


