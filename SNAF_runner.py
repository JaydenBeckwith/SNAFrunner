import os,sys
import pandas as pd
import numpy as np
import anndata as ad
import snaf
import tensorflow as tf
os.makedirs("assets", exist_ok=True)
print('SNAF OK, TF', tf.__version__)