import argparse
import subprocess
from pathlib import Path

from Bio import SeqIO


def validate_filepath(filepath):
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")
    return path


def get_args():
    parser = argparse.ArgumentParser(
        description="""
        Merge two fasta files, identify clusters of similar proteins, and delete all 
        sequences from `target` fasta file if they cluster with a sequence from the 
        `reference` file. 
        """,
        formatter_class=argparse.HelpFormatter,
    )

    parser.add_argument(
        "-t",
        "--target",
        type=validate_filepath,
        required=True,
        help="Target fasta file to be filtered (usually OTH class)",
    )
    parser.add_argument(
        "-r",
        "--reference",
        type=validate_filepath,
        required=True,
        help="Reference fasta file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help='Output fasta file. Default: target file with suffix ".filtered"',
    )

    args = parser.parse_args()

    if args.output is None:
        args.output = args.target.with_suffix(".filtered")

    return args


def main():
    args = get_args()

    target_hash_lookup = {}
    all_records = []

    # combine files with hashed headers
    for record in SeqIO.parse(args.target, "fasta"):
        file_stem = args.target.stem

        seq_hash = str(hash(record.seq))
        target_hash_lookup[seq_hash] = (record.description, record.seq)
        record.description = f"{file_stem}@@@{seq_hash}"
        all_records.append(record)

    for record in SeqIO.parse(args.reference, "fasta"):
        file_stem = args.reference.stem

        seq_hash = str(hash(record.seq))
        record.description = f"{file_stem}@@@{seq_hash}"
        all_records.append(record)

    # write combined file
    with open("combined.fasta", "w") as f:
        SeqIO.write(all_records, f, "fasta")

    # cluster sequences
    cmd = """cd-hit
        -i combined.fasta
        -o combined.fasta.clstr
        -c 0.4
        -n 2
        -d 0
        -M 0
        -T 0
        -sc 1
        -sf 1
    """


    results = subprocess.run(cmd, shell=True, universal_newlines=True, check=True)
    print(results.stdout)


if __name__ == "__main__":
    main()
