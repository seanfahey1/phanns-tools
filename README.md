# phanns-tools
`phanns-tools` is a collection of python and bash scripts used to structure data prior
to training PhANNs 3.0 models.

- [phanns-tools](#phanns-tools)
      - [Installation](#installation)
    - [OTH-cluster-deletion](#oth-cluster-deletion)
    - [train-test-split.sh](#train-test-splitsh)
    - [annotation\_cleanup](#annotation_cleanup)
    - [train\_test\_split\_random](#train_test_split_random)

#### Installation
```
git clone https://github.com/seanfahey1/phanns-tools.git
cd phanns-tools
pip install .
```

### OTH-cluster-deletion
`OTH_cluster_deletion` is used to remove any sequences from a target `fasta` file if
it clusters with any file in the `reference` dataset.

### train-test-split.sh
`train_test_split.sh` is used to split an amino acid `.fasta` file into 11 distinct
groups using the following method:
- cluster file at 40% sequence identity with a word length of 2 (using `cd-hit`)
- split the resulting clusters into 11 groups
- rebuild the fasta file for each clustered protein

### annotation_cleanup
`annotation-cleanup` cleans up cross class annotation leakage by supplying a list
of target classes and their corresponding class-specific terms in an 
`annotation-config.toml` file.

The structure of the file is: 
```
["terms"]
Class1 = ["term1", "term2", "term3", ...]
Class2 = ["term4", "term5", ...]
...
```
_A sample annotation config file can be found at src/annotation-config.toml_

### train_test_split_random
`train-test-split-random` is used to randomly split a `.fasta` file into N distinct 
sub-files with even numbers of proteins in each file.
