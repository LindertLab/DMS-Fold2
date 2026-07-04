# DMS-Fold2

[![Weights](https://img.shields.io/badge/DMS--Fold2-Weights-green)](https://huggingface.co/LindertLab/DMS-Fold2)
[![Training Dataset](https://img.shields.io/badge/DMS--Fold2-Training--Dataset-green)](https://huggingface.co/datasets/LindertLab/DMS-Fold2-Training-Dataset)
[![Benchmark Dataset](https://img.shields.io/badge/DMS--Fold2-Benchmark--Dataset-yellow)](https://huggingface.co/datasets/LindertLab/DMS-Fold2-Benchmark-Dataset)

DMS-Fold2 is an extension of OpenFold that incorporates pairwise epistatic information from deep mutational scanning (DMS) experiments into protein structure prediction. The model integrates enrichment scores derived from single-mutant and double-mutant ΔΔG measurements into the pair representation through a learned embedding and introduces an auxiliary loss for predicting enrichment scores during training.

Currently, DMS-Fold2 supports thermodynamic stability (ΔΔG) measurements as input.

## Installation

DMS-Fold2 is built on OpenFold. Please see the [OpenFold documentation](https://openfold.readthedocs.io/en/latest/) for installation instructions and required sequence databases.

Pretrained DMS-Fold2 model weights are available on Hugging Face:

https://huggingface.co/LindertLab/DMS-Fold2

Specify the checkpoint during inference using

```bash
--openfold_checkpoint_path path/to/dmsfold2_model_5_ptm.pt
```

## Formatting DMS Input

DMS-Fold2 requires **two CSV files** for each protein:

- a single-mutant ΔΔG file
- a double-mutant ΔΔG file

The filenames should share the FASTA basename:

```
protein.fasta
protein_sm_dms.csv
protein_dm_dms.csv
```

### Single-mutant CSV

The CSV must contain the columns

```
mut_type,ddG
```

where `mut_type` is formatted as

```
A1G
```

meaning

- wild-type residue **A**
- residue position **1**
- mutated residue **G**

Example

```text
mut_type,ddG
A1G,-0.42
A1C,-0.13
A1D,0.81
...
```

### Double-mutant CSV

The double-mutant CSV must also contain

```
mut_type,ddG
```

where `mut_type` is formatted as

```
A1G:C2A
```

representing the simultaneous mutations

- A1G
- C2A

Example

```text
mut_type,ddG
A1G:C2A,-0.64
A1G:C2D,-0.11
A1G:C2F,0.92
...
```

## Usage
DMS-Fold requires a protein sequence FASTA file, CSV with dms data, and the databases used by OpenFold for MSA/template information. A directory containing fastas files, and a corresponding directory containing matching dms CSVs should be specified. CSVs should start with the same name as the fasta file, with addition of '_dms.csv'. 
 
```bash
python3 predict_with_dmsfold2.py \
    $INPUT_FASTA_DIR \
    $INPUT_DMS_DIR \
    $TEMPLATE_MMCIF_DIR \    
    --openfold_checkpoint_path openfold/resources/dmsfold_model_5_ptm.pt \
    --uniref90_database_path uniref90.fasta \
    --mgnify_database_path mgy_clusters_2018_12.fa \
    --pdb70_database_path pdb70/pdb70 \
    --uniclust30_database_path uniclust30/uniclust30_2018_08/uniclust30_2018_08 \
    --bfd_database_path bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt \
    --model_device "cuda:0" \
    --config_preset model_5_ptm
```
#### Required Arguments:
* `$INPUT_FASTA_DIR` — directory containing one FASTA file per target.

* `$INPUT_DMS_DIR` — directory containing

```
<protein>_sm_dms.csv
<protein>_dm_dms.csv
```

for every FASTA.

* `$TEMPLATE_MMCIF_DIR` — directory containing template mmCIF files used by OpenFold.

* `*_database_path` — OpenFold sequence databases.

* `--openfold_checkpoint_path` — path to the pretrained DMS-Fold2 checkpoint.

* `--config_preset model_5_ptm`

The use of MSA-subsampling can be specified with `--neff` and size-dependent neff can be specified with `--neff_size_dependent`

## Example
An example command with a provided fasta directory, dms directory, and precomputed alignments for 1PWT are located within the directory named 'example'. Expected outputs of relaxed and unrelaxed DMS-Fold predictions and feature pickle file are also provided. To obtain reproducible predictions, specify a fixed random seed using

```bash
--data_random_seed
```

## Network Weights
The weights can be found on the [DMS-Fold model repository](https://huggingface.co/LindertLab/DMS-Fold2) on huggingface.co. Once downloaded, the weights should be added to DMS-Fold/openfold/resources/. The path to the weights can be specified with `--openfold_checkpoint_path'.

## Citing this work
If you use the code or data in this package, please cite:

```bibtex
@Article{}
```
