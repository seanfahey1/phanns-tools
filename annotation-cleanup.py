#!/usr/bin/env python

import argparse
import re
import sys
from pathlib import Path

import toml
from Bio import SeqIO


def validate_path(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path


def get_args():
    parser = argparse.ArgumentParser(
        description="""
        Remove sequences from a FASTA file with description headers that match a list of keywords.
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
        "-c",
        "--config",
        type=validate_path,
        required=True,
        help="Path to the configuration file with 'terms' section.",
    )
    parser.add_argument(
        "--use",
        type=str,
        required=False,
        default="*",
        help="Keys in the config file to use, separated by commas",
    )
    parser.add_argument(
        "--ignore",
        type=str,
        required=False,
        help="Keys in the config file to ignore, separated by commas.",
    )
    parser.add_argument(
        "-o", "--output", type=str, required=True, help="Path to the output file."
    )

    return parser.parse_args()


def main():
    args = get_args()
    print(f"Parsing FASTA file: {args.fasta}")

    config = toml.load(args.config)

    print(f"Ignoring keys: {args.ignore}")
    ignore = args.ignore.split(",") if args.ignore else []

    if ignore != []:
        assert all(
            x in config["terms"] for x in ignore
        ), "Some ignore keys are not present in the config file."

    ignore_terms = [term for key in ignore for term in config["terms"][key]]

    if args.use == "*":
        all_keys = [x for x in config["terms"].keys() if x not in ignore]
    else:
        use = args.use.split(",")
        all_keys = [x for x in config["terms"].keys() if x not in ignore and x in use]
    terms_list = []

    for key in all_keys:
        for term in config["terms"][key]:
            if term not in ignore_terms:
                terms_list.append(term)

    print(f"Using keys: {all_keys}")
    print(f"Using terms: {terms_list}")

    keep = []
    discarded = []
    with open(args.fasta, "r") as handle:
        for record in SeqIO.parse(handle, "fasta"):
            match = re.search("(.*)(\[.*\])", record.description)

            if not match:
                record_without_species = record.description
            else:
                record_without_species = match.group(1)

            found = False
            for term in terms_list:
                if re.search(term, record_without_species, re.IGNORECASE):
                    print(
                        f"Removing {record.id} with description: {record.description}"
                    )
                    discarded.append(record)
                    found = True
                    break
            if not found:
                keep.append(record)

    SeqIO.write(keep, args.output, "fasta")
    SeqIO.write(discarded, Path(args.output).with_suffix(".discarded.fasta"), "fasta")
    print("Sequences removed successfully.")


if __name__ == "__main__":
    sys.exit(main())
