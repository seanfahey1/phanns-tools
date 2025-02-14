import argparse
import sys
from pathlib import Path
from subprocess import run


def validate_path(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return str(path.resolve())


def validate_program(program):
    if run(["which", program]).returncode != 0:
        raise FileNotFoundError(f"Program not found: {program}")
    return program


def get_args():
    parser = argparse.ArgumentParser(
        description=r"""
        Remove sequences in each .fasta file in the target directory if the sequence
        shares >=40% sequence homology with a word length of 2 when compared to each
        sequence in the rest of the files combined.
        """,
        formatter_class=argparse.HelpFormatter,
    )
    parser.add_argument(
        "-d",
        "--target_dir",
        type=validate_path,
        required=True,
        help="Path to the FASTA file to be cleaned up.",
    )

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    print(args)

    script_path = Path(__file__).parent / "cluster_deletion_2d.sh"
    run([str(script_path), args.target_dir])


if __name__ == "__main__":
    sys.exit(main())
