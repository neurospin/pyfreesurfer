##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
Modules that provides polar plot tools.
"""

# System import
import numpy as np
import matplotlib.pyplot as plt


def polar_plot(individual_stats, cohort_stats, snapfile, name=None):
    """ Display a polar plot with some summary values (statistics).

    Parameters
    ----------
    individual_stats, cohort_stats: dict (mandatory)
        structure describing the measure by regions on the cohort and
        on the individual: can be generated with the
        'pyfreesurfer.utils.statistics.population_summary'.
    snapfile: str (mandatory)
        the destination file name where polar plot is saved.
    name: str (optional, default None)
        the name of the polar plot.
    """
    fig = plt.figure(figsize=(45, 18))
    fig.subplots_adjust(wspace=0.25, hspace=0.20, top=0.85, bottom=0.05)
    color_ok = 1
    color_out = 255
    sigma_thr = 2
    nb_cols = 4
    nb_rows = len(individual_stats) / nb_cols
    if len(individual_stats) % nb_cols != 0:
        nb_rows += 1

    # Go through measure
    nb_subplots = 0
    for measure_name, measure_item in individual_stats.items():

        # Calculate evenly-spaced axis angles
        nb_regions = len(measure_item)
        angle = np.linspace(0, 2 * np.pi, nb_regions, endpoint=False)

        # Rotate theta such that the first axis is at the top
        angle += np.pi/2
        angle = angle.tolist()
        angle.append(angle[0])

        # Create plor subplot for the measure
        nb_subplots += 1
        ax = fig.add_subplot(nb_rows, nb_cols, nb_subplots, projection="polar")
        ax.set_title(measure_name, weight="bold", size="medium",
                     position=(0.5, 1.1),
                     horizontalalignment="center",
                     verticalalignment="center")

        # Go through regions
        _data = []
        _color = []
        _bound_max = [sigma_thr + 3, ] * (len(measure_item) + 1)
        _bound_min = [3 - sigma_thr, ] * (len(measure_item) + 1)
        _mean = [3, ] * (len(measure_item) + 1)
        _regions = []
        for region_name, indstats in measure_item.items():
            indmeasure = indstats["m"]
            stats = cohort_stats[measure_name][region_name]
            if stats["s"] == 0:
                normalize_value = 0
            else:
                normalize_value = (indmeasure - stats["m"]) / stats["s"] + 3
            if normalize_value < 0:
                normalize_value = 0
            _data.append(normalize_value)
            if (normalize_value > sigma_thr + 3 or
                    normalize_value < 3 - sigma_thr):
                _color.append(color_out)
            else:
                _color.append(color_ok)
            _regions.append(region_name)
        _data.append(_data[0])
        _color.append(_color[0])

        # Create a polar subplot
        plt.scatter(angle, _data, c=_color, s=100, cmap=plt.cm.bwr)
        plt.plot(angle, _bound_max, "r")
        plt.plot(angle, _bound_min, "r")
        plt.plot(angle, _mean, "g--", linewidth=2)
        ax.fill(angle, _data, facecolor="b", alpha=0.25)
        ax.set_thetagrids(np.degrees(angle), _regions, fontsize="small")

        ax.set_yticks(range(0, 6, 1))
        ax.set_yticklabels([r"-3$\sigma$", r"-2$\sigma$", r"-$\sigma$",
                            r"$\mu$", r"+$\sigma$", r"+2$\sigma$",
                            r"+3$\sigma$"])

    # Set figure title
    plt.figtext(0.5, 0.965, name or "", ha="center", color="black",
                weight="bold", size="large")
    plt.savefig(snapfile)
