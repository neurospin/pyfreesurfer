#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013 - 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import csv
import numpy as np


def sst_paradigm(behav_file, outfile, timepoint):
    """
    Converts an Imagen raw behavioral file to a FsFast compatible paradigm file
    for the Stop Signal Task (SST).
    Checks file content according to timepoint specific requirements.
    Also check trial timeline reset.
    Each line of the output file represents one stimulus presentation.
    First column is the event time, second column is the event code
    (0 for fixation (baseline) and >0 for stimuli), third column is the
    stimulus duration in seconds, fourth column is the associated weight
    (default 1.),
    and last column is the stimulus name (ignored by FsFast).
    Althought it's an event related protocol, we define stimuli duration to be
    non zero, else the design matrix can not be inverted by FsFast.
    Displays the mean of the event durations to set the 'refeventdur'
    parameter needed by 'mkmodel_sess' function.

    Parameters
    ----------
    behav_file: str
        The path to the raw imagen behavioral file.
    outfile: str
        The path of the output file.
    timepoint: str
        The coresponding timepoint (for integrity checks)
    """

    # Define stimuli names and indexes and their corresponding keys in the
    # raw behavioral file.
    transcoding_table = {
        "go_success": (('GO_SUCCESS', 'STOP_TOO_EARLY_RESPONSE'), 1),
        "go_toolate": (('GO_TOO_LATE'), 2),
        "go_wrong": (('GO_WRONG_KEY_RESPONSE'), 3),
        "stop_success": (('STOP_SUCCESS'), 4),
        "stop_failure": (('STOP_FAILURE'), 5)
    }

    # Read the raw bahavioral file
    with open(behav_file, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        csv_rows = [row for row in reader]

    # Extract the header line
    cols_idx = []
    headers = []
    for i, header in enumerate(csv_rows[1]):
        if len(header.strip()) > 0:
            cols_idx.append(i)
            headers.append(header)

    # Remove any empty line
    csv_data = []
    for row in csv_rows[2:]:
        if len(" ".join(row).strip()) > 0:
            csv_data.append(
                [cell for i, cell in enumerate(row) if i in cols_idx])

    # Look for any trial timeline reset
    st_idx = headers.index("Trial Start Time (Onset)")
    ref_i = 0
    ref_st = -1.
    for i, st in enumerate([float(row[st_idx]) for row in csv_data]):
        if st < ref_st:
            ref_i = i
            print "[warning] {} : timeline reset".format(behav_file)
        ref_st = st
    csv_data = csv_data[ref_i:]

    # Timepoint specific checks
    nb_trials = len(csv_data)
    if timepoint == 'BL':
        assert nb_trials > 480, ("{} : behav file has less than "
                                 "480 trials.".format(behav_file))
    elif timepoint == 'FU2':
        assert nb_trials > 360 and nb_trials < 370, ("BL behav file do not "
                                                     "have 360 trials.")

    # Get the cell index for headers of interest
    go_st_idx = headers.index("Go Stimulus Presentation Time ")
    stop_st_idx = headers.index("Stop Stimulus Presentation Time")
    ro_idx = headers.index("Response Outcome")
    abs_resp_idx = headers.index("Absolute Response Time")

    # Build the output file
    output = []
    # Store the stimuli durations
    durations = []
    for i, row in enumerate(csv_data):
        # Keep only known conditions
        for cname, (events, idx) in transcoding_table.items():
            if row[ro_idx] in events:
                # Get the go stimulus presentation time
                go_start = float(row[go_st_idx])
                # Case of 'go_success' and 'go_wrong': the subject responded so
                # the go stimulus duration is the minimum between go maximum
                # duration (1s) and time elapsed between go start and response
                if cname in ["go_success", "go_wrong"]:
                    go_end = min(float(row[abs_resp_idx]), go_start + 1000.)
                # Case of 'go_toolate' : the subject did not responded
                elif cname == "go_toolate":
                    go_end = go_start + 1000.
                # Case of 'stop_failure' : the subject failed to inhibit
                # his response so the go stimulus end is the minimum between
                # the reponse time and the stop stimulus presentatio time
                elif cname == "stop_failure":
                    go_end = min(
                        float(row[abs_resp_idx]), float(row[stop_st_idx]))
                # Case of 'stop_success' : the subject dis not responded so the
                # go end time is the stop presentation time
                elif cname == "stop_success":
                    go_end = float(row[stop_st_idx])
                go_dur = go_end - go_start
                # Add the new line to the output file
                output.append(
                    [go_start/1000., idx, go_dur/1000., 1, cname])
                # Store the go duration
                durations.append(go_dur)
                # Case of stop trials : we add an other line for the
                # stop stimulus
                stop_dur = 0.
                # TODO : Add jitter info?
                if cname.startswith("stop"):
                    stop_pres = float(row[stop_st_idx])
                    stop_end = None
                    # Case of 'stop_failure' : the subject failed to inhibit
                    if cname == "stop_failure":
                        abs_resp_t = float(row[abs_resp_idx])
                        if abs_resp_t > stop_pres:
                            stop_end = abs_resp_t
                    # Case of 'stop_success' : the subject did not responded so
                    # the stop duration is the max stop duration (300 ms)
                    elif cname == "stop_success":
                        stop_end = stop_pres + 300.
                    if stop_end is not None:
                        stop_dur = stop_end - stop_pres
                        # Add the stop line to the output file
                        output.append(
                            [stop_pres/1000., idx, stop_dur/1000., 1, cname])
                        # Store the stop duration
                        durations.append(stop_dur)
                # Add a line for the fixation period between latest stimulus
                # end and next go presentation time
                if i < nb_trials - 1:
                    fix_start = go_start + go_dur + stop_dur
                    fix_end = float(csv_data[i + 1][go_st_idx])
                    fix_dur = fix_end - fix_start
                    # Add the fixation line to the output file
                    output.append(
                        [fix_start/1000., 0, fix_dur/1000., 1, "fixation"])

    # Display the mean of the stimuli durations to set the mkmodel_sess
    # 'refeventdur' parameter.
    print("Mean of the task event durations : {} seconds".format(
        np.mean(durations)/1000.))

    # Save output paradigm file
    with open(outfile, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=" ")
        writer.writerows(output)


if __name__ == "__main__":
    behav_file = ("/neurospin/imagen/BL/processed/nifti/000001441076/"
                  "BehaviouralData/ss_000001441076.csv")
    output_file = "/volatile/FsFast/imagen/inputs/paradigm.txt"
    timepoint = "BL"
    sst_paradigm(behav_file=behav_file, outfile=output_file,
                 timepoint=timepoint)
