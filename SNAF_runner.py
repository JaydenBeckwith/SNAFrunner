import os, sys
import pandas as pd
import numpy as np
import anndata as ad
import snaf
import tensorflow as tf

os.makedirs("assets", exist_ok=True)
print('SNAF OK, TF', tf.__version__)

df = pd.read_csv('count.noLocus.txt', index_col=0, sep='\t')
print(df.head())

db_dir = os.environ.get("data", "/db")

tcga_ctrl_db   = ad.read_h5ad(os.path.join(db_dir, 'controls', 'tcga_matched_control_junction_count.h5ad'))
gtex_skin_ctrl = ad.read_h5ad(os.path.join(db_dir, 'controls', 'gtex_skin_count.h5ad'))
add_control = {'tcga_control': tcga_ctrl_db, 'gtex_skin': gtex_skin_ctrl}

snaf.initialize(df=df, db_dir=db_dir, add_control=add_control)

jcmq = snaf.JunctionCountMatrixQuery(junction_count_matrix=df,cores=14,add_control=add_control,outdir='result')

sample_to_hla = pd.read_csv('optitype_summary.filtered.tsv',sep='\t',index_col=0)['hla'].to_dict()
hlas = [hla_string.split(',') for hla_string in df.columns.map(sample_to_hla)]

jcmq.run(hlas=hlas,outdir='./result')
snaf.JunctionCountMatrixQuery.generate_results(path='./result/after_prediction.p',outdir='./result')