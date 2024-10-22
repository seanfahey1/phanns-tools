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
        "config",
        type=validate_path,
        required=True,
        help="Path to the configuration file with 'terms' section.",
    )
    parser.add_argument(
        "--ignore", type=str, required=False, help="Keys in the config file to ignore"
    )
    parser.add_argument(
        "-o", "--output", type=str, required=True, help="Path to the output file."
    )

    return parser.parse_args()


def main():
    args = get_args()
    config = toml.load(args.config)

    all_keys = [x for x in config["terms"].keys() if x != args.ignore]
    terms_list = []

    for key in all_keys:
        terms_list.extend(config["terms"][key])

    with open(args.fasta, "r") as handle:
        for record in SeqIO.parse(handle, "fasta"):
            for term in terms_list:
                if re.search(term, record.description, re.IGNORECASE):
                    print(
                        f"Removing {record.id} with description: {record.description}"
                    )
                    break
                else:
                    SeqIO.write(record, args.output, "fasta")


if __name__ == "__main__":
    sys.exit(main())
