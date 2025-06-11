from django.shortcuts import render

# Create your views here.
import json
import os
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest

JSON_FILE_PATH = 'C:/Users/user/Desktop/Python/assist_bot/backup.json'

def load_notifications():
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_notifications(notifications):
    with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(notifications, f, ensure_ascii=False, indent=4)

def index(request):
    notifications = load_notifications()
    return render(request, 'notifications/index.html', {'notifications': notifications})

def add_notification(request):
    if request.method == 'POST':
        datetime_key = request.POST['datetime']
        content = request.POST['content']
        participant = request.POST['participant']
        eventType = request.POST['eventType']
        repeat = request.POST.get('repeat') == 'on'
        repeatDelta = request.POST.get('repeatDelta')

        notifications = load_notifications()

        if datetime_key in notifications:
            return HttpResponseBadRequest("Notification with this datetime already exists.")

        notifications[datetime_key] = {
            "datetime": datetime_key,
            "todoLIST": [],
            "content": content,
            "channelID": 0,  # Default or fetched elsewhere
            "task": None,
            "repeat": repeat,
            "participant": participant,
            "eventType": eventType,
            "repeatDelta": repeatDelta
        }

        save_notifications(notifications)
        return redirect('index')
    return render(request, 'notifications/add.html')

def edit_notification(request, key):
    notifications = load_notifications()
    notification = notifications.get(key)
    if not notification:
        return redirect('index')

    if request.method == 'POST':
        notification['content'] = request.POST['content']
        notification['participant'] = request.POST['participant']
        notification['eventType'] = request.POST['eventType']
        notification['repeat'] = request.POST.get('repeat') == 'on'
        notification['repeatDelta'] = request.POST.get('repeatDelta')

        notifications[key] = notification
        save_notifications(notifications)
        return redirect('index')

    return render(request, 'notifications/edit.html', {'notification': notification, 'key': key})

def delete_notification(request, key):
    notifications = load_notifications()
    if key in notifications:
        del notifications[key]
        save_notifications(notifications)
    return redirect('index')
