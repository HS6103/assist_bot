#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
    Loki module for set

    Input:
        inputSTR      str,
        utterance     str,
        args          str[],
        resultDICT    dict,
        refDICT       dict,
        pattern       str

    Output:
        resultDICT    dict
"""

from importlib.util import module_from_spec
from importlib.util import spec_from_file_location
from random import sample
import json
import os
import datetime
import re

INTENT_NAME = "set"
CWD_PATH = os.path.dirname(os.path.abspath(__file__))

def import_from_path(module_name, file_path):
    spec = spec_from_file_location(module_name, file_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

MODULE_DICT = {
    "Account": import_from_path("assist_datetime_lib_Account", os.path.join(os.path.dirname(CWD_PATH), "lib/Account.py"))
}
"""
Account 變數清單
[變數] BASE_PATH         => 根目錄位置
[變數] LIB_PATH          => lib 目錄位置
[變數] INTENT_PATH       => intent 目錄位置
[變數] REPLY_PATH        => reply 目錄位置
[變數] ACCOUNT_DICT      => account.info 內容
[變數] ARTICUT           => ArticutAPI (用法：ARTICUT.parse()。 #需安裝 ArticutAPI.)
[變數] USER_DEFINED_FILE => 使用者自定詞典的檔案路徑
[變數] USER_DEFINED_DICT => 使用者自定詞典內容
"""
REPLY_PATH = MODULE_DICT["Account"].REPLY_PATH
ACCOUNT_DICT = MODULE_DICT["Account"].ACCOUNT_DICT
USER_DEFINED_DICT = MODULE_DICT["Account"].USER_DEFINED_DICT
ARTICUT = MODULE_DICT["Account"].ARTICUT

# userDefinedDICT (Deprecated)
# 請使用 Account 變數 USER_DEFINED_DICT 代替
#userDefinedDICT = {}
#try:
#    userDefinedDICT = json.load(open(os.path.join(CWD_PATH, "USER_DEFINED.json"), encoding="utf-8"))
#except:
#    pass

replyDICT = {}
replyPathSTR = os.path.join(REPLY_PATH, "reply_{}.json".format(INTENT_NAME))
if os.path.exists(replyPathSTR):
    try:
        replyDICT = json.load(open(replyPathSTR, encoding="utf-8"))
    except Exception as e:
        print("[ERROR] reply_{}.json => {}".format(INTENT_NAME, str(e)))
CHATBOT = True if replyDICT else False

# 將符合句型的參數列表印出。這是 debug 或是開發用的。
def debugInfo(inputSTR, utterance):
    if ACCOUNT_DICT["debug"]:
        print("[{}] {} ===> {}".format(INTENT_NAME, inputSTR, utterance))

# 將時間詞轉為 datetime 格式
def arg2Time(argSTR):
    articutResultDICT = ARTICUT.parse(argSTR, level= 'lv3')
    if articutResultDICT["time"] != [[]]:
        datetimeSTR = articutResultDICT["time"][0][0]["datetime"]
        if "晚" in argSTR:
            datetimeOBJ = datetime.datetime.strptime(datetimeSTR, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=12)
    else:
        datetimeOBJ = None

    return datetimeOBJ

def getReply(utterance, args):
    replySTR = ""
    try:
        replySTR = sample(replyDICT[utterance], 1)[0]
        if args:
            replySTR = replySTR.format(*args)
    except:
        pass

    return replySTR

def getResult(inputSTR, utterance, args, resultDICT, refDICT, pattern="", toolkitDICT={}):
    debugInfo(inputSTR, utterance)
    if utterance == "[這禮拜]要開會":
        if CHATBOT:
            replySTR = getReply(utterance, args)
            if replySTR:
                resultDICT["response"] = replySTR
                resultDICT["source"] = "reply"
        else:
            resultDICT["response"] = f"好的，我會提醒你{args[0]}要開會！"
            resultDICT["time"] = arg2Time(args[0])
            resultDICT["intent"] = INTENT_NAME

    return resultDICT


if __name__ == "__main__":
    from pprint import pprint

    resultDICT = getResult("這禮拜要開會", "[這禮拜]要開會", [], {}, {})
    pprint(resultDICT)