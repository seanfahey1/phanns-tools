#!/usr/bin/env python

import argparse
import sys
from pathlib import Path

from Bio import SeqIO
import random


def validate_path(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path


def get_args():
    parser = argparse.ArgumentParser(
        description=r"""
        Split a fasta file into N random sub-files.
        """,
        formatter_class=argparse.HelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--fasta",
        type=validate_path,
        required=True,
        help="Path to the FASTA file to be cleaned up.",
    )
    parser.add_argument(
        "-n", "--number", type=int, default=11, help="Number of groups to split into."
    )

    args = parser.parse_args()
    return args


def main():
    args = get_args()

    with open(args.fasta, "r") as f:
        records = list(SeqIO.parse(f, "fasta"))
        # Shuffle the records to ensure randomness
        random.shuffle(records)

        # Split the records into N sub-files
        sub_files = [[] for _ in range(args.number)]
        for i, record in enumerate(records):
            sub_files[i % args.number].append(record)

        # Write the sub-files
        for i, sub_file in enumerate(sub_files, 1):
            output_file = f"{i}_{args.fasta.stem}.fasta"
            print(f"\tWriting {len(sub_file)} records to {output_file}")
            SeqIO.write(sub_file, output_file, "fasta")

if __name__ == "__main__":
    sys.exit(main())
