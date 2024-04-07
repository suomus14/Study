#!/usr/bin/env python
# coding: euc_jp

#===============================================================================
# File Name         : init_check_tool.py
#
# Copyright(C) Canon Inc.
# All rights reserved.
# Confidential
#-------------------------------------------------------------------------------
# Function          : xxx
#-------------------------------------------------------------------------------
# Designer          : Canon Inc.
#-------------------------------------------------------------------------------
# History      Date          Theme
# V0.0.1.00    2024/03/14    new
#===============================================================================

import os
import re
import glob
import json
import subprocess
import calendar
from time import time
from datetime import datetime
from ftplib import FTP, all_errors

# Espritset file
ESPRITSET_PATH      = "/console/mdas/MachineList"
ESPRITSET_NAME      = "*.espritset"
ESPRITSET_SN_KEY    = "SERIAL_NUM"
ESPRITSET_EIP_KEY   = "EPC_IPADDR"
ESPRITSET_LIP_KEY   = "LOGPC_IPADDR"
ESPRITSET_NAME_KEY  = "TOOL_ID"
ESPRITSET_TYPE_KEY  = "ESPRIT_MACHINE_TYPE"
ESPRITSET_FTP_USER  = "LOGPC_FTP_LOGIN_USER"
ESPRITSET_FTP_PASS  = "LOGPC_FTP_LOGIN_PASSWD"
ESPRITSET_FILE_PORT = "LOGPC_FTP_PORT"
ESPRITSET_DCDP_PORT = "DCDP_FTP_PORT"
SETENV_STR          = "setenv "

# file_handler.json
MDAS_SETTING_PATH_6300          = "/console/mdas/MachineModel/6300ES6a/etc"
MDAS_SETTING_PATH_5550          = "/console/mdas/MachineModel/5550iZ2/etc"
FILE_HANDLER_JSON               = "file_handler.json"
FILE_HANDLER_EQUIP_FILE_TYPE    = "FileType"
FILE_HANDLER_EQUIP_FILE_PATH    = "TargetFilePath"
FILE_HANDLER_EQUIP_FILE_NAME    = "FileName"
FILE_HANDLER_MDAS_ORI_FILE_PATH = "OutputPath"
FILE_HANDLER_MDAS_REC_FILE_PATH = "FCRecoveryFileDir"
LAST_2_STR = -2

DCDP_TARGET_PATH = "/VROOT/COMPAT/BRTL"

# FTP LIST return value parsing syntax
LS_AUTHORITY      = 0
LS_HARD_LINK      = 1
LS_OWNER          = 2
LS_GROUP          = 3
LS_FILE_SIZE      = 4
LS_TIMESTAMP_MON  = 5
LS_TIMESTAMP_DAY  = 6
LS_TIMESTAMP_TIME = 7
LS_TIMESTAMP_YEAR = 7
LS_FILE_NAME      = 8
FTP_FILE_TYPE_KEY      = "FileType"
FTP_PERMISSION_KEY     = "Permission"
FTP_OWNER_GROUP_KEY    = "OwnerGroup"
FTP_FILE_NAME_KEY      = "Name"
FTP_FILE_SIZE_KEY      = "Size"
FTP_TIMESTAMP_YEAR_KEY = "Year"
FTP_TIMESTAMP_DATE_KEY = "Date"
FTP_TIMESTAMP_TIME_KEY = "Time"
FTP_RAW_DATA_LINE_KEY  = "RawData"
TIME_PATTERN = re.compile(r"\d{2}:\d{2}")
YEAR_PATTERN = re.compile(r"\d{4}")

# data_push.json
DATA_PUSH_PATH = "/console/mdas/etc"
DATA_PUSH_NAME = "data_push.json"
LDB_FAB_KEY    = "CustomerName"
LDB_ADDR_KEY   = "IPAddress"
LDB_PORT_KEY   = "Port"
LDB_USER_KEY   = "LoginUser"
LDB_PASS_KEY   = "LoginPassword"

# Machine type
MACHINE_TYPE_6300 = "6300ES6a"
MACHINE_TYPE_5550 = "5550iZ2"

# FTP settings
TIME_OUT = 5

class LogMng():
    def __init__(self):
        self.log_file = open("mdas_status.log", 'w')

    def __del__(self):
        self.log_file.close()

    def logOutput(self, level, msg):
        log_msg = datetime.now().strftime("%Y/%m/%d %H:%M:%S") + " [" + str(level) + "] " + str(msg)
        print(log_msg)
        self.log_file.write(log_msg + '\n')

    def info(self, msg):
        self.logOutput("INFO", msg)

    def warn(self, msg):
        self.logOutput("WARN", msg)

    def error(self, msg):
        self.logOutput("ERROR", msg)

class InitCheckTool():
    def __init__(self):
        self.log = LogMng()
        self.ftp = FTP()

        self.equip_list = list()
        self.equip_valid = False
        self.ldb_info = {}
        self.ldb_valid = False

        self.file_handler_6300 = {}
        self.file_handler_5550 = {}

    def __del__(self):
        pass

    ### ... ###
    ### ... ###
    ### ... ###

    def ftpListCallback(self, line):
        elem = line.split()

        if elem[LS_AUTHORITY][0] == 'd':
            is_file = False
        else:
            is_file = True

        if False: pass
        elif TIME_PATTERN.match(elem[LS_TIMESTAMP_TIME]):
            year = ""
            time = elem[LS_TIMESTAMP_TIME]
        elif TIME_PATTERN.match(elem[LS_TIMESTAMP_YEAR]):
            year = elem[LS_TIMESTAMP_YEAR]
            time = ""
        else:
            year = ""
            time = ""

        temp = elem[LS_TIMESTAMP_MON] + ' ' + elem[LS_TIMESTAMP_DAY]
        print(elem)
        print(temp)
        try:
            date = datetime.strptime(temp, "%b %d").strftime("%m/%d")
        except:
            date = datetime.strptime("2000 " + temp, "%Y %b %d").strftime("%m/%d")

        file_attr = {
            FTP_FILE_TYPE_KEY:      is_file,
            FTP_PERMISSION_KEY:     elem[LS_AUTHORITY][1:],
            FTP_OWNER_GROUP_KEY:    elem[LS_OWNER] + ':' + elem[LS_GROUP],
            FTP_FILE_NAME_KEY:      elem[LS_FILE_NAME],
            FTP_FILE_SIZE_KEY:      elem[LS_FILE_SIZE],
            FTP_TIMESTAMP_YEAR_KEY: year,
            FTP_TIMESTAMP_DATE_KEY: date,
            FTP_TIMESTAMP_TIME_KEY: time,
            FTP_RAW_DATA_LINE_KEY:  line,
        }
        self.ftp_file_info_list.append(file_attr)
        if (not self.file_only) or (is_file):
            self.log.info(file_attr)

    def ftpList(self, path, file_only=False, log_valid=True):
        if path == '':
            return list()

        self.file_only = file_only
        self.ftp_file_info_list = list()
        try:
            if log_valid: self.log.info("FTP retrlines(LIST) try: " + path)
            self.ftp.retrlines("LIST {}".format(path), self.ftpListCallback)
            if log_valid: self.log.info("FTP retrlines(LIST) success.")
        except all_errors as e:
            self.log.error("FTP retrlines(LIST) error: " + str(e))
            return list()

        try:
            if log_valid: self.log.info("FTP nlst try: " + path)
            self.ftp.nlst()
            if log_valid: self.log.info("FTP nlst success.")
        except all_errors as e:
            self.log.error("FTP nlst error: " + str(e))
            return list()

        return self.ftp_file_info_list

    def ftpCwd(self, path, log_valid=True):
        if path == '':
            return False

        try:
            if log_valid: self.log.info("FTP cwd try: " + path)
            self.ftp.cwd(path)
            if log_valid: self.log.info("FTP cwd success.")
        except all_errors as e:
            self.log.error("FTP cwd error: " + str(e))
            return False

        return True

    def getEquipBrtlFileList(self, path):
        if not self.ftpCwd(path, log_valid=False): return
        file_dir_info_list = self.ftpList(path, file_only=True, log_valid=False)
        for file_dir_info in file_dir_info_list:
            if not file_dir_info[FTP_FILE_TYPE_KEY]:
                child_path = os.path.join(path, file_dir_info[FTP_FILE_NAME_KEY])
                self.getEquipBrtlFileList(child_path)

        return

    def getEquipFileList(self):
        if self.equip_valid:
            for equip_info in self.equip_list:
                self.log.info("Get file list: " + equip_info[ESPRITSET_NAME_KEY])

                try:
                    self.log.info("FTP connect try: " + equip_info[ESPRITSET_LIP_KEY])
                    self.ftp.connect(host=equip_info[ESPRITSET_LIP_KEY], port=equip_info[ESPRITSET_FILE_PORT], timeout=TIME_OUT)
                    self.log.info("FTP connect success.")
                    self.log.info("FTP login try: " + equip_info[ESPRITSET_FTP_USER])
                    self.ftp.login(user=equip_info[ESPRITSET_FTP_USER], passwd=equip_info[ESPRITSET_FTP_PASS])
                    self.log.info("FTP login success.")
                except all_errors as e:
                    self.log.error("FTP connection error: " + str(e))
                    continue

                if False: pass
                elif equip_info[ESPRITSET_TYPE_KEY] == MACHINE_TYPE_6300:
                    file_handler = self.file_handler_6300
                elif equip_info[ESPRITSET_TYPE_KEY] == MACHINE_TYPE_5550:
                    file_handler = self.file_handler_5550

                for target in file_handler.keys():
                    target_path = file_handler[target][FILE_HANDLER_EQUIP_FILE_PATH]

                    path_list = list()
                    if target_path[LAST_2_STR:] == "/*":
                        parent_path = os.path.dirname(target_path)
                        if not self.ftpCwd(parent_path): continue

                        child_dir_info_list = self.ftpList(parent_path)
                        for child_dir_info in child_dir_info_list:
                            if not child_dir_info[FTP_FILE_TYPE_KEY]:
                                path = os.path.join(parent_path, child_dir_info[FTP_FILE_NAME_KEY])
                                if not self.ftpCwd(path): continue
                                self.ftpList(path)

                    else:
                        if not self.ftpCwd(target_path): continue
                        self.ftpList(path)

                self.ftp.close()

                print("AAA")

                try:
                    self.log.info("FTP connect try: " + equip_info[ESPRITSET_LIP_KEY])
                    self.ftp.connect(host=equip_info[ESPRITSET_LIP_KEY], port=equip_info[ESPRITSET_DCDP_PORT], timeout=TIME_OUT)
                    self.log.info("FTP connect success.")
                    self.log.info("FTP login try: " + equip_info[ESPRITSET_FTP_USER])
                    self.ftp.login(user=equip_info[ESPRITSET_FTP_USER], passwd=equip_info[ESPRITSET_FTP_PASS])
                    self.log.info("FTP login success.")
                except all_errors as e:
                    self.log.error("FTP connection error: " + str(e))
                    continue

                self.getEquipBrtlFileList("/home/suomus/debug")

                self.ftp.close()
                return

    def exe(self):
        proc_time = time()
        self.log.info("[INFO] Start.")

        ### ... ###

        self.equip_valid = True
        self.equip_list.append({
            ESPRITSET_SN_KEY: "1234567",
            ESPRITSET_EIP_KEY: "192.168.11.142",
            ESPRITSET_LIP_KEY: "192.168.11.142",
            ESPRITSET_NAME_KEY: "HOME",
            ESPRITSET_TYPE_KEY: "6300ES6a",
            ESPRITSET_FTP_USER: "suomus",
            ESPRITSET_FTP_PASS: "1018",
            ESPRITSET_DCDP_PORT: 21,
            ESPRITSET_FILE_PORT: 21,
        })
        self.getEquipFileList()

        self.log.info("[INFO] It's finished.")
        self.log.info("[INFO] Proc time: " + str(round((time() - proc_time))) + "s")

def main():
    obj = InitCheckTool()
    obj.exe()

    return

    try:
        obj = InitCheckTool()
        obj.exe()
    except Exception as e:
        print(str(e))
        #self.log.error(str(e))

if __name__ == '__main__':
    main()
