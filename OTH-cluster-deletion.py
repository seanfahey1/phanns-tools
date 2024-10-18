#!/usr/bin/env python

import argparse
import re
import subprocess
from datetime import datetime
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
    parser.add_argument(
        '-jid',
        '--job_id',
        type=str,
        default=None,
        help='Optional job ID to be used in intermediate files. Default: current date and time',
    )

    args = parser.parse_args()

    if args.output is None:
        args.output = args.target.with_suffix(".filtered")
    if args.job_id is None:
        args.job_id = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    return args


def cd_hit(input_file, output_file, **kwargs):
    cmd = f"""cd-hit\
        -i {input_file}\
        -o {output_file}\
        -c {kwargs.get("c", 0.4)}\
        -n {kwargs.get("n", 2)}\
        -d 0\
        -M 0\
        -T 0\
        -sc 1\
        -sf 1
    """

    results = subprocess.run(cmd, shell=True, universal_newlines=True, check=True)
    return results


def digest_clusters(cluster_file_path):
    assert (
        cluster_file_path.is_file()
    ), f"File not found: {cluster_file_path}. CD-hit may have not run properly"

    with open(cluster_file_path) as f:
        clusters = f.read().split(">Cluster")[1:]
        clusters = [x for x in clusters if x.strip() != ""]

    for cluster in clusters:
        # clean up cluster
        cluster_lines = [x.strip() for x in cluster.split("\n") if x.strip() != ""][1:]

        # pull just descriptions
        descriptions = []
        for line in cluster_lines:
            try:
                descriptions.append(str(re.search("\d+aa,\s+>(.*@@@-?\d*)\.\.\.", line).group(1)))
            except AttributeError:
                print(cluster)
                print("")
                print(line)
                raise AttributeError

        # skip non-mixed clusters
        source_files = [x.split("@@@")[0] for x in descriptions]
        if len(set(source_files)) == 1:
            continue

        for line in descriptions:
            source_file, seq_hash = line.split("@@@")
            yield source_file, seq_hash


def write_dict_to_fasta(d, output_file):
    with open(output_file, "w") as f:
        for description, seq in d.values():
            seq_80 = re.sub("(.{64})", "\\1\n", seq, 0, re.DOTALL)
            f.write(f">{description}\n{seq_80}\n")


def main():
    args = get_args()

    target_hash_lookup = {}
    removed_records = {}
    all_records = []

    # combine files with hashed headers
    for record in SeqIO.parse(args.target, "fasta"):
        file_stem = args.reference.stem

        seq_hash = str(hash(record.seq))
        record.id = f"{file_stem}@@@{seq_hash}"
        record.name = ""
        record.description = ""
        all_records.append(record)

    for record in SeqIO.parse(args.reference, "fasta"):
        file_stem = args.reference.stem

        seq_hash = str(hash(record.seq))
        record.id = f"{file_stem}@@@{seq_hash}"
        record.name = ""
        record.description = ""
        all_records.append(record)

    # write combined file
    with open(f"{args.job_id}_combined.fasta", "w") as f:
        SeqIO.write(all_records, f, "fasta")

    # cluster sequences
    results = cd_hit(f"{args.job_id}_combined.fasta", f"{args.job_id}_combined_out.fasta")

    for source_file, seq_hash in digest_clusters(
        Path(f"{args.job_id}_combined_out.fasta.clstr")
    ):
        if source_file == args.target.stem:
            if seq_hash not in target_hash_lookup:
                raise ValueError(
                    f"Hash from {source_file} not found in target lookup: {seq_hash}"
                )

            removed_records[seq_hash] = target_hash_lookup.pop(seq_hash)

    write_dict_to_fasta(target_hash_lookup, args.output)
    write_dict_to_fasta(
        removed_records, f"{args.output.with_name(args.output.stem + '_removed.fasta')}"
    )


if __name__ == "__main__":
    main()
