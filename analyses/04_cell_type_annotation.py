# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.1
#   kernelspec:
#     display_name: Python [conda env:conda-2022-schneeberger-liver-scanpy]
#     language: python
#     name: conda-env-conda-2022-schneeberger-liver-scanpy-py
# ---

# %% [markdown]
# # Cell-type annotation

# %%
# %load_ext autoreload
# %autoreload 2

# %%
# ensure reproducibility -> set numba multithreaded mode
from nxfvars import nxfvars
from threadpoolctl import threadpool_limits
import os

cpus = nxfvars.get("cpus", 2)
os.environ["NUMBA_NUM_THREADS"] = str(cpus)
threadpool_limits(cpus)

# %%
import scanpy as sc
import scanpy_helpers as sh
import pandas as pd
import matplotlib.pyplot as plt

# %%
sc.settings.set_figure_params(figsize=(4, 4), frameon=False)

# %%
adata_path = nxfvars.get(
    "adata_path", "../data/results/03_scvi/artifacts/adata_scvi_doublet_filtered.h5ad"
)
artifact_dir = nxfvars.get("artifact_dir", "/home/sturm/Downloads/nmp-temp/")
marker_genes_path = nxfvars.get("marker_genes_path", "../tables/cell_type_markers.csv")

# %% [markdown]
# ## Load data

# %%
marker_genes = pd.read_csv(marker_genes_path)

# %%
ah = sh.annotation.AnnotationHelper(markers=marker_genes)

# %%
adata = sc.read_h5ad(adata_path)

# %%
sc.tl.leiden(adata, resolution=1)

# %%
pb = sh.pseudobulk.pseudobulk(adata, groupby=["patient_id", "leiden"], log_norm=True)

# %% [markdown]
# ## Plot marker genes

# %%
with plt.rc_context({"figure.figsize": (6, 6)}):
    sc.pl.umap(adata, color="leiden", legend_loc="on data", legend_fontoutline=1)

# %%
ah.plot_umap(adata, cmap="inferno")

# %% [markdown]
# ### What is cluster 25?
# -> Erythrocytes

# %%
sc.tl.rank_genes_groups(pb, groupby="leiden", groups=[25], method="wilcoxon")

# %%
with plt.rc_context({"figure.figsize": (12, 4)}):
    sc.pl.rank_genes_groups(pb, n_genes=60)

# %%
with plt.rc_context({"figure.figsize": (6, 6)}):
    sc.pl.umap(adata, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
ah.annotate_cell_types(
    adata,
    {
        "B cells": [20],
        "Cholangiocytes": [26],
        "Endothelial cells": [15],
        "Hepatocytes": [18],
        "Plasma cells": [24],
        "Progenitor cells": [21, 17],
        "Mast cells": [27],
        "Neutrophils": [6, 2, 1, 10, 13, 11, 7, 12, 14],
        "myeloid": [22, 23, 0, 3],
        "NKT cells": [4, 19, 8, 9, 5, 16, 28],
        "Erythrocytes": [25],
    },
)

# %% [markdown]
# ## myeloid compartment subclustering

# %%
adata_m = adata[adata.obs["cell_type"] == "myeloid", :].copy()

# %%
ah.reprocess_adata_subset_scvi(adata_m, leiden_res=0.3, n_neighbors=15)

# %%
ah.plot_dotplot(adata_m)

# %%
ah.plot_umap(adata_m, filter_cell_type=["Macro", "mono", "DC", "div"], cmap="inferno")

# %%
sc.pl.umap(adata_m, color="total_counts", vmax=20000)

# %%
with plt.rc_context({"figure.figsize": (6, 6)}):
    sc.pl.umap(adata_m, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
ah.annotate_cell_types(
    adata_m,
    {
        "cDCs": [6],
        "pDCs": [7],
        "Monocytes ⁄ Macrophages": [0, 1, 2, 3, 4],
        "potentially empty droplets": [5],
    },
)

# %%
ah.integrate_back(adata, adata_m)

# %% [markdown]
# ## NK/T compartment

# %%
adata_t = adata[adata.obs["cell_type"] == "NKT cells", :].copy()

# %%
ah.reprocess_adata_subset_scvi(adata_t, leiden_res=0.5)

# %%
ah.plot_dotplot(adata_t)

# %%
sc.pl.umap(adata_t, color=["total_counts"], vmax=20000)

# %%
ah.plot_umap(adata_t, filter_cell_type=["div", "T cell", "NK"], cmap="inferno")

# %%
with plt.rc_context({"figure.figsize": (6, 6)}):
    sc.pl.umap(adata_t, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
ah.annotate_cell_types(
    adata_t,
    {
        # 7 is NK dividing, but we do not annotate this for this dataset
        # 0 and 1/6 are different subtypes of NK cells. We don't annotate this either for now.
        "NK cells": [7, 0, 1, 6],
        "T cells CD4": [3],
        "NKT cells": [5],
        "T cells CD8": [2, 4, 8],
        "potentially empty droplets": [9],
    },
)

# %%
ah.integrate_back(adata, adata_t)

# %% [markdown]
# ## Remove spurious cell-types and save results

# %%
adata = adata[
    ~adata.obs["cell_type"].isin(["potentially empty droplets", "Erythrocytes"]), :
]

# %%
sc.tl.umap(adata)

# %%
sc.pl.umap(adata, color="cell_type")

# %% [markdown]
# ## Coarse cell-type annotation

# %%
adata.obs["cell_type_coarse"] = [
    "T cells" if "T cells" in x else x for x in adata.obs["cell_type"]
]

# %%
sc.pl.umap(adata, color="cell_type_coarse")

# %%
ah.plot_dotplot(adata, groupby="cell_type")

# %%
adata.write_h5ad(f"{artifact_dir}/adata_cell_types.h5ad")
