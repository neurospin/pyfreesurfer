##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


"""
Modules that provides features manipulation tools.
"""

# System import
from __future__ import print_function
import os

# Third party import
import scipy.cluster.hierarchy
import matplotlib.pyplot as plt
from sklearn import preprocessing


def sort_features(features, outdir, name, header=None, verbose=0):
    """ Sort a feature array using a Ward hierachical clustering analysis on
    the rows and the columns.

    Parameters
    ----------
    features: array (N, M)
        an array of features to be sorted.
    outdir: str
        the destination folder where the ouputs will be saved.
    name: str
        the name of the plot.
    header: list (M, ), default None
        the features names.
    verbose: int, default 0
        the verbosity level.

    Returns
    -------
    features_snap: str
        the sorted features representation.
    """
    # Check inputs
    if verbose > 0:
        print("[info] Sorting features in array of shape "
              "'{0}'...".format(features.shape))

    # Normalize features
    scaler = preprocessing.StandardScaler().fit(features)
    scaled_features = scaler.transform(features)

    # Use the seaborn template to create a pretty display
    with plt.style.context("seaborn-deep"):

        # Create a figure
        fig = plt.figure(figsize=(12, 12))
        ax1 = fig.add_axes([0.17, 0.15, 0.1, 0.73])
        ax2 = fig.add_axes([0.3, 0.89, 0.6, 0.1])
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax1.xaxis.set_visible(False)
        ax1.yaxis.set_visible(False)
        ax2.xaxis.set_visible(False)
        ax2.yaxis.set_visible(False)

        # Ward hierachical clustering analysis on the rows and the columns.
        linkage_array_row = scipy.cluster.hierarchy.linkage(
            scaled_features, method="ward", metric="euclidean")
        dendogram_1 = scipy.cluster.hierarchy.dendrogram(
            linkage_array_row, orientation="left", ax=ax1)
        linkage_array_col = scipy.cluster.hierarchy.linkage(
            scaled_features.transpose(), method="ward", metric="euclidean")
        dendogram_2 = scipy.cluster.hierarchy.dendrogram(
            linkage_array_col, ax=ax2)

        # Organize the input feature array
        idx1 = dendogram_1["leaves"]
        idx2 = dendogram_2["leaves"]
        axmatrix = fig.add_axes([0.3, 0.15, 0.6, 0.73])
        matrix = scaled_features[:, idx2]
        matrix = matrix[idx1, :]

        # Render the organized feature matrix
        im = axmatrix.matshow(matrix, aspect="auto", origin="lower",
                              cmap=plt.cm.get_cmap("Spectral"),
                              vmin=-1, vmax=1)
        if header is not None:
            clusterized_labels = [header[i] for i in idx2]
            axmatrix.xaxis.set_visible(True)
            axmatrix.xaxis.set_label_position("bottom")
            axmatrix.xaxis.tick_bottom()
            axmatrix.set_xticks(range(len(header)))
            axmatrix.set_xticklabels(clusterized_labels, fontsize=8,
                                     rotation=-90)
        else:
            axmatrix.xaxis.set_visible(False)
        axmatrix.yaxis.set_visible(False)
        axcolor = fig.add_axes([0.91, 0.15, 0.02, 0.73])
        plt.colorbar(im, cax=axcolor)
        plt.title("Organized features", fontsize=10)

        # Display/save the plot
        features_snap = os.path.join(outdir, name + ".png")
        plt.savefig(features_snap, format="png")

    return features_snap
