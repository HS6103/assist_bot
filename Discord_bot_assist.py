#!/user/bin/env python
# -*- coding: utf-8 -*-

import logging
import discord
import json
import atexit
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
alarm_instances = {} # Store alarm instances
class notification():
    def __init__(self,time,repeat=False,participant="@everyone",eventTypeSTR="alarm",contentSTR=""):
        self.datetime =  time
        self.todoLIST = []
        self.channelID = int(os.getenv("channel_id"))
        self.task = None
        self.repeat = repeat
        self.participant = participant
        self.eventType = eventTypeSTR
        self.content = contentSTR
    
    def __getattribute__(self, name):
        try:
            # Attempt to get the attribute using the default behavior
            return super().__getattribute__(name)
        except AttributeError:
            # Handle the case where the attribute does not exist
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def start(self):
        if self.task is None:
            self.task = asyncio.create_task(self.notify())
            if self.eventType == "meet":
                meet_instances[str(self.datetime)] = self
            else:
                alarm_instances[str(self.datetime)] = self

    def cancel(self):
        if self.task:
            if self.repeat == True:
                self.setRepeat()
            self.task.cancel()
            self.task = None
        if self in meet_instances.values():
            # Remove the instance from meet_instances after sending the notification
            del meet_instances[str(self.datetime)]
        else:
            # Remove the instance from alarm_instances after sending the notification
            del alarm_instances[str(self.datetime)]



    def setRepeat(self):
            newTime = self.datetime + datetime.timedelta(weeks=1)  # 預設是週會，一週重複一次
            newmeet = notification(newTime, repeat=True)
            newmeet.start()
    
    def resetDatetime(self,newTime):
        self.datetime = newTime

    # Method to convert the Notification object to a dictionary, which can be saved to JSON
    def to_dict(self):
        # Convert datetime to string for JSON serialization
        return {
            "datetime": self.datetime.strftime("%Y-%m-%d %H:%M:%S"),  # Format as a string
            "todoLIST": self.todoLIST,
            "channelID": self.channelID,
            "task": None,
            "repeat": self.repeat,
            "participant": self.participant,
            "eventType": self.eventType
        }

    async def notify(self):
        now = datetime.datetime.now()
        await client.wait_until_ready()  # Ensure bot is logged in
        channel = client.get_channel(self.channelID)  # Get the target channel
        
        wait_time = (self.datetime - now).total_seconds()
        if wait_time <= 0:
            self.resetDatetime(self.datetime + datetime.timedelta(weeks=1))
            print(self.getDatetime())
            wait_time = (self.datetime - now).total_seconds()

        while not client.is_closed():
            if self.datetime:
                try:
                    print(f"Notification for {str(self.datetime)} ready")
                    await asyncio.sleep(wait_time)  # Wait until the scheduled time
                    if self.eventType == "meet":
                        await channel.send(f"哈囉！我來提醒{self.participant}要開會囉")  # Send the message
                    elif self.eventType == "alarm":
                        await channel.send(f"哈囉！我來提醒{self.participant} 「{self.content}」！")
                    self.cancel()
                    print(f'Notification for {str(self.datetime)} sent')
                    
                except asyncio.CancelledError:
                    print("Scheduled message task was canceled.")
                    break  # Exit the loop if canceled

# Function to save set alarms / meets to a JSON file
def save_notifications():
    # Convert all Notification objects to dictionaries
    notifications_data = {key: value.to_dict() for key, value in meet_instances.items()}
    alarm_data = {key: value.to_dict() for key, value in alarm_instances.items()}
    
    with open("backup.json", "w") as json_file:
        json.dump(notifications_data, json_file, indent=4)
    print("Notifications saved to backup.json")

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
        "response":[],
        "time":[],
        "intent":[],
        "repeat":[],
        "participant":[],
        "content":[]
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
                        # 不符合任何意圖
                        if resultDICT["intent"] == []: 
                            replySTR = "抱歉，我看不太懂你要我做什麼，要閒聊請去找真人喔 <3"
                            self.mscDICT[message.author.id]["false_count"] += 1
                        else:
                            replySTR = resultDICT["response"][0]
                            intentSTR = resultDICT["intent"][0]
                            self.mscDICT[message.author.id]["false_count"] = 0
                            # 會議預約 + 一般提醒
                            if "set_adv" in resultDICT["intent"] and "meet_adv" in resultDICT["intent"]:
                                repeatBOOL = resultDICT["repeat"][0]
                                if "time" in resultDICT["intent"]:
                                    alarmDATETIME = resultDICT["time"][0][0]
                                    if alarmDATETIME < datetime.datetime.now():
                                        if repeatBOOL == False:
                                            replySTR = "你預約的時間已經過了喔！"
                                        else:
                                            alarmDATETIME += datetime.timedelta(weeks=1)
                                            newMeet = notification(alarmDATETIME,repeatBOOL,eventTypeSTR="meet")
                                            newMeet.start()
                                            print(meet_instances)
                                            replySTR = replySTR.format(resultDICT["time"][0][1])
                                    else:
                                        newMeet = notification(alarmDATETIME,repeatBOOL,eventTypeSTR="meet")
                                        newMeet.start()
                                        print(meet_instances)
                                        replySTR = replySTR.format(resultDICT["time"][0][1])
                                else:
                                    replySTR = "好勒，啊那什麼時候開會？"

                            # 純會議提醒
                            elif "meet_adv" in resultDICT["intent"]:
                                repeatBOOL = resultDICT["repeat"][0]
                                if "time" in resultDICT["intent"]:
                                    alarmDATETIME = resultDICT["time"][0][0]
                                    if checkDuplicateMeet(str(alarmDATETIME)):
                                        replySTR = "該時段已經有預約會議提醒了喔！"
                                    elif alarmDATETIME < datetime.datetime.now():
                                        if repeatBOOL == False:
                                            replySTR = "你預約的時間已經過了喔！"
                                        else:
                                            alarmDATETIME += datetime.timedelta(weeks=1)
                                            newMeet = notification(alarmDATETIME,repeatBOOL,eventTypeSTR="meet")
                                            newMeet.start()
                                            print(meet_instances)
                                            self.mscDICT[message.author.id]["latestIntent"] = intentSTR
                                            replySTR = replySTR.format(resultDICT["time"][0][1])
                                    else:
                                        newMeet = notification(alarmDATETIME,repeatBOOL,eventTypeSTR="meet")
                                        newMeet.start()
                                        print(meet_instances)
                                        self.mscDICT[message.author.id]["latestIntent"] = intentSTR
                                        replySTR = replySTR.format(resultDICT["time"][0][1])
                                else:
                                    self.mscDICT[message.author.id]["latestIntent"] = intentSTR
                                    replySTR = "好勒，啊那什麼時候開會？"
                            
                            # 純一般提醒
                            elif "set_adv" in resultDICT["intent"]:
                                if "time" in resultDICT["intent"] and resultDICT["time"][0][0] != []:
                                    alarmDATETIME = resultDICT["time"][0][0]
                                    replySTR = replySTR.format(resultDICT["time"][0][1])
                                    newAlarm = notification(alarmDATETIME)
                                    newAlarm.start()
                                    print(alarm_instances)
                                    self.mscDICT[message.author.id]["latestIntent"] = intentSTR
                                else:
                                    self.mscDICT[message.author.id]["latestIntent"] = intentSTR
                                    pass  # 'response': ['請問什麼時候要提醒您呢？']
                            
                            
                            elif intentSTR == "time":
                                alarmDATETIME = resultDICT["time"][0][0]
                                latestIntent = self.mscDICT[message.author.id]["latestIntent"]
                                if latestIntent == "meet_adv":
                                    if checkDuplicateMeet(str(alarmDATETIME)):
                                        replySTR = "該時段已經有會議了喔！"
                                    elif alarmDATETIME < datetime.datetime.now():
                                        replySTR = "你預約的時間已經過了喔！"
                                    else:
                                        newMeet = notification(alarmDATETIME)
                                        newMeet.start()
                                        print(meet_instances)
                                        replySTR = f"好的，我會提醒你{resultDICT['time'][0][1]}要開會!"
                                        self.mscDICT[message.author.id]["latestIntent"] = intentSTR

                                elif latestIntent == "cancel":
                                    if checkDuplicateMeet(str(alarmDATETIME)):
                                        meet_instances[str(alarmDATETIME)].cancel()
                                        del meet_instances[str(alarmDATETIME)]
                                        print(meet_instances)
                                        replySTR = f"好的，已經幫你取消{resultDICT['time'][0][1]}的提醒！"
                                        self.mscDICT[message.author.id]["latestIntent"] = intentSTR

                                
                                elif latestIntent == "set_adv":
                                    if alarmDATETIME < datetime.datetime.now():
                                        replySTR = "你預約的時間已經過了喔！"
                                    else:
                                        newAlarm = notification(alarmDATETIME)
                                        newAlarm.start()
                                        print(alarm_instances)
                                        replySTR = f"好的，我會在{resultDICT['time'][0][1]}提醒你！"
                                        self.mscDICT[message.author.id]["latestIntent"] = intentSTR


                                else:
                                    replySTR = "抱歉，我看不懂你給我那個時間要做什麼！"
                                    self.mscDICT[message.author.id]["false_count"] += 1
                                    
                            # 取消會議提醒
                            elif intentSTR == "cancel":
                                if "time" in resultDICT["intent"]:
                                    alarmDATETIME = resultDICT["time"][0][0]
                                    if checkDuplicateMeet(str(alarmDATETIME)):
                                        meet_instances[str(alarmDATETIME)].cancel()
                                        del meet_instances[str(alarmDATETIME)]
                                        replySTR = replySTR.format(resultDICT["time"][0][1])
                                        print(meet_instances)
                                    else:
                                        replySTR = "該時段沒有會議！"
                                else:
                                    replySTR = "你要取消什麼時候的會議呢？"

                        # Nonsense Handling :)
                        if self.mscDICT[message.author.id]["false_count"] == 4:
                            replySTR = "你再吵一次我就不理你了喔！"
                        if self.mscDICT[message.author.id]["false_count"] >=5:
                            return None

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
    atexit.register(save_notifications)
