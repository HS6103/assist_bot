#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
名稱： Loki Intent Update Tool 3.0
作者： Droidtown
日期： 2022-06-13
信箱： info@droidtown.co
範例： Updater.py <new_intent_dir>
說明： Loki Intent Update Tool 3.0 會將新目錄 (new_intent_dir) 中的 Utterance 及
      UserDefined 更新至現在目錄中的 Loki 意圖檔 (Loki_{intent}.py)，
      並自動備份更新前的 Loki 意圖檔至 backup_{timestamp} 目錄中。

      注意：新增的 Loki 意圖檔需要使用者至 Project.py runLoki() 中加入呼叫程式碼！
"""

from argparse import ArgumentParser
from datetime import datetime
from importlib.util import module_from_spec
from importlib.util import spec_from_file_location
from shutil import copyfile
import os
import re

def import_from_path(module_name, file_path):
    spec = spec_from_file_location(module_name, file_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

CWD_PATH = os.path.dirname(os.path.abspath(__file__))
MODULE_DICT = {
    "Account": import_from_path("assist_record_lib_Account", os.path.join(CWD_PATH, "Account.py"))
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
INTENT_PATH = MODULE_DICT["Account"].INTENT_PATH

TIMESTAMP = datetime.utcnow().strftime("%Y%m%d%H%M%S")
BACKUP_FOLDER = "backup_{}".format(TIMESTAMP)
USER_DEFINED_NAME = "USER_DEFINED.json"

intentFilePAT = re.compile("^Loki_.+(?<!_updated)\.py$") #排除 1.0 產生的 _updted.py 檔案
intentFileNamePAT = re.compile("^Loki_(.+)\.py$")
utterancePAT = re.compile("if utterance == \".+\":$")
userDefinedPAT = re.compile("userDefinedDICT = (\{.*\})$")
endResultPAT = re.compile("^    return resultDICT$")


def updateUtterance(newIntentPath):
    # 取得目前目錄下的 intent
    intentFileLIST = sorted([f for f in os.listdir(newIntentPath) if intentFilePAT.search(f)])
    for intentFile in intentFileLIST:
        filePath = os.path.join(INTENT_PATH, intentFile)
        if os.path.exists(filePath):
            print("\n[{}]".format(intentFile))

            # 取出舊 intent 的所有內容
            sourceLIST = []
            with open(filePath, encoding="utf-8") as f:
                sourceLIST = f.readlines()

            # 移除結尾空白列
            while sourceLIST[-1] == "\n":
                sourceLIST = sourceLIST[:-1]

            # 取出舊 intent 中的句型
            intentLIST = []
            for source in sourceLIST:
                for g in utterancePAT.finditer(source):
                    intentLIST.append(g.group())

            # 取出新 intent 中的句型
            newIntentLIST = []
            with open(os.path.join(newIntentPath, intentFile), encoding="utf-8") as f:
                lineLIST = f.readlines()
                for line in lineLIST:
                    for g in utterancePAT.finditer(line):
                        newIntentLIST.append(g.group())

            # 新 intent 中的句型不存在於舊 intent 裡才更新
            updatedBOOL = False
            for newIntent in newIntentLIST:
                if newIntent not in intentLIST:
                    indexLIST = [i for i, source in enumerate(sourceLIST) if utterancePAT.search(source)]
                    if indexLIST:
                        indexINT = indexLIST[-1]
                    else:
                        indexLIST = [i for i, source in enumerate(sourceLIST) if endResultPAT.search(source)]
                        indexINT = indexLIST[-1]

                    sourceLIST.insert(indexINT, """    {}
        if CHATBOT:
            replySTR = getReply(utterance, args)
            if replySTR:
                resultDICT["response"] = replySTR
                resultDICT["source"] = "reply"
        else:
            # write your code here
            # resultDICT[key].append(value)
            pass

""".format(newIntent))

                    updatedBOOL = True
                    print("=> 新增 {}".format(newIntent))

            if updatedBOOL:
                try:
                    # 備份 intent
                    copyfile(filePath, os.path.join(INTENT_PATH, BACKUP_FOLDER, intentFile))
                    try:
                        # 更新 intent
                        f = open(filePath, "w", encoding="utf-8")
                        f.write("".join(sourceLIST))
                        f.close()
                        print("=> 更新成功")
                    except Exception as e:
                        print("=> 更新失敗 {}".format(str(e)))
                except Exception as e:
                    print("=> 備份失敗 {}".format(str(e)))
            else:
                print("=> 沒有新句型")

        else:
            # 新 intent 直接複製
            print("\n[新增 {}]".format(intentFile))
            try:
                copyfile(os.path.join(newIntentPath, intentFile), os.path.join(INTENT_PATH, intentFile))
                intentNameSTR = intentFileNamePAT.findall(intentFile)[0]
                print("=> 請在 Project.py 中加入以下的程式碼")
                print("from intent import Loki_{}\n".format(intentNameSTR))
                print("def runLoki(...):")
                print("    # {}".format(intentNameSTR))
                print("    if lokiRst.getIntent(index, resultIndex) == \"{}\":".format(intentNameSTR))
                print("        lokiResultDICT = Loki_{}.getResult(key, lokiRst.getUtterance(index, resultIndex), lokiRst.getArgs(index, resultIndex), lokiResultDICT, refDICT, pattern=lokiRst.getPattern(index, resultIndex), toolkitDICT=toolkitDICT)".format(intentNameSTR))
            except Exception as e:
                print("=> 新增失敗 {}".format(str(e)))

    return True

def updateUserDefined(newIntentPath):
    if os.path.exists(os.path.join(newIntentPath, USER_DEFINED_NAME)):
        # 2.0 使用 USER_DEFINED.json
        print("\n[{}]".format(USER_DEFINED_NAME))
        # 備份 UserDefined
        try:
            copyfile(os.path.join(INTENT_PATH, USER_DEFINED_NAME), os.path.join(INTENT_PATH, BACKUP_FOLDER, USER_DEFINED_NAME))
        except Exception as e:
            print("=> 備份失敗 {}".format(str(e)))
            return False

        # 更新 UserDefined
        try:
            copyfile(os.path.join(newIntentPath, USER_DEFINED_NAME), os.path.join(INTENT_PATH, USER_DEFINED_NAME))
            print("=> 更新成功")
        except Exception as e:
            print("=> 更新失敗 {}".format(str(e)))
            return False
    else:
        # 1.0 使用 intent 內的 userDefinedDICT
        # 取得目前目錄下的 intent
        intentFileLIST = sorted([f for f in os.listdir(INTENT_PATH) if intentFilePAT.search(f)])

        # 讀取 UserDefined
        userDefinedSTR = ""
        for intentFile in intentFileLIST:
            if os.path.exists(os.path.join(newIntentPath, intentFile)):
                flagBOOL = False
                with open(os.path.join(newIntentPath, intentFile), encoding="utf-8") as f:
                    lineLIST = f.readlines()
                    for line in lineLIST:
                        for g in userDefinedPAT.finditer(line):
                            try:
                                userDefinedSTR = line
                                flagBOOL = False
                                break
                            except:
                                pass

                if flagBOOL:
                    break

        # 更新所有 intent 的 userDefinedDICT
        for intentFile in intentFileLIST:
            print("\n[{}]".format(intentFile))

            # 取出舊 intent 的所有內容
            sourceLIST = []
            with open(os.path.join(INTENT_PATH, intentFile), encoding="utf-8") as f:
                sourceLIST = f.readlines()

            # 更新 UserDefined
            for i, source in enumerate(sourceLIST):
                if userDefinedPAT.search(source):
                    sourceLIST[i] = userDefinedSTR
                    break

            # 備份 intent
            if not os.path.exists(os.path.join(INTENT_PATH, BACKUP_FOLDER, intentFile)):
                try:
                    copyfile(os.path.join(INTENT_PATH, intentFile), os.path.join(INTENT_PATH, BACKUP_FOLDER, intentFile))
                except Exception as e:
                    print("=> 備份失敗 {}".format(str(e)))
                    continue

            try:
                # 更新 intent
                f = open(os.path.join(INTENT_PATH, intentFile), "w", encoding="utf-8")
                f.write("".join(sourceLIST))
                f.close()
                print("=> 更新成功")
            except Exception as e:
                print("=> 更新失敗 {}".format(str(e)))

    return True

if __name__ == "__main__":
    progSTR = "Loki Intent Update Tool 2.0"
    usageSTR = "\nUpdater.py <new_intent_dir>"
    descriptionSTR = """
    Loki Intent Update Tool 2.0 會將新目錄 (new_intent_dir) 中的 Utterance 及 UserDefined 更新至現在目錄中的 Loki 意圖檔 (Loki_{intent}.py)，
    並自動備份更新前的 Loki 圖檔至 backup_{timestamp} 目錄中。

    注意：新增的 Loki 意圖檔需要使用者至 Project.py 中加入呼叫程式碼！
    """
    argParser = ArgumentParser(prog=progSTR, usage=usageSTR, description=descriptionSTR, epilog=None)
    # Updater 1.0
    argParser.add_argument("-o", "--old-intent-dir", required=False, help="Old intent(s) directory", dest="oldIntentDirectory")
    argParser.add_argument("-n", "--new-intent-dir", required=False, help="New intent(s) directory", dest="newIntentDirectory")
    # Updater 2.0
    argParser.add_argument("new_intent_dir", nargs="?", default="", help="New intent directory")
    args = argParser.parse_args()

    newIntentPath = None
    if args.new_intent_dir:
        newIntentPath = args.new_intent_dir
    if args.newIntentDirectory:
        newIntentPath = args.newIntentDirectory

    if newIntentPath:
        if os.path.exists(newIntentPath):
            # 取得新目錄完整路徑
            newIntentPath = os.path.abspath(newIntentPath)
            if os.path.isdir(newIntentPath):
                print("新 Intent 目錄 {}".format(newIntentPath))
                # 建立備份資料夾
                os.mkdir(os.path.join(INTENT_PATH, BACKUP_FOLDER))
                print("備份目錄 {}".format(os.path.join(INTENT_PATH, BACKUP_FOLDER)))
                print("\n--------------------")

                # 檢查 Utterance
                print("\n[1] 檢查 Utterance")
                updateUtterance(newIntentPath)
                print("\n--------------------")

                # 檢查 UserDefined
                print("\n[2] 檢查 UserDefined")
                updateUserDefined(newIntentPath)

                print("\n--------------------\n\n作業完成")
            else:
                print("{} 不是有效的目錄".format(newIntentPath))
        else:
            print("{} 不是有效的路徑".format(newIntentPath))
    else:
        argParser.print_help()