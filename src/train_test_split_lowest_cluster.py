#!/usr/bin/env python

import argparse
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from copy import copy
from itertools import cycle
from pathlib import Path

from Bio import SeqIO


def validate_path(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path


def get_args():
    parser = argparse.ArgumentParser(
        description=r"""
        Split a fasta file into N groups with no more than 40% sequence homology.
        """,
        formatter_class=argparse.HelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--fasta",
        type=validate_path,
        required=True,
        help="Path to the FASTA file to be split.",
    )
    parser.add_argument(
        "-n", "--Number", type=int, default=11, help="Number of groups to split into."
    )
    parser.add_argument(
        "--cd-hit",
        type=str,
        required=False,
        default="cd-hit",
        help="Path to the cd-hit program.",
    )
    parser.add_argument(
        "-notmp", "--no_temp_dir", action="store_true", help="Don't use a temporary directory for intermediate files."
    )

    return parser.parse_args()


def call_cd_hit(fasta, cd_hit, no_tmp_dir=False):
    if no_tmp_dir:
        Path('cd_hit_temp').mkdir(exist_ok=True)
        file_path = str(Path('cd_hit_temp') / (str(fasta.name) + '_clustered'))
        cmd = (
            f"{cd_hit} -i {fasta} -o {file_path} -c 0.4 -n 2 -d 0 -M 0 -T 0 -sc 1"
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Running cd-hit with command: {cmd}")
        return file_path

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name
        cmd = (
            f"{cd_hit} -i {fasta} -o {temp_file_path} -c 0.4 -n 2 -d 0 -M 0 -T 0 -sc 1"
        )
        print(f"Running cd-hit with command: {cmd}")

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Writing cd-hit output to temporary file {temp_file_path}...")
        return temp_file_path


def hash_headers(fasta):
    hash_lookup = {}
    hashed_records = []

    print("Hashing headers...")
    for record in SeqIO.parse(fasta, "fasta"):
        hash_value = hash(record.seq)
        hash_lookup[str(hash_value)] = copy(record)

        record.id = str(hash_value)
        record.description = ""
        hashed_records.append(record)

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name
        print(f"Writing hashed records to temporary file {temp_file_path}...")
        SeqIO.write(hashed_records, temp_file_path, "fasta")

    return hash_lookup, Path(temp_file_path)


def fetch_clusters(cd_hit_output):
    print(f"Opening {cd_hit_output}")
    hash_pattern = re.compile("\d+\s\d+aa,\s>(?P<hash_str>-?[0-9]*)\.\.\.")

    with open(cd_hit_output + ".clstr") as file:
        file = file.read()
        clusters = file.split(">Cluster")[1:]

    print(f"Parsing {len(clusters)} clusters from cd-hit output")
    for cluster_number, cluster in enumerate(clusters):
        cluster = [x.strip() for x in cluster.split("\n") if x.strip() != ""][1:]
        hashes = [hash_pattern.match(line).group("hash_str") for line in cluster]
        print(f"\tFound {len(hashes)} sequences in cluster {cluster_number}")

        yield hashes


def lowest_split(outputs, expected_splits):
    if len(outputs) < expected_splits:
        return len(outputs.keys()) + 1

    min_size = min(len(v) for v in outputs.values())
    for key, records in outputs.items():
        if len(records) == min_size:
            return key


def main():
    args = get_args()

    hash_lookup, temp_file_path = hash_headers(args.fasta)

    # Call the cd-hit function with the temporary file
    cd_hit_output = call_cd_hit(temp_file_path, args.cd_hit, args.no_temp_dir)

    # Parse the cd-hit output file
    outputs = defaultdict(list)

    for hash_list in fetch_clusters(cd_hit_output):
        split_number = lowest_split(outputs, args.Number)
        print(f"\t\tAssigning cluster with {len(hash_list)} sequences to split # {split_number} ({args.fasta})")

        for hash_str in hash_list:
            original_record = hash_lookup[hash_str]
            outputs[split_number].append(original_record)

    # Write the output files
    print("Writing output files...")
    for key, records in outputs.items():
        output_file = f"{key}_{args.fasta.stem}.fasta"
        print(f"\tWriting {len(records)} records to {output_file}")
        SeqIO.write(records, output_file, "fasta")

    # Remove the temporary files after it's no longer needed
    os.remove(temp_file_path)
    os.remove(cd_hit_output)


if __name__ == "__main__":
    sys.exit(main())
