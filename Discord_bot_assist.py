#!/user/bin/env python
# -*- coding: utf-8 -*-

import logging
import discord
import json
import re
import datetime
import concurrent.futures
import asyncio
from pprint import pprint
import os
from dotenv import load_dotenv
load_dotenv()

from assist_datetime.main import askLoki as askLoki_datetime

logging.basicConfig(level=logging.DEBUG)

scheduled_task = None  # Global variable to store the scheduled task
meet_instances = {} # Store meet instances

class meet():
    def __init__(self,time,repeat=False,participant=None):
        self.datetime =  time
        self.todoLIST = []
        self.channelIdINT = int(os.getenv("channel_id"))
        self.participant = ""
        self.task = None
        self.repeat = repeat
        self.participant = participant

    def start(self):
        if self.task is None:
            self.task = asyncio.create_task(self.notify())

    def cancel(self):
        if self.task:
            self.task.cancel()
            self.task = None

    def getDatetime(self):
        return self.datetime

    async def notify(self):
        now = datetime.datetime.now()
        await client.wait_until_ready()  # Ensure bot is logged in
        channel = client.get_channel(self.channelIdINT)  # Get the target channel

        wait_time = (self.datetime - now).total_seconds()
        print(f"Next message in {wait_time:.2f} seconds")

        while not client.is_closed():
            if self.datetime:
                try:
                    await asyncio.sleep(wait_time)  # Wait until the scheduled time
                    await channel.send("哈囉！我來提醒各位要開會囉")  # Send the message
                    print('Message sent')
                    self.cancel()
                except asyncio.CancelledError:
                    print("Scheduled message task was canceled.")
                    break  # Exit the loop if canceled

def checkDuplicateMeet(meetTimeSTR):
    if meetTimeSTR in meet_instances:
        return True
    else:
        return False

# Send msgSTR to multiple Loki project concurrently
def processMsg(msgSTR):
    proj = ""
    # Define the functions to run concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(getLokiResult, msgSTR, "datetime")
        """
        future2 = executor.submit(module2.func, msgSTR, "meet")
        future3 = executor.submit(module3.func, msgSTR, "record")
        """

        # Collect results
        results = [future.result() for future in concurrent.futures.as_completed([future1])]

    # Initialize final result dictionary
    final_result = {}

    for result in results:
            final_result.update(result)  # Merge the result

    return final_result

def getLokiResult(inputSTR, projSTR, filterLIST=[]):
    splitLIST = ["！", "，", "。", "？", "!", ",", "\n", "；", "\u3000", ";"] #
    # 設定參考資料
    refDICT = { # value 必須為 list
        #"key": []
    }

    if projSTR == "datetime":
        resultDICT = askLoki_datetime(inputSTR, filterLIST=filterLIST, splitLIST=splitLIST, refDICT=refDICT)
    elif projSTR == "meet":
        pass
    elif projSTR == "record":
        pass
    else:
        pass

    logging.debug("Loki Result => {}".format(resultDICT))
    return resultDICT

class BotClient(discord.Client):

    def resetMSCwith(self, messageAuthorID):
        '''
        清空與 messageAuthorID 之間的對話記錄
        '''
        templateDICT = {    "id": messageAuthorID,
                             "updatetime" : datetime.datetime.now(),
                             "latestQuest": "",
                             "latestIntent":[],
                             "false_count" : 0
        }
        return templateDICT

    async def on_ready(self):
        # ################### Multi-Session Conversation :設定多輪對話資訊 ###################
        self.templateDICT = {"updatetime" : None,
                             "latestQuest": ""
        }
        self.mscDICT = { #userid:templateDICT
        }
        # ####################################################################################
        print('Logged on as {} with id {}'.format(self.user, self.user.id))

    async def on_message(self, message):
        # Don't respond to bot itself. Or it would create a non-stop loop.
        # 如果訊息來自 bot 自己，就不要處理，直接回覆 None。不然會 Bot 會自問自答個不停。
        if message.author == self.user:
            return None

        logging.debug("收到來自 {} 的訊息".format(message.author))
        logging.debug("訊息內容是 {}。".format(message.content))
        if self.user.mentioned_in(message):
            replySTR = "我是預設的回應字串…你會看到我這串字，肯定是出了什麼錯！"
            logging.debug("本 bot 被叫到了！")
            msgSTR = message.content.replace("<@{}> ".format(self.user.id), "").strip()
            logging.debug("人類說：{}".format(msgSTR))
            if msgSTR == "ping":
                replySTR = "pong"
            elif msgSTR == "ping ping":
                replySTR = "pong pong"

# ##########初次對話：這裡是 keyword trigger 的。
            elif msgSTR.lower() in ["哈囉","嗨","你好","您好","hi","hello"]:
                #有講過話(判斷對話時間差)
                if message.author.id in self.mscDICT.keys():
                    timeDIFF = datetime.now() - self.mscDICT[message.author.id]["updatetime"]
                    #有講過話，但與上次差超過 5 分鐘(視為沒有講過話，刷新template)
                    if timeDIFF.total_seconds() >= 300:
                        self.mscDICT[message.author.id] = self.resetMSCwith(message.author.id)
                        replySTR = "嗨嗨，我們好像見過面，但卓騰的隱私政策不允許我記得你的資料，抱歉！"
                    #有講過話，而且還沒超過5分鐘就又跟我 hello (就繼續上次的對話)
                    else:
                        replySTR = self.mscDICT[message.author.id]["latestQuest"]
                #沒有講過話(給他一個新的template)
                else:
                    self.mscDICT[message.author.id] = self.resetMSCwith(message.author.id)
                    replySTR = msgSTR.title()

# ##########非初次對話：這裡用 Loki 計算語意
            else: #開始處理正式對話
                #從這裡開始接上 NLU 模型
                if message.author.id not in self.mscDICT.keys():
                    self.mscDICT[message.author.id] = self.resetMSCwith(message.author.id)
                resultDICT = processMsg(msgSTR)
                logging.debug("######\nLoki 處理結果如下：")
                logging.debug(resultDICT)
                try:
                    if resultDICT:
                        if "intent" not in resultDICT.keys():
                            replySTR = "抱歉，這好像跟我的工作無關，要閒聊請去找真人喔 <3"
                            self.mscDICT[message.author.id]["false_count"] += 1
                            if self.mscDICT[message.author.id]["false_count"] == 4:
                                replySTR = "你再吵一次我就不理你了喔！"
                            if self.mscDICT[message.author.id]["false_count"] >=5:
                                return None
                        elif resultDICT["intent"] != []:
                            replySTR = resultDICT["response"][0]
                            intentSTR = resultDICT["intent"][0]
                            self.mscDICT[message.author.id]["false_count"] = 0
                            # 預約會議
                            if intentSTR == "set":
                                if "time" in resultDICT["intent"]:
                                    meetDATETIME = resultDICT["time"][0][0]
                                    if checkDuplicateMeet(str(meetDATETIME)):
                                        replySTR = "該時段已經有會議了喔！"
                                    elif meetDATETIME < datetime.datetime.now():
                                        replySTR = "你預約的時間已經過了喔！"
                                    else:
                                        newMeet = meet(meetDATETIME,resultDICT["repeat"][0])
                                        newMeet.start()
                                        meet_instances[str(meetDATETIME)] = newMeet
                                        replySTR = replySTR.format(resultDICT["time"][0][1])
                                        self.mscDICT[message.author.id]["latestIntent"] = intentSTR
                                else:
                                    replySTR = "好勒，啊那什麼時候開會？"
                                    self.mscDICT[message.author.id]["latestIntent"] = intentSTR
                            
                            elif intentSTR == "time":
                                if self.mscDICT[message.author.id]["latestIntent"] == "set":
                                    meetDATETIME = resultDICT["time"][0][0]
                                    if checkDuplicateMeet(str(meetDATETIME)):
                                        replySTR = "該時段已經有會議了喔！"
                                    elif meetDATETIME < datetime.datetime.now():
                                        replySTR = "你預約的時間已經過了喔！"
                                    else:
                                        newMeet = meet(meetDATETIME)
                                        newMeet.start()
                                        meet_instances[str(meetDATETIME)] = newMeet
                                        replySTR = f"好的，我會提醒你{resultDICT['time'][0][1]}要開會！"
                                        
                            # 取消會議提醒
                            elif intentSTR == "cancel":
                                if checkDuplicateMeet(str(meetDATETIME)):
                                    meet_instances[str(meetDATETIME)].cancel()
                                    del meet_instances[str(meetDATETIME)]
                                    #print(meet_instances)
                                else:
                                    replySTR = "該時段沒有會議！"

                        else:
                            assistantSTR = "！"
                            userSTR = msgSTR
                            #replySTR = llmCall(accountDICT["username"], assistantSTR, userSTR)
                    else:
                        replySTR = "抱歉，這好像跟我的工作無關，要閒聊請去找真人喔 <3"
                        self.mscDICT[message.author.id]["false_count"] += 1

                except Exception as e:
                    replySTR = "我是預設的回應字串…你會看到我這串字，肯定是出了什麼錯！"
                    print(f"Error:{type(e).__name__}:{e}")

            await message.reply(replySTR)


if __name__ == "__main__":
    with open("account.info", encoding="utf-8") as f: #讀取account.info
        accountDICT = json.loads(f.read())
    client = BotClient(intents=discord.Intents.default())
    client.run(accountDICT["discord_token"])
