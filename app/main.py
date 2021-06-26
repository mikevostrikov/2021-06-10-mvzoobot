import os
import datetime
import requests
import boto3


ENV = os.getenv('ENV', 'dev')
AWS_SSM_PREFIX = os.getenv('AWS_SSM_PREFIX', '/2021-16-10-mvzoobot-dev')
TELEGRAM_BOT_API_TOKEN = None
TELEGRAM_CHAT_ID = None


def config():
    global TELEGRAM_BOT_API_TOKEN
    global TELEGRAM_CHAT_ID
    ssm_client = boto3.client('ssm')
    TELEGRAM_BOT_API_TOKEN =\
        ssm_client.get_parameter(
            Name=f'{AWS_SSM_PREFIX}/telegram-bot-api-token', WithDecryption=True
        )['Parameter']['Value']
    TELEGRAM_CHAT_ID =\
        int(ssm_client.get_parameter(
            Name=f'{AWS_SSM_PREFIX}/telegram-chat-id'
        )['Parameter']['Value'])
    print(f'Config: ENV={ENV}, AWS_SSM_PREFIX={AWS_SSM_PREFIX}, TELEGRAM_CHAT_ID={TELEGRAM_CHAT_ID}')


def find_closest_weekend_dates():
    now = datetime.datetime.utcnow() - datetime.timedelta(hours=4)
    today = now.date()
    if today.isoweekday() <= 5:
        next_friday = today + datetime.timedelta(days=5 - today.isoweekday())
    else:
        next_friday = today + datetime.timedelta(days=5)
    if today.isoweekday() <= 6:
        next_saturday = today + datetime.timedelta(days=6 - today.isoweekday())
    else:
        next_saturday = today + datetime.timedelta(days=6)
    next_sunday = today + datetime.timedelta(days=7 - today.isoweekday())
    next_next_saturday = next_saturday + datetime.timedelta(days=7)
    next_next_sunday = next_sunday + datetime.timedelta(days=7)
    next_next_friday = next_friday + datetime.timedelta(days=7)
    return sorted([next_saturday, next_sunday, next_next_saturday, next_next_sunday])


def check_availability():
    closest_weekend_dates = find_closest_weekend_dates()
    times_str = ['9:00AM', '9:15AM', '9:30AM', '9:45AM', '10:00AM', '10:15AM', '10:30AM', '10:45AM', '11:00AM']
    result_dict = {}
    # for every date check tickets available
    for dt in closest_weekend_dates:
        dt_str = dt.isoformat()
        result_dict[dt] = []
        response = requests.get(f'https://tickets.torontozoo.com/events/times/2071?selected-date={dt_str}')
        if response.status_code == 200:
            response_json = response.json()
            for availability_json in response_json:
                # filter only info for certain times:
                if availability_json['itemCode2'] in times_str:
                    time_str = availability_json['itemCode2']
                    available_quantity = availability_json['availableQuantity']
                    if available_quantity > 0:
                        result_dict[dt].append((time_str, available_quantity))
    return result_dict


def format_html(availability):
    chunks = []
    for dt in availability:
        if dt.isoweekday() == 1:
            wk_str = 'Mon'
        elif dt.isoweekday() == 2:
            wk_str = 'Tue'
        elif dt.isoweekday() == 3:
            wk_str = 'Wed'
        elif dt.isoweekday() == 4:
            wk_str = 'Thu'
        elif dt.isoweekday() == 5:
            wk_str = 'Fri'
        elif dt.isoweekday() == 6:
            wk_str = 'Sat'
        elif dt.isoweekday() == 7:
            wk_str = 'Sun'
        else:
            wk_str = f'{dt.isoweekday()}'

        dt_str = dt.isoformat() + " " + wk_str
        chunks.append(f"<b>{dt_str}</b>")
        if len(availability[dt]) == 0:
            chunks.append(" - &lt;3 tickets\n")
        else:
            chunks.append("\n")
            chunks.append("<pre>")
            for time_item in availability[dt]:
                chunks.append(f" {time_item[0][:-2]:>5} - {time_item[1]}\n")
            chunks.append("</pre>")
    return "".join(chunks)


def are_there_enough_tickets(availability):
    """'Enough' meaning there should be more than 2 tickets"""
    result = False
    for dt in availability:
        if sum(map(lambda x: x[1], availability[dt])) >= 3:
            result = True
    return result


def check_and_alert():
    availability = check_availability()
    print(availability)
    if are_there_enough_tickets(availability):
        availability_html = format_html(availability)
        alert(availability_html)


def alert(msg):
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    print(data)
    req = requests.post(
        url=f'https://api.telegram.org/bot{TELEGRAM_BOT_API_TOKEN}/sendMessage',
        json=data
    )
    # print(req.json())


def lambda_handler(event, lambda_context):
    config()
    check_and_alert()


if __name__ == '__main__':
    lambda_handler(None, None)
