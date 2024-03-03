#!/usr/bin/env python
# coding: utf_8

'''
Below is an example of the execution command.
python plot_top_cmd.py -i output.csv -o output.png -s "2024/02/18 00:00" -e "2024/02/19 00:00" -k mdas_cpu
'''

import argparse
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def date_type(date_str):
    return datetime.strptime(date_str, '%Y/%m/%d %H:%M')

def parseArgs():
    # Parse the argument.
    parser = argparse.ArgumentParser(prog="plot_top_cmd.py", description="", epilog="end", add_help=True)
    parser.add_argument("--input_file" , "-i", action="store", default="output.csv", type=str      , required=False, help="Specify the file you want to graph.")
    parser.add_argument("--output_file", "-o", action="store", default="output.png", type=str      , required=False, help="Specify the file name when saving as an image.")
    parser.add_argument("--start_time" , "-s", action="store",                       type=date_type, required=True , help="Specify the start time of the range to be graphed. (YYYY/MM/DD hh:mm)")
    parser.add_argument("--end_time"   , "-e", action="store",                       type=date_type, required=True , help="Specify the end time of the range to be graphed. (YYYY/MM/DD hh:mm)")
    parser.add_argument("--graph_kind" , "-k", action="store", default="none"      , type=str      , required=False, help="Specify the type of data to graph.")
    args = parser.parse_args()
    i_file = args.input_file
    o_file = args.output_file
    s_time = args.start_time
    e_time = args.end_time
    graph_kind = args.graph_kind

    return i_file, o_file, s_time, e_time, graph_kind

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

def plotOnGraph(o_file, s_time, e_time, graph_kind, pid_list, mem_mat):
    time = [datetime.strptime(row['time'], '%Y/%m/%d %H:%M:%S') for row in mem_mat]
    for col_elem in pid_list:
        data = [int(row[col_elem]) for row in mem_mat]
        plt.plot(time, data, label=col_elem)

    # Set the minimum and maximum for the X and Y axes.
    plt.ylim(0, None)
    plt.xlim(s_time, e_time)

    # Set the plot area.
    plt.subplots_adjust(right=0.96, top=0.94, bottom=0.21)

    # Set the axis labels.
    plt.title(graph_kind)
    date_format = mdates.DateFormatter("%m/%d %H:%M")
    plt.gca().xaxis.set_major_formatter(date_format)
    plt.xticks(rotation=90)

    # Show the legend.
    plt.legend()

    plt.savefig(o_file)
    # Display the graph.
    plt.show()

def main():
    print("[INFO] Start.")

    # Parse the argument.
    i_file, o_file, s_time, e_time, graph_kind = parseArgs()
    print("[INFO] Parsed the argument.")

    pid_list, cmd_list = readTimeSeriesName(i_file)
    #print(pid_list)
    #print(cmd_list)
    mem_mat = readTimeSeriesData(i_file, s_time, e_time)
    #print(mem_mat)

    plotOnGraph(o_file, s_time, e_time, graph_kind, pid_list, mem_mat)

    print("[INFO] It's finished.")

if __name__ == "__main__":
    main()
