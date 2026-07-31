#!/bin/bash -l
#SBATCH -A uppmax2026-1-123
#SBATCH -M pelle
#SBATCH -p gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH -t 12:00:00
#SBATCH -J p2_eval_33b_bok
#SBATCH -o logs/p2_eval_33b_bok_%j.out
#SBATCH -e logs/p2_eval_33b_bok_%j.err

set -euo pipefail

PROJECT_DIR=/gorilla/proj/uppmax2026-1-123/uppmax2026-1-123/private/yaxj1/mt_oil_no_bokmal

source ~/miniconda3/etc/profile.d/conda.sh
conda activate /gorilla/proj/uppmax2026-1-123/uppmax2026-1-123/private/yaxj1/conda_envs/mt_old_clone

export HF_CACHE_DIR=/gorilla/proj/uppmax2026-1-123/uppmax2026-1-123/private/yaxj1/hf_cache
export HF_HOME=$HF_CACHE_DIR
export TRANSFORMERS_CACHE=$HF_CACHE_DIR
export HF_DATASETS_CACHE=$HF_CACHE_DIR
export TORCH_HOME=$HF_CACHE_DIR

mkdir -p logs

cd "$PROJECT_DIR"
python experiments/en_no_bokmal/c_evaluate.py --model bokmal --test bokmal --model-id nllb_3_3b
python experiments/en_no_bokmal/c_evaluate.py --model bokmal --test original --model-id nllb_3_3b
