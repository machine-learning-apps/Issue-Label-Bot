#!/bin/bash
# simple array list and loop for display

GPULIST=(0 1 2 3 4 5 6 7)

for GPU in ${GPULIST[@]}; do
    CUDA_VISIBLE_DEVICES=${GPU} wandb agent 7eiuq24o &
done
