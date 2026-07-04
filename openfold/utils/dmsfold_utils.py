import os
from typing import Optional

import numpy as np
import pandas as pd
import torch


def build_df_enrich(
    sm_csv: str,
    dm_csv: str,
) -> pd.DataFrame:
    """
    Construct the intermediate dataframe used for enrichment scoring
    from single- and double-mutant DMS measurements.

    Parameters
    ----------
    sm_csv
        CSV containing single-mutant measurements.

    dm_csv
        CSV containing double-mutant measurements.

    Returns
    -------
    pd.DataFrame
        Dataframe containing all quantities needed to compute
        enrichment scores.
    """

    # -------------------------
    # Read input files
    # -------------------------

    sm = pd.read_csv(
        sm_csv,
        usecols=["mut_type", "ddG"],
    )

    dm = pd.read_csv(
        dm_csv,
        usecols=["mut_type", "ddG"],
    )

    # -------------------------
    # Single mutant table
    # -------------------------

    sm = (
        sm.rename(columns={"ddG": "sm_ddg"})
        .set_index("mut_type")
    )

    # -------------------------
    # Parse double mutant names
    # -------------------------

    m12 = dm["mut_type"].str.split(
        ":",
        n=1,
        expand=True,
    )

    dm["Mut1"] = m12[0]
    dm["Mut2"] = m12[1]

    dm["Res1"] = dm["Mut1"].str[:-1]
    dm["Res2"] = dm["Mut2"].str[:-1]

    # -------------------------
    # Build enrichment dataframe
    # -------------------------

    df = pd.DataFrame(
        {
            "Mutation": dm["Mut1"] + ":" + dm["Mut2"],
            "Res1": dm["Res1"],
            "Res2": dm["Res2"],
            "Res1:Res2": dm["Res1"] + ":" + dm["Res2"],
            "Mut1": dm["Mut1"],
            "Mut2": dm["Mut2"],
            "Mut1:Mut2": dm["Mut1"] + ":" + dm["Mut2"],
            "Mut1:Mut2 ddG": dm["ddG"].astype(np.float32),
        }
    )

    # -------------------------
    # Lookup single-mutant values
    # -------------------------

    df["Mut1 ddG"] = (
        sm.reindex(dm["Mut1"])["sm_ddg"]
        .to_numpy(dtype=np.float32)
    )

    df["Mut2 ddG"] = (
        sm.reindex(dm["Mut2"])["sm_ddg"]
        .to_numpy(dtype=np.float32)
    )

    return df

def label_extremes_in_ddg_grid(
    df: pd.DataFrame,
    x_col: str = "Mut1 ddG",
    y_col: str = "Mut2 ddG",
    score_col: str = "Mut1:Mut2 ddG",
    bin_size: float = 0.5,
    frac: float = 0.05,
    min_points_per_cell: int = 10,
    label_col: str = "label",
) -> pd.DataFrame:
    """
    Divide the single-mutant ΔΔG landscape into bins and label the
    highest- and lowest-scoring double mutants within each bin.

    The top and bottom fraction of measurements within each populated
    bin are labeled positive and negative, respectively.
    """

    out = df.copy()

    x_min = out[x_col].min()
    x_max = out[x_col].max()

    y_min = out[y_col].min()
    y_max = out[y_col].max()

    # Handle degenerate cases

    if (
        not np.isfinite(x_min)
        or not np.isfinite(x_max)
        or x_min == x_max
    ):
        out["is_top_in_cell"] = False
        out["is_bottom_in_cell"] = False
        out["is_labeled_in_cell"] = False
        out[label_col] = ""
        return out

    if (
        not np.isfinite(y_min)
        or not np.isfinite(y_max)
        or y_min == y_max
    ):
        out["is_top_in_cell"] = False
        out["is_bottom_in_cell"] = False
        out["is_labeled_in_cell"] = False
        out[label_col] = ""
        return out

    # Construct grid

    x_edges = np.arange(
        np.floor(x_min / bin_size) * bin_size,
        np.ceil(x_max / bin_size) * bin_size + bin_size,
        bin_size,
    )

    y_edges = np.arange(
        np.floor(y_min / bin_size) * bin_size,
        np.ceil(y_max / bin_size) * bin_size + bin_size,
        bin_size,
    )

    out["x_bin"] = pd.cut(
        out[x_col],
        bins=x_edges,
        include_lowest=True,
    )

    out["y_bin"] = pd.cut(
        out[y_col],
        bins=y_edges,
        include_lowest=True,
    )


    group_cols = ["x_bin", "y_bin"]

    out["cell_n"] = (
        out.groupby(group_cols)[score_col]
        .transform("size")
    )

    def _mark_group(g):

        if len(g) < min_points_per_cell:
            g["_top"] = False
            g["_bot"] = False
            return g

        lo = g[score_col].quantile(frac)
        hi = g[score_col].quantile(1.0 - frac)

        g["_bot"] = g[score_col] <= lo
        g["_top"] = g[score_col] >= hi

        return g

    out = (
        out.groupby(group_cols, group_keys=False)
        .apply(_mark_group)
    )

    labeled = out["_top"] | out["_bot"]

    out[label_col] = ""

    out.loc[labeled, label_col] = out.loc[
        labeled,
        "Mut1:Mut2",
    ]

    out["is_top_in_cell"] = out["_top"]
    out["is_bottom_in_cell"] = out["_bot"]
    out["is_labeled_in_cell"] = labeled

    return out.drop(columns=["_top", "_bot"])


def enrichment_scores_log_odds(
    df: pd.DataFrame,
    pair_cols=("pos1", "pos2"),
    pos_flag="is_top_in_cell",
    neg_flag="is_bottom_in_cell",
    min_n: int = 5,
    alpha: float = 1.0,
) -> pd.DataFrame:
    """
    Compute residue-pair enrichment scores using a smoothed log-odds ratio.

    enrichment_score = log(
        (k_pos + alpha) /
        (k_neg + alpha)
    )
    """

    grouped = df.groupby(
        list(pair_cols),
        dropna=False,
    )

    out = pd.DataFrame(
        {
            "n": grouped.size(),
            "k_pos": grouped[pos_flag].sum(),
            "k_neg": grouped[neg_flag].sum(),
        }
    ).reset_index()

    out = out[out["n"] >= min_n].copy()

    out = out[
        (out["k_pos"] + out["k_neg"]) > 0
    ].copy()

    out["enrichment_score"] = np.log(
        (out["k_pos"] + alpha)
        /
        (out["k_neg"] + alpha)
    )

    return out.sort_values(
        "enrichment_score",
        ascending=False,
    )


def df_enrich_to_enrichment_tensor(
    df_enrich: pd.DataFrame,
    seq_len: int,
    bin_size: float = 0.25,
    frac: float = 0.05,
    min_points_per_cell: int = 10,
    min_n: int = 5,
):
    """
    Convert an enrichment dataframe into an NxNx1 enrichment tensor.

    Parameters
    ----------
    df_enrich
        Output of build_df_enrich().

    seq_len
        Protein sequence length.

    Returns
    -------
    tensor : torch.Tensor
        Shape (seq_len, seq_len, 1)

    enrichment_table : pd.DataFrame
    """

    needed = [
        "Mut1 ddG",
        "Mut2 ddG",
        "Mut1:Mut2 ddG",
        "Res1",
        "Res2",
    ]

    df = df_enrich.dropna(subset=needed).copy()

    ###############################################################
    # Label enriched mutations
    ###############################################################

    labeled = label_extremes_in_ddg_grid(
        df,
        x_col="Mut1 ddG",
        y_col="Mut2 ddG",
        score_col="Mut1:Mut2 ddG",
        bin_size=bin_size,
        frac=frac,
        min_points_per_cell=min_points_per_cell,
        label_col="label",
    )

    ###############################################################
    # Extract residue indices
    ###############################################################

    labeled["pos1"] = (
        labeled["Res1"]
        .str.extract(r"(\d+)", expand=False)
        .astype(np.int32)
    )

    labeled["pos2"] = (
        labeled["Res2"]
        .str.extract(r"(\d+)", expand=False)
        .astype(np.int32)
    )


    ###############################################################
    # Compute enrichment scores
    ###############################################################

    enr = enrichment_scores_log_odds(
        labeled,
        pair_cols=("pos1", "pos2"),
        pos_flag="is_top_in_cell",
        neg_flag="is_bottom_in_cell",
        min_n=min_n,
        alpha=1.0,
    )

    ###############################################################
    # Construct tensor
    ###############################################################

    tensor = torch.zeros(
        (seq_len, seq_len),
        dtype=torch.float32,
    )

    i = torch.from_numpy(
        enr["pos1"].to_numpy(dtype=np.int64) - 1
    )

    j = torch.from_numpy(
        enr["pos2"].to_numpy(dtype=np.int64) - 1
    )

    values = torch.from_numpy(
        enr["enrichment_score"].to_numpy(dtype=np.float32)
    )

    mask = (
        (i >= 0)
        & (i < seq_len)
        & (j >= 0)
        & (j < seq_len)
    )

    i = i[mask]
    j = j[mask]
    values = values[mask]

    tensor[i, j] = values
    tensor[j, i] = values

    return tensor.unsqueeze(2), enr

def make_dms_tensor(
    sm_csv: str,
    dm_csv: str,
    sequence: str,
    bin_size: float = 0.25,
    frac: float = 0.05,
    min_points_per_cell: int = 10,
    min_n: int = 5,
):
    """
    Generate an NxNx1 enrichment tensor from single- and double-mutant
    DMS measurements.

    Parameters
    ----------
    sm_csv
        Path to the single-mutant CSV.

    dm_csv
        Path to the double-mutant CSV.

    sequence
        Amino acid sequence of the protein.

    Returns
    -------
    tensor : torch.Tensor
        Tensor of shape (L, L, 1), where L is the sequence length.

    enrichment_table : pd.DataFrame
        Residue-pair enrichment statistics.
    """

    df_enrich = build_df_enrich(
        sm_csv=sm_csv,
        dm_csv=dm_csv,
    )

    tensor, enrichment = df_enrich_to_enrichment_tensor(
        df_enrich=df_enrich,
        seq_len=len(sequence),
        bin_size=bin_size,
        frac=frac,
        min_points_per_cell=min_points_per_cell,
        min_n=min_n,
    )

    return tensor