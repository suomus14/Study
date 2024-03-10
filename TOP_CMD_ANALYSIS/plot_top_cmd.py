#!/usr/bin/env python
# coding: utf_8

'''
Below is an example of the execution command.
python plot_top_cmd.py -s "2024/01/01 00:00" -e "2024/01/01 23:59" -k xxx_cpu
'''

import argparse
import os
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DEFAULT_DATE = datetime.strptime("1970/01/01 00:00", '%Y/%m/%d %H:%M')

def date_type(date_str):
    return datetime.strptime(date_str, '%Y/%m/%d %H:%M')

def parseArgs():
    # Parse the argument.
    parser = argparse.ArgumentParser(prog="plot_top_cmd.py", description="", epilog="end", add_help=True)
    parser.add_argument("--input_file",  "-i", action="store", default="system_metrics/output.csv", type=str,       required=False, help="Specify the file to plot.")
    parser.add_argument("--output_file", "-o", action="store", default="system_metrics/output.png", type=str,       required=False, help="Specify the file name when saving as an image.")
    parser.add_argument("--start_time",  "-s", action="store", default=DEFAULT_DATE,                type=date_type, required=True,  help="Specify the start time of the range to plot. (YYYY/MM/DD hh:mm)")
    parser.add_argument("--end_time",    "-e", action="store", default=DEFAULT_DATE,                type=date_type, required=True,  help="Specify the end time of the range to plot. (YYYY/MM/DD hh:mm)")
    parser.add_argument("--graph_kind",  "-k", action="store", default="none",                      type=str,       required=False, help="Specifies the type of data to plot.")
    args = parser.parse_args()
    i_file = args.input_file
    o_file = args.output_file
    s_time = args.start_time
    e_time = args.end_time
    graph_kind = args.graph_kind

    return i_file, o_file, s_time, e_time, graph_kind

def findTargetFile(i_file):
    if i_file:
        if not os.path.isfile(i_file):
            print("[ERROR] " + i_file + " not found.")
            exit(1)

    return i_file

def readTimeSeriesName(i_file):
    fi = open(i_file, 'r', newline='\n')
    pid_list = (fi.readline().strip().split(','))[1:]
    cmd_list = (fi.readline().strip().split(','))[1:]
    fi.close()

    return pid_list, cmd_list

def readTimeSeriesData(i_file, s_time, e_time):
    fi = open(i_file, 'r', newline='\n')
    reader = csv.DictReader(fi)
    next(reader) # To skip the command name header line.
    mem_mat_tmp = [row for row in reader]
    fi.close()

    mem_mat = []
    for row in mem_mat_tmp:
        cur_time = datetime.strptime(row['time'], '%Y/%m/%d %H:%M:%S')
        if ((s_time <= cur_time) and (cur_time <= e_time)):
            mem_mat.append(row)

    return mem_mat

def plotOnGraph(o_file, s_time, e_time, graph_kind, pid_list, cmd_list, mem_mat):
    plt.figure(figsize=(12, 8))
    plt.subplots_adjust(left=0.07, right=0.96, top=0.96, bottom=0.09)

    plt.title(graph_kind, fontsize=16)

    plt.xlabel("")
    plt.ylabel("memory(RES) [KB]")
    plt.ticklabel_format(useOffset=False)

    time = [datetime.strptime(row['time'], '%Y/%m/%d %H:%M:%S') for row in mem_mat]
    for idx in range(len(pid_list)):
        pid = pid_list[idx]
        cmd = cmd_list[idx]
        label_name = ("(" + pid + ") " + cmd[1:-1])[:20]
        data = [int(row[pid]) for row in mem_mat]
        plt.plot(time, data, label=label_name)

    plt.xlim(s_time, e_time)
    plt.ylim(0, None)

    plt.xticks(rotation=30)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))

    plt.legend()

    plt.savefig(o_file)
    plt.show()

def main():
    print("[INFO] Start.")

    # Parse the argument.
    i_file, o_file, s_time, e_time, graph_kind = parseArgs()
    print("[INFO] Parsed the argument.")

    # Find for files to analyze.
    i_file = findTargetFile(i_file)

    pid_list, cmd_list = readTimeSeriesName(i_file)
    #print(pid_list)
    #print(cmd_list)
    mem_mat = readTimeSeriesData(i_file, s_time, e_time)
    #print(mem_mat)

    plotOnGraph(o_file, s_time, e_time, graph_kind, pid_list, cmd_list, mem_mat)

    print("[INFO] It's finished.")

if __name__ == "__main__":
    main()

