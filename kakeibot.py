"""
家計簿ボットアプリ
"""

import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request

app = Flask(__name__)

ACCESS_TOKEN = 'EAAi6HZC8lnUIBAMZCSVd8sDkRe6YSi58nlsoAHbAgGyzsbKssZBShgj3TCRS7L5Om62x0GRVLwcN9jVggpK8pqRzBFiiRIpmZBN2oMnH6FaNGVBy2JLsthUS83gMgNObpVwZBkOaUwJmNmJYbNIh2USZAClN68f3G2J6jacz0PfQZDZD'
VERIFY_TOKEN = 'Verify_Token_Dev'

genres = []
prices = []
dates = []

def send_get_started():
    params = {
        "access_token": ACCESS_TOKEN  # os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "get_started": {
            "payload": "Welcome!"
        },
        "greeting": [
            {
                "locale": "default",
                "text": "家計簿ボットアプリ"
            }
        ]
    })

    requests.post("https://graph.facebook.com/v2.6/me/messenger_profile", params=params, headers=headers, data=data)


send_get_started()

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN: # os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
#    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message
                    """
                        ユーザからメッセージが送られた時に実行される
                    """

                    global genres
                    global prices
                    global dates

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    if '、' in message_text:
                        split_message_texts = message_text.split('、')
                        genres.append(split_message_texts[0])
                        prices.append(int(split_message_texts[1]))
                        dates.append(datetime.now())

                        text = '今月の合計はこちら'
                        buttons = ['今月の合計はこちら']
                        send_quick_reply(sender_id, text, buttons)

                    elif message_text == '今月の合計はこちら':
                        genre_list = list(set(genres))
                        total = []
                        for genre in genre_list:
                            total_child = []
                            for index, genre_child in enumerate(genres):
                                if genre_child == genre:
                                    total_child.append(prices[index])
                            total.append(total_child)

                        for index, genre in enumerate(genre_list):
                            total_price = sum(total[index])
                            text = '{} : {}'.format(genre, total_price)
                            send_message(sender_id, text)

                        text = 'また追加するときは、「ジャンル、値段」みたいに入れてね！'
                        send_message(sender_id, text)

                    elif message_text == 'リセット':
                        genres.clear()
                        prices.clear()
                        dates.clear()

                        text = 'すべてリセットしたよ！'
                        send_message(sender_id, text)



                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    """
                        「スタート」を押した時に実行される
                        ユーザがボットと会話を初めて開始した時
                    """

                    sender_id = messaging_event["sender"]["id"]
                    text = 'これから楽しく家計簿をつけましょう！'
                    send_message(sender_id, text)
                    text = '例えばこんな感じで記録してね！'
                    send_message(sender_id, text)
                    text = 'お菓子、320'
                    send_message(sender_id, text)
                    text = '「ジャンル、値段」みたいに句読点が重要だよ！'
                    send_message(sender_id, text)


    return "ok", 200


def send_message(recipient_id, message_text):

#    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": ACCESS_TOKEN # os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text,
        }
    })

    """
    ここでrequests.postを実行した時点で指定urlにリクエストを送信し、
    botがメッセージを送信している
    """
    requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)

#    if r.status_code != 200:
#        log(r.status_code)
#        log(r.text)


def send_quick_reply(recipient_id, text, buttons):

    """
    :param recipient_id: string
    :param text: string
    :param buttons: list; string
    :return: post
    """

    params = {
        "access_token": ACCESS_TOKEN  # os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }

    quick_replies = []

    for button in buttons:
        quick_dict = {
            "content_type": "text",
            "title": button,
            "payload": "payload: {}".format(button)
        }
        quick_replies.append(quick_dict)

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": text,
            "quick_replies": quick_replies
        }
    })

    requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)

def send_url_image(recipient_id, title, subtitle, url_str, image_url):
    """
    :param recipient_id: string: bot送信する相手のID
    :param title: string: タイトル
    :param subtitle: string: サブタイトル
    :param url: string: リンク先のURL
    :param url_image: string: サムネイル画像が格納されているURL
    :return: POSTリクエスト
    """

    params = {
        "access_token": ACCESS_TOKEN  # os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": title,
                            "image_url": image_url,
                            "subtitle": subtitle,
                            "buttons": [
                                {
                                    "type":  "web_url",
                                    "url": url_str,
                                    "title": "View Website"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    })

    requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)


"""
def log(msg):# , *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        #else:
        #    msg = unicode(msg).format(*args, **kwargs)
        #print(u"{}: {}".format(datetime.now(), msg))
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()
"""

if __name__ == '__main__':
    #    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)