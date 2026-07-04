#!/bin/bash
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
export LIBRARY_PATH=$CONDA_PREFIX/lib:$LIBRARY_PATH

export FASTA_DIR=./fasta_dir
export DMS_DIR=./dms_dir
export OUTPUT_DIR=./
export PRECOMPUTED_ALIGNMENT_DIR=./alignments
export MMCIF_DIR=/mmcifs    # UPDATE with path to your mmcifs directory 

python3 predict_with_dmsfold2.py $FASTA_DIR \
  $DMS_DIR \
  $MMCIF_DIR \
  --output_dir $OUTPUT_DIR \
  --config_preset model_5_ptm \
  --openfold_checkpoint_path openfold/resources/dmsfold2_model_5_ptm.pt
  --model_device "cuda:0" \
  --data_random_seed 462093 \
  --use_precomputed_alignments $PRECOMPUTED_ALIGNMENT_DIR 
