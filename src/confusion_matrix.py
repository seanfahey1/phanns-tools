import argparse
import sys
from pathlib import Path

import numpy as np
import plotly.express as px
from plotly.io import to_html


def validate_path(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path


def get_args():
    parser = argparse.ArgumentParser(
        description=r"""
        Generate a confusion matrix graph from true and predicted class labels.
        """,
        formatter_class=argparse.HelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--csv_path",
        type=validate_path,
        required=True,
        help="Path to write the confusion matrix graph.",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        required=False,
        default="confusion_matrix.html",
        help="Path to write the confusion matrix graph.",
    )

    args = parser.parse_args()
    return args


def confusion_matrix(file_path, true_class, predicted_class):
    all_classes = list(set(true_class).union(set(predicted_class)))
    classes = {x: i for i, x in enumerate(sorted(all_classes))}

    matrix = np.zeros((len(classes), len(classes)))
    for true, pred in zip(true_class, predicted_class):
        matrix[classes[true]][classes[pred]] += 1

    row_sums = matrix.sum(axis=1)
    normalized_matrix = matrix / row_sums[:, np.newaxis]

    fig = px.imshow(
        normalized_matrix,
        x=list(classes.keys()),
        y=list(classes.keys()),
        title="Confusion Matrix - Recall",
        text_auto=".2f",
    ).update_layout(
        xaxis_title="Predicted Class",
        yaxis_title="True Class",
        width=800,
        height=800,
    )

    with open(file_path, "w") as output:
        output.write(to_html(fig, include_plotlyjs="cdn"))
    print(f"Confusion matrix graph written to {Path(file_path).absolute()}")


def print_statistics(true_class, predicted_class):
    all_classes = list(set(true_class).union(set(predicted_class)))
    correct = [true if true == pred else False for true, pred in zip(true_class, predicted_class)]

    for cls in all_classes:
        cls_support = sum([1 for x in true_class if x == cls])
        cls_correct = sum([1 for x in correct if x == cls])
        print(f"    Class: {cls} - Support: {cls_support} - Accuracy: {(cls_correct / cls_support):.4f}")

    accuracy = len([x for x in correct if x]) / len(correct)
    print(f"Overall Accuracy: {accuracy:.4f}")


def main():
    args = get_args()
    with open(args.csv_path, "r") as f:
        lines = f.readlines()[1:]
        true_class = [line.split(",")[0].strip() for line in lines]
        predicted_class = [line.split(",")[-1].strip() for line in lines]
    confusion_matrix(args.output_path, true_class, predicted_class)
    print_statistics(true_class, predicted_class)


if __name__ == "__main__":
    sys.exit(main())
