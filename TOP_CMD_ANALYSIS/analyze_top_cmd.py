#!/usr/bin/env python
# coding: utf_8

'''
Below is an example of the execution command.
python analyze_top_cmd.py
'''

import argparse
import os
import re

# PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
#   0    1  2  3    4   5   6 7    8    9    10      11
PL_PID  = 0
PL_USER = 1
PL_PR   = 2
PL_NI   = 3
PL_VIRT = 4
PL_RES  = 5
PL_SHR  = 6
PL_S    = 7
PL_CPU  = 8
PL_MEM  = 9
PL_TIME = 10
PL_CMD  = 11
PL_NUM  = 12

DATE_PATTERN = re.compile(r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}")
RES_PATTERN = re.compile(r"\d*\.?\d+")

def parseArgs():
    # Parse the argument.
    parser = argparse.ArgumentParser(prog="analyze_top_cmd.py", description="", epilog="end", add_help=True)
    parser.add_argument("--input_dir",   "-d", action="store",  default="system_metrics", type=str, required=False, help="Specify the directory to analyze.")
    parser.add_argument("--input_file",  "-i", action="append",                           type=str, required=False, help="Specify the file to analyze.")
    parser.add_argument("--output_file", "-o", action="store",  default="output.csv",     type=str, required=False, help="Specify the output file name of the analysis results.")
    parser.add_argument("--pid_num",     "-n", action="store",  default=20,               type=int, required=False, help="Specify the number of 'pid' to be analyzed.")
    args = parser.parse_args()
    i_dir = args.input_dir
    i_file = args.input_file
    o_file = args.output_file
    pid_num = args.pid_num

    return i_dir, i_file, o_file, pid_num

def findTargetFile(i_dir, i_file, o_file):
    if i_file:
        for file in i_file:
            if not os.path.isfile(file):
                print("[ERROR] " + file + " not found.")
                exit(1)
        return i_file, o_file

    if os.path.isdir(i_dir):
        i_f = [os.path.join(i_dir, file) for file in os.listdir(i_dir) if 'top_cmd' in file]
        o_f = os.path.join(i_dir, o_file)
        return i_f, o_f
    else:
        print("[ERROR] " + i_dir + " not found.")
        exit(1)

def unifyResUnits(res_str):
    if False: pass
    elif 'm' in res_str:
        res = float(RES_PATTERN.search(res_str).group()) * 1024
    elif 'g' in res_str:
        res = float(RES_PATTERN.search(res_str).group()) * 1048576
    else:
        res = res_str

    return int(res)

def extractpidessToAnalyze(i_file, pid_num):
    data_cnt = 0
    pid_mem = dict()
    pid_cmd = dict()

    for file in i_file:
        print("[INFO] (pre) input file: " + file)

        pid_list_flg = False

        fi = open(file, 'r', newline='\n')
        for line in fi:
            # Skip blank lines.
            if line == '\n':
                pid_list_flg = False
                continue

            result = DATE_PATTERN.search(line)
            if ("timestamp:" in line) and (result):
                data_cnt += 1
                continue

            # Parse each element.
            elem = line.split()
            pid = elem[PL_PID]
            cmd = elem[PL_CMD:]

            # PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
            # Set a flag to read after the above line.
            if (elem[PL_PID] == "PID") and (elem[PL_USER] == "USER") and (elem[PL_RES] == "RES") and (elem[PL_SHR] == "SHR"):
                pid_list_flg = True
                continue

            # Get maximum memory usage by pidess.
            if (pid_list_flg == True) and (len(elem) >= PL_NUM):
                # Since it is sometimes expressed in gigabytes, the unit is unified to kilobytes.
                res = unifyResUnits(elem[PL_RES])

                if pid in pid_mem.keys():
                    if res > int(pid_mem[pid]):
                        pid_mem[pid] = res
                        pid_cmd[pid] = cmd
                else:
                    if res > 0:
                        pid_mem[pid] = res
                        pid_cmd[pid] = cmd

        fi.close()

    # Sort by memory usage. Please note that it is a list type.
    sorted_pid_mem = sorted(pid_mem.items(), key=lambda x:x[1], reverse=True)
    # Extract the top n items.
    if (0 < pid_num) and (pid_num < len(sorted_pid_mem)):
        pickup_pid_mem = sorted_pid_mem[:pid_num]
    else:
        pickup_pid_mem = sorted_pid_mem
    pid_list = [pid for pid, mem in pickup_pid_mem]

    return pid_list, pid_cmd, data_cnt

def getTimeSeriesData(pid_list, pid_cmd, total_data_cnt, i_file, o_file):
    data_cnt = 0
    pid_mem = dict()

    fo = open(o_file, 'w', newline='\n')
    fo.write("time")
    for pid in pid_list:
        fo.write(',' + pid)
        pid_mem[pid] = 0
    fo.write('\n')
    fo.write("time")
    for pid in pid_list:
        fo.write("," + "\"" + ' '.join(pid_cmd[pid]) + "\"")
    fo.write('\n')

    for file in i_file:
        print("[INFO] (act) input file: " + file)

        pid_list_flg = False

        fi = open(file, 'r', newline='\n')
        for line in fi:
            # Skip blank lines.
            if line == '\n':
                # Output to file.
                if pid_list_flg == True:
                    prog = data_cnt / total_data_cnt * 100
                    print("[INFO] - " + cur_time + " (" + "{: >6.2f}".format(prog) + " %)" )
                    fo.write(cur_time)
                    for pid in pid_list:
                        fo.write(',' + str(pid_mem[pid]))
                    fo.write('\n')

                    # Clear the file output buffer.
                    for pid in pid_list:
                        pid_mem[pid] = 0

                pid_list_flg = False
                continue

            result = DATE_PATTERN.search(line)
            if (result) and ("timestamp:" in line):
                cur_time = result.group()
                data_cnt += 1
                continue

            # Parse each element.
            elem = line.split()
            pid = elem[PL_PID]

            # PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ COMMAND
            # Set a flag to read after the above line.
            if (elem[PL_PID] == "PID") and (elem[PL_USER] == "USER") and (elem[PL_RES] == "RES") and (elem[PL_SHR] == "SHR"):
                pid_list_flg = True
                continue

            # Get maximum memory usage by pidess.
            if (pid_list_flg == True) and (len(elem) >= PL_NUM):
                # Since it is sometimes expressed in gigabytes, the unit is unified to kilobytes.
                res = unifyResUnits(elem[PL_RES])

                if pid in pid_list:
                    pid_mem[pid] = res

        fi.close()
    fo.close()

    return

def main():
    print("[INFO] Start.")

    # Parse the argument.
    i_dir, i_file, o_file, pid_num = parseArgs()
    print("[INFO] Parsed the argument.")

    # Find for files to analyze.
    i_file, o_file = findTargetFile(i_dir, i_file, o_file)

    # Extract the pidess to analyze in advance
    pid_list, pid_cmd, data_cnt = extractpidessToAnalyze(i_file, pid_num)
    print("[INFO] It's ready.")

    # Output to file as time series data.
    getTimeSeriesData(pid_list, pid_cmd, data_cnt, i_file, o_file)

    print("[INFO] It's finished.")

if __name__ == "__main__":
    main()



'''
------------------------------
timestamp: 2024/01/01 00:00:00
                             0
[ 0]: タイムスタンプ(YYYY/MM/DD hh:mm:ss)

top - 00:00:00 up 1 days,  1:00,  1 users,  load average: 0.00, 0.00, 0.00
             0         1      2         3                    4     5     6
[ 0]: タイムスタンプ(hh:mm:ss)
[ 1]: OSが起動してからの日数
[ 2]: OSが起動してからの時間
[ 3]: コンソールにログインしているユーザー
[ 4]: 実行待ちとディスクI/O待ちのプロセス数[ 1min平均]
[ 5]: 実行待ちとディスクI/O待ちのプロセス数[ 5min平均]
[ 6]: 実行待ちとディスクI/O待ちのプロセス数[15min平均]

Tasks: 198 total,   1 running, 197 sleeping,   0 stopped,   0 zombie
               0            1             2            3           4
[ 0]: 存在するプロセス数
[ 1]: 実行中のプロセス数
[ 2]: スリープ中のプロセス数
[ 3]: 停止中のプロセス数
[ 4]: ゾンビプロセス数

%Cpu(s): 10.0 us, 15.0 sy,  0.0 ni, 75.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st 
               0        1        2        3        4        5        6        7
[ 0]: ユーザープロセスの使用時間の割合
[ 1]: システムプロセスの使用時間の割合
[ 2]: 優先度を設定されたプロセス使用時間の割合
[ 3]: アイドル状態の時間の割合
[ 4]: 読み書きや書き込みの完了待ち時間の割合
[ 5]: ハードウェア割り込み時間の割合
[ 6]: ソフトウェア割り込み時間の割合
[ 7]: CPUリソースを他サーバーに割かれしまい割り当てられなかった時間の割合

MiB Mem :   3793.2 total,    229.3 free,    381.5 used,   3283.0 buff/cache
                       0              1              2                    3
|<------------------------------------ total ----------------------------------->|
|<------ used ------><------------- buff/cache -------------><------ free ------>|
|                    <----- cannot -----><--- releasable --->                    |
|                                        <-------------- available ------------->|
[ 0]: 合計メモリ量
[ 1]: 空きメモリ量
[ 2]: 割り当てられているメモリ量
[ 3]: バッファやキャッシュに割り当てられているメモリ量

MiB Swap:      0.0 total,      0.0 free,      0.0 used.   3411.7 avail Mem 
                       0              1              2                   3
[ 0]: 合計スワップ量
[ 1]: 空きスワップ量
[ 2]: 割り当てられているスワップ量
[ 3]: 物理メモリの実質的な空き容量

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
    901 user      20   0  408492  86336  62940 S   0.0   2.2   0:14.48 /usr/bin/wayfire
   1095 user      20   0  843648  60420  45796 S   0.0   1.6   2:12.24 wf-panel-pi
   1385 user      20   0  294280  56584  44800 S   0.0   1.5   0:00.11 /usr/libexec/xdg-desktop-portal-wlr
      0    1       2   3       4      5      6 7     8     9        10      11
[ 0]: プロセスID
[ 1]: 実行しているユーザー
[ 2]: プロセス優先度(低いほど優先)(最優先はrt)
[ 3]: nice値(低いほど優先)(NI=PR-20)
[ 4]: 割り当てられている仮想メモリ量(スワップを含む)
[ 5]: 実際に消費されているメモリ量(Resident Memory Size)
[ 6]: RESのうち共有メモリとして消費されているメモリ量(Shared Memory Size)
[ 7]: プロセスの稼働状態
[ 8]: CPU使用率
[ 9]: MEM使用率
[10]: プロセスが稼働してからCPUが処理した時間(+は10msec単位であることを示す)
[11]: プロセス名

'''

