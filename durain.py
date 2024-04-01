import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import requests
from datetime import datetime
import time
import json
import os
import sys
import threading
import configparser

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

dir_path = 'tmp'

if not os.path.exists(dir_path):
    os.mkdir(dir_path)

name = os.environ.get('NAME', '')
pwd = ""
ApiKey = os.environ.get('APIKEY', '')
bot_token = os.environ.get('BOT_TOKEN', '')
authorized_users = os.environ.get('AUTHORIZED_USERS', '')
authorized_users_list = [int(uid) for uid in authorized_users.split(',') if uid.strip()]

pid = ""

cuy = ""

pn = ""

bot = None

endpoint_account = f"http://api.drncloud.com/out/ext_api/getUserInfo?name={name}&pwd={pwd}&ApiKey={ApiKey}"
endpoint_phone = f"http://api.drncloud.com/out/ext_api/getMobile?name={name}&pwd={pwd}&ApiKey={ApiKey}&cuy={cuy}&pid={pid}&num=1&noblack=0&serial=2&secret_key=null&vip=null"
endpoint_code = f"http://api.drncloud.com/out/ext_api/getMsg?name={name}&pwd={pwd}&ApiKey={ApiKey}&pn={pn}&pid={pid}&serial=2"
endpoint_release = f"http://api.drncloud.com/out/ext_api/passMobile?name={name}&pwd={pwd}&ApiKey={ApiKey}&pn=+{pn}&pid={pid}&serial=2"

sys_status = False

def reboot_done():
    """This function sends a message to the user when the reboot is done"""
    try:
        with open("tmp/reboot_chat_id.txt", "r") as f:
            bot = telegram.Bot(token=bot_token)
            chat_id = f.read()
            reboot_done_msg = "重启完毕。"
            bot.send_message(chat_id, reboot_done_msg)
    except:
        pass

reboot_done()

def authorized_check(update):
    global bot
    chat_id = update.message.chat_id
    if chat_id not in authorized_users_list:
        # If the user is not authorized, send an error message
        logging.warning("Unauthorized user %s (id=%d, %s) attempted to use the bot at %s", update.message.from_user.username, update.message.from_user.id, update.message.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        error_message = "你没有使用此 BOT 的权限，跪安吧！！！"
        bot.send_message(chat_id, error_message)
        return False
    return True

def start(update, context):
    if not authorized_check(update):
        return

    global sys_status
    user = update.message.from_user
    keyboard = [[InlineKeyboardButton("开启", callback_data='sys_on'),
                 InlineKeyboardButton("关闭", callback_data='sys_off'),
                 InlineKeyboardButton("账户", callback_data="account")],
                [InlineKeyboardButton("Gmail", callback_data='gmail'),
                 InlineKeyboardButton("Gv", callback_data='googlevoice'),
                 InlineKeyboardButton("Netfilx", callback_data='netfilx')],
                [InlineKeyboardButton("Aws", callback_data='aws'),
                 InlineKeyboardButton("Azure", callback_data='azure'),
                 InlineKeyboardButton("Linode", callback_data='linode')],
                [InlineKeyboardButton("Paypal", callback_data='paypal'),
                 InlineKeyboardButton("TG", callback_data='telegram'),
                 InlineKeyboardButton("Dynadot", callback_data='dynadot')],
                [InlineKeyboardButton("Win365", callback_data='Windows 365'),
                 InlineKeyboardButton("验证码", callback_data='verification_code'),
                 InlineKeyboardButton("重启", callback_data='reboot')],]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('发送 /help 获取帮助信息\n请选择：', reply_markup=reply_markup)
    # add buttons to user_data
    #context.user_data['start_buttons'] = keyboard
    logging.info("Start command called by %s (id=%d, %s) at %s", update.message.from_user.username, update.message.from_user.id, update.message.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def country_menu(update, context):
    query = update.callback_query
    global sys_status
    keyboard = [[InlineKeyboardButton("美国", callback_data='us'),
                 InlineKeyboardButton("加拿大", callback_data='ca'),
                 InlineKeyboardButton("墨西哥", callback_data='mx')],
                [InlineKeyboardButton("澳大利亚", callback_data='au'),
                 InlineKeyboardButton("香港", callback_data='hk'),
                 InlineKeyboardButton("台湾", callback_data='tw')],
                [InlineKeyboardButton("日本", callback_data='jp'),
                 InlineKeyboardButton("新加坡", callback_data='sg'),
                 InlineKeyboardButton("马来西亚", callback_data='my')],
                [InlineKeyboardButton("泰国", callback_data='th'),
                 InlineKeyboardButton("印度尼西亚", callback_data='id'),
                 InlineKeyboardButton("菲律宾", callback_data='ph')],
                [InlineKeyboardButton("英国", callback_data='gb'),
                 InlineKeyboardButton("法国", callback_data='fr'),
                 InlineKeyboardButton("意大利", callback_data='it')],
                [InlineKeyboardButton("德国", callback_data='de'),
                 InlineKeyboardButton("荷兰", callback_data='nl'),
                 InlineKeyboardButton("尼日利亚", callback_data='ng')],
                [InlineKeyboardButton("西班牙", callback_data='es'),
                 InlineKeyboardButton("南非", callback_data='za'),
                 InlineKeyboardButton("土耳其", callback_data='tr')],
                [InlineKeyboardButton("挪威", callback_data='no'),
                 InlineKeyboardButton("爱尔兰", callback_data='ie'),
                 InlineKeyboardButton("埃及", callback_data='eg')],
                [InlineKeyboardButton("验证码", callback_data='verification_code')],]
    # add start and gmail buttons to reply_markup if they exist
    #if 'start_buttons' in context.user_data:
    #    keyboard = context.user_data['start_buttons'] + keyboard
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text="请选择国家:", reply_markup=reply_markup)
    logging.info("Country Menu called by %s (id=%d, %s) at %s", query.from_user.username, query.from_user.id, query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def reboot(update, context):
    query = update.callback_query
    bot = context.bot
    chat_id = update.callback_query.message.chat_id
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/reboot_chat_id.txt", "w") as f:
        f.write(str(chat_id))
    logging.info("User %s (id=%d, %s) selected the Reboot option at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    python = sys.executable
    os.execl(python, python, * sys.argv)

def verification_code(update, context):
    query = update.callback_query
    bot = context.bot
    chat_id = update.callback_query.message.chat_id
    logging.info("User %s (id=%d, %s) selected the 验证码 option at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if sys_status:
        query.answer()
        with open("tmp/liulian_functions.txt", "r") as f:
            liulian_functions = f.read()
        with open("tmp/country.txt", "r") as f:
            country_code = f.read()
            if country_code == 'us':
                display_country = "美国"
            elif country_code == 'ca':
                display_country = "加拿大"
            elif country_code == 'mx':
                display_country = "墨西哥"
            elif country_code == 'au':
                display_country = "澳大利亚"
            elif country_code == 'hk':
                display_country = "香港"
            elif country_code == 'tw':
                display_country = "台湾"
            elif country_code == 'jp':
                display_country = "日本"      
            elif country_code == 'sg':
                display_country = "新加坡"
            elif country_code == 'my':
                display_country = "马来西亚"
            elif country_code == 'th':
                display_country = "泰国"
            elif country_code == 'id':
                display_country = "印度尼西亚"
            elif country_code == 'ph':
                display_country = "菲律宾"
            elif country_code == 'gb':
                display_country = "英国"
            elif country_code == 'fr':
                display_country = "法国"
            elif country_code == 'it':
                display_country = "意大利"
            elif country_code == 'de':
                display_country = "德国"
            elif country_code == 'nl':
                display_country = "荷兰"
            elif country_code == 'ng':
                display_country = "尼日利亚"
            elif country_code == 'es':
                display_country = "西班牙"
            elif country_code == 'za':
                display_country = "南非"
            elif country_code == 'tr':
                display_country = "土耳其"
            elif country_code == 'no':
                display_country = "挪威"
            elif country_code == 'ie':
                display_country = "爱尔兰"
            elif country_code == 'eg':
                display_country = "埃及"
            else:
                display_country = ""

        message_text = "{} {} 获取验证码中...".format(liulian_functions, display_country)
        bot.send_message(chat_id=chat_id, text=message_text)

        def code_thread():
            while sys_status:
                for i in range(12):
                    if not sys_status:
                        break
                    try:
                        with open("tmp/pid_code.txt", "r") as f:
                            pid_code = f.read()
                    except:
                        message_text = "警告：获取到手机号后再获取验证码。"
                        bot.send_message(chat_id=chat_id, text=message_text)
                        break
                    try:
                        with open("tmp/phone_number.txt", "r") as f:
                            pn_code = f.read()
                    except:
                        message_text = "警告：获取到手机号后再获取验证码。"
                        bot.send_message(chat_id=chat_id, text=message_text)
                        break
                    with open("tmp/liulian_functions.txt", "r") as f:
                        liulian_functions = f.read()
                    logging.info(f"这是手机号 %s 获取 %s 第{i+1}个验证码log. %s", pn_code, liulian_functions, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    endpoint_verification_code = endpoint_code.replace("pid=" + pid, "pid=" + pid_code).replace("pn=" + pn, "pn=" + pn_code)
                    response = requests.get(endpoint_verification_code)
                    verification_code_info = response.json()
                    verification_code_status_code = verification_code_info['code']
                    if verification_code_status_code == 200:
                        message_text = "验证码：\n"
                        message_text += "`{}`".format(verification_code_info['data'])
                        bot.send_message(chat_id=chat_id, text=message_text, parse_mode=telegram.ParseMode.MARKDOWN)
                        break
                    elif i+1 == 12:
                        message_text = "未获取到验证码，请再点击验证码按钮重新获取\n获取2-3验证码后，还是未获取到验证码，请重新获取手机号"
                        bot.send_message(chat_id=chat_id, text=message_text)
                        break
                    time.sleep(5)
                if verification_code_status_code == 200:
                    break
                elif i+1 == 12:
                    break
                elif not sys_status:
                    break

        t = threading.Thread(target=code_thread)
        t.start()
    else:
        txt = "请先开启系统"
        query.answer(txt)

def sys_off(update, context):
    query = update.callback_query
    bot = context.bot
    chat_id = update.callback_query.message.chat_id
    system_off_message = "系统已关闭"
    query.answer(system_off_message)
    global sys_status
    sys_status = False

def account(update, context):
    query = update.callback_query
    bot = context.bot
    chat_id = update.callback_query.message.chat_id
    query.answer("正在处理请求，请稍候...")
    response = requests.get(endpoint_account)
    account_info = response.json()
    account_status_code = account_info['code']
    if account_status_code == 200:
        message_text = "账户信息如下：\n"
        message_text += "用户名: {}\n".format(account_info['data']['username'])
        message_text += "积分: {}\n".format(account_info['data']['score'])
        message_text += "日期: {}".format(account_info['data']['create_date'])
    elif account_status_code == 800:
        message_text = "账号被封禁"
    elif account_status_code == 802:
        message_text = "用户名或密码错误"
    elif account_status_code == 803:
        message_text = "用户名和密码不能为空"
    bot.send_message(chat_id=chat_id, text=message_text)
    logging.info("User %s (id=%d, %s) selected the 账户 option at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def get_number(update, context):
    query = update.callback_query
    bot = context.bot
    chat_id = update.callback_query.message.chat_id
    try:
        with open("tmp/liulian_functions.txt", "r") as f:
            liulian_functions = f.read()
    except:
        pass
    try:
        with open("tmp/country.txt", "r") as f:
            country_code = f.read()
            if country_code == 'us':
                display_country = "美国"
            elif country_code == 'ca':
                display_country = "加拿大"
            elif country_code == 'mx':
                display_country = "墨西哥"
            elif country_code == 'au':
                display_country = "澳大利亚"
            elif country_code == 'hk':
                display_country = "香港"
            elif country_code == 'tw':
                display_country = "台湾"
            elif country_code == 'jp':
                display_country = "日本"
            elif country_code == 'sg':
                display_country = "新加坡"
            elif country_code == 'my':
                display_country = "马来西亚"
            elif country_code == 'th':
                display_country = "泰国"
            elif country_code == 'id':
                display_country = "印度尼西亚"
            elif country_code == 'ph':
                display_country = "菲律宾"
            elif country_code == 'gb':
                display_country = "英国"
            elif country_code == 'fr':
                display_country = "法国"
            elif country_code == 'it':
                display_country = "意大利"
            elif country_code == 'de':
                display_country = "德国"
            elif country_code == 'nl':
                display_country = "荷兰"
            elif country_code == 'ng':
                display_country = "尼日利亚"
            elif country_code == 'es':
                display_country = "西班牙"
            elif country_code == 'za':
                display_country = "南非"
            elif country_code == 'tr':
                display_country = "土耳其"
            elif country_code == 'no':
                display_country = "挪威"
            elif country_code == 'ie':
                display_country = "爱尔兰"
            elif country_code == 'eg':
                display_country = "埃及"
            else:
                display_country = ""
    except:
        pass
    logging.info("User %s (id=%d, %s) selected the %s option at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, liulian_functions, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if sys_status:
        message_text = "{} {} 获取号码中...".format(liulian_functions, display_country)
        bot.send_message(chat_id=chat_id, text=message_text)
        try:
            with open("tmp/phone_number.txt", "r") as f:
                pn_code = f.read()
            try:
                with open("tmp/pid_code.txt", "r") as f:
                    pid_code = f.read()
                    endpoint_release_new = endpoint_release.replace("pid=" + pid, "pid=" + pid_code).replace("pn=" + pn, "pn=" + pn_code)
                    response = requests.get(endpoint_release_new)
                    release_info = response.json()
                    release_status_code = (release_info['code'])
                    if release_status_code == 200:
                        logging.info("User %s (id=%d, %s) released phone number %s at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, pn_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        os.remove('tmp/phone_number.txt')
                    else:
                        logging.info("User %s (id=%d, %s) failed to release phone number %s at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, pn_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            except:
                pass
        except:
            pass

        def get_number_thread():
            global sys_status
            count = 1
            while sys_status:
                global pid
                global cuy
                try:
                    with open("tmp/pid_new1.txt", "r") as f:
                        pid_new1 = f.read()
                except:
                    message_text = "请先点击项目，再点击国家"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                with open("tmp/country.txt", "r") as f:
                    cuy_new = f.read()
                endpoint_phone_new = endpoint_phone.replace("cuy=" + cuy, "cuy=" + cuy_new).replace("pid=" + pid, "pid=" + pid_new1)
                response = requests.get(endpoint_phone_new)
                phone_info = response.json()
                phone_status_code = (phone_info['code'])
                if phone_status_code == 200:
                    phone_number = "{}".format(phone_info['data'])
                    message_text = "`{}`".format(phone_info['data'])
                    bot.send_message(chat_id=chat_id, text=message_text, parse_mode=telegram.ParseMode.MARKDOWN)
                    if not os.path.exists("tmp"):
                        os.mkdir("tmp")
                    with open("tmp/phone_number.txt", "w") as f:
                        f.write(str(phone_number))
                    with open("tmp/pid_code.txt", "w") as f:
                        f.write(str(pid_new1))
                    logging.info("User %s (id=%d, %s) got a phone mumber %s with option %s at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, phone_number, liulian_functions, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    break
                elif phone_status_code == 406:
                    try:
                        os.remove('tmp/pid_code.txt')
                    except:
                        pass
                    os.remove('tmp/pid_new1.txt')
                    os.remove('tmp/pid_new2.txt')
                    message_text = "24小时内获得的新数量已达到最大数量"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                elif phone_status_code == 403:
                    try:
                        os.remove('tmp/pid_code.txt')
                    except:
                        pass
                    os.remove('tmp/pid_new1.txt')
                    os.remove('tmp/pid_new2.txt')
                    message_text = "积分不足"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                else:
                    print(f"第{count}次搜寻号码中... ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    count += 1
                time.sleep(0.1)
                try:
                    with open("tmp/pid_new2.txt", "r") as f:
                        pid_new2 = f.read()
                except:
                    message_text = "请先点击项目，再点击国家"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                endpoint_phone_new = endpoint_phone.replace("cuy=" + cuy, "cuy=" + cuy_new).replace("pid=" + pid, "pid=" + pid_new2)
                response = requests.get(endpoint_phone_new)
                phone_info = response.json()
                phone_status_code = (phone_info['code'])
                if phone_status_code == 200:
                    phone_number = "{}".format(phone_info['data'])
                    message_text = "`{}`".format(phone_info['data'])
                    bot.send_message(chat_id=chat_id, text=message_text, parse_mode=telegram.ParseMode.MARKDOWN)
                    if not os.path.exists("tmp"):
                        os.mkdir("tmp")
                    with open("tmp/phone_number.txt", "w") as f:
                        f.write(str(phone_number))
                    with open("tmp/pid_code.txt", "w") as f:
                        f.write(str(pid_new2))
                    logging.info("User %s (id=%d, %s) got a phone mumber %s with option %s at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, phone_number, liulian_functions, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    break
                elif phone_status_code == 406:
                    try:
                        os.remove('tmp/pid_code.txt')
                    except:
                        pass
                    os.remove('tmp/pid_new1.txt')
                    os.remove('tmp/pid_new2.txt')
                    message_text = "24小时内获得的新数量已达到最大数量。"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                elif phone_status_code == 403:
                    try:
                        os.remove('tmp/pid_code.txt')
                    except:
                        pass
                    os.remove('tmp/pid_new1.txt')
                    os.remove('tmp/pid_new2.txt')
                    message_text = "积分不足"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                else:
                    print(f"第{count}次搜寻号码中... ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    count += 1
                time.sleep(0.1)

        t = threading.Thread(target=get_number_thread)
        t.start()
    else:
        message_text = "请先开启系统"
        bot.send_message(chat_id=chat_id, text=message_text)

def googlevoice(update, context):
    query = update.callback_query
    bot = context.bot
    chat_id = update.callback_query.message.chat_id
    logging.info("User %s (id=%d, %s) selected the GV option at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if sys_status:
        message_text = "GV 获取号码中..."
        bot.send_message(chat_id=chat_id, text=message_text)
        try:
            with open("tmp/phone_number.txt", "r") as f:
                pn_code = f.read()
            try:
                with open("tmp/pid_code.txt", "r") as f:
                    pid_code = f.read()
                    endpoint_release_new = endpoint_release.replace("pid=" + pid, "pid=" + pid_code).replace("pn=" + pn, "pn=" + pn_code)
                    response = requests.get(endpoint_release_new)
                    release_info = response.json()
                    release_status_code = (release_info['code'])
                    if release_status_code == 200:
                        logging.info("User %s (id=%d, %s) released phone number %s at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, pn_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        os.remove('tmp/phone_number.txt')
                    else:
                        logging.info("User %s (id=%d, %s) failed to release phone number %s at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, pn_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            except:
                pass
        except:
            pass

        def gv_thread():
            global sys_status
            count = 1
            while sys_status:
                global pid
                global cuy
                cuy_new = "us"
                pid_new1 = "0299"
                endpoint_phone_new = endpoint_phone.replace("cuy=" + cuy, "cuy=" + cuy_new).replace("pid=" + pid, "pid=" + pid_new1)
                response = requests.get(endpoint_phone_new)
                phone_info = response.json()
                phone_status_code = (phone_info['code'])
                if phone_status_code == 200:
                    phone_number = "{}".format(phone_info['data'])
                    message_text = "`{}`".format(phone_info['data'])
                    bot.send_message(chat_id=chat_id, text=message_text, parse_mode=telegram.ParseMode.MARKDOWN)
                    if not os.path.exists("tmp"):
                        os.mkdir("tmp")
                    with open("tmp/phone_number.txt", "w") as f:
                        f.write(str(phone_number))
                    with open("tmp/pid_code.txt", "w") as f:
                        f.write(str(pid_new1))
                    logging.info("User %s (id=%d, %s) got a phone mumber %s with option Google Voice at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, phone_number, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    break
                elif phone_status_code == 406:
                    message_text = "24小时内获得的新数量已达到最大数量"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                elif phone_status_code == 403:
                    message_text = "积分不足"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                else:
                    print(f"第{count}次搜寻号码中... ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    count += 1
                time.sleep(0.1)
                pid_new2 = "0556"
                endpoint_phone_new = endpoint_phone.replace("cuy=" + cuy, "cuy=" + cuy_new).replace("pid=" + pid, "pid=" + pid_new2)
                response = requests.get(endpoint_phone_new)
                phone_info = response.json()
                phone_status_code = (phone_info['code'])
                if phone_status_code == 200:
                    phone_number = "{}".format(phone_info['data'])
                    message_text = "`{}`".format(phone_info['data'])
                    bot.send_message(chat_id=chat_id, text=message_text, parse_mode=telegram.ParseMode.MARKDOWN)
                    if not os.path.exists("tmp"):
                        os.mkdir("tmp")
                    with open("tmp/phone_number.txt", "w") as f:
                        f.write(str(phone_number))
                    with open("tmp/pid_code.txt", "w") as f:
                        f.write(str(pid_new2))
                    logging.info("User %s (id=%d, %s) got a phone mumber %s with option Google Voice at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, phone_number, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    break
                elif phone_status_code == 406:
                    message_text = "24小时内获得的新数量已达到最大数量。"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                elif phone_status_code == 403:
                    message_text = "积分不足"
                    bot.send_message(chat_id=chat_id, text=message_text)
                    break
                else:
                    print(f"第{count}次搜寻号码中... ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    count += 1
                time.sleep(0.1)

        t = threading.Thread(target=gv_thread)
        t.start()
    else:
        message_text = "请先开启系统"
        bot.send_message(chat_id=chat_id, text=message_text)

def button(update, context):
    global sys_status
    query = update.callback_query
    txt = "开启系统后再点击选项"
    bot = context.bot
    chat_id = update.callback_query.message.chat_id
    if query.data == 'account':
        account(update, context)
        logging.info("账户 button clicked by %s (id=%d, %s) at %s", query.from_user.username, query.from_user.id, query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return
    elif query.data == 'googlevoice':
        if sys_status:
            liulian_functions = "Google Voice"
            cuy_new = "us"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            googlevoice(update, context)
            return
        else:
            query.answer(txt)
            #message_text = "请先开启系统"
            #bot.send_message(chat_id=chat_id, text=message_text)
    elif query.data == 'gmail':
        if sys_status:
            pid_new1 = "0097"
            pid_new2 = "0098"
            liulian_functions = "GMmail"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'azure':
        if sys_status:
            pid_new1 = "0241"
            pid_new2 = "0049"
            liulian_functions = "Azure"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'aws':
        if sys_status:
            pid_new1 = "0209"
            pid_new2 = "0209"
            liulian_functions = "Aws"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'linode':
        if sys_status:
            pid_new1 = "2257"
            pid_new2 = "2257"
            liulian_functions = "Linode"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'paypal':
        if sys_status:
            pid_new1 = "0271"
            pid_new2 = "0271"
            liulian_functions = "Paypal"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'telegram':
        if sys_status:
            pid_new1 = "0257"
            pid_new2 = "0257"
            liulian_functions = "Telegram"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'netfilx':
        if sys_status:
            pid_new1 = "0208"
            pid_new2 = "0208"
            liulian_functions = "Netfilx"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'dynadot':
        if sys_status:
            pid_new1 = "3026"
            pid_new2 = "3026"
            liulian_functions = "Dynadot"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'Windows 365':
        if sys_status:
            pid_new1 = "3958"
            pid_new2 = "3958"
            liulian_functions = "Windows 365"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/pid_new1.txt", "w") as f:
                f.write(str(pid_new1))
            with open("tmp/pid_new2.txt", "w") as f:
                f.write(str(pid_new2))
            with open("tmp/liulian_functions.txt", "w") as f:
                f.write(str(liulian_functions))
            query.answer("正在处理请求，请稍候...")
            country_menu(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'sys_on':
        sys_status = True
        system_on_message = "系统已开启，可以点击选项了"
        query.answer(system_on_message)
        logging.info("System has been turned on by %s (id=%d, %s) at %s", query.from_user.username, query.from_user.id, query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    elif query.data == 'sys_off':
        sys_off(update, context)
        logging.info("System has been turned off by %s (id=%d, %s) at %s", query.from_user.username, query.from_user.id, query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return
    elif query.data == 'reboot':
        reboot_message = "BOT 重启中......"
        query.answer(reboot_message)
        logging.info("Telegram Bot has been reboot by %s (id=%d, %s) at %s", query.from_user.username, query.from_user.id, query.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        reboot(update, context)
        return
    elif query.data == 'verification_code':
        verification_code(update, context)
        return
    elif query.data == 'us':
        if sys_status:
            cuy_new = "us"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'ca':
        if sys_status:
            cuy_new = "ca"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'mx':
        if sys_status:
            cuy_new = "mx"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'au':
        if sys_status:
            cuy_new = "au"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'hk':
        if sys_status:
            cuy_new = "hk"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'tw':
        if sys_status:
            cuy_new = "tw"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'jp':
        if sys_status:
            cuy_new = "jp"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'sg':
        if sys_status:
            cuy_new = "sg"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'my':
        if sys_status:
            cuy_new = "my"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'th':
        if sys_status:
            cuy_new = "th"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)        
    elif query.data == 'id':
        if sys_status:
            cuy_new = "id"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'ph':
        if sys_status:
            cuy_new = "ph"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'gb':
        if sys_status:
            cuy_new = "gb"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'fr':
        if sys_status:
            cuy_new = "fr"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'it':
        if sys_status:
            cuy_new = "it"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'de':
        if sys_status:
            cuy_new = "de"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'nl':
        if sys_status:
            cuy_new = "nl"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'ng':
        if sys_status:
            cuy_new = "ng"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'es':
        if sys_status:
            cuy_new = "es"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'za':
        if sys_status:
            cuy_new = "za"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'tr':
        if sys_status:
            cuy_new = "tr"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'no':
        if sys_status:
            cuy_new = "no"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'ie':
        if sys_status:
            cuy_new = "ie"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    elif query.data == 'eg':
        if sys_status:
            cuy_new = "eg"
            if not os.path.exists("tmp"):
                os.mkdir("tmp")
            with open("tmp/country.txt", "w") as f:
                f.write(str(cuy_new))
            query.answer("正在处理请求，请稍候...")
            get_number(update, context)
            return
        else:
            query.answer(txt)
    else:
        query.edit_message_text(text="{}功能还在开发中...".format(query.data))

    logging.info("User %s (id=%d, %s) selected option %s before turn the system on at %s", update.callback_query.from_user.username, update.callback_query.from_user.id, update.callback_query.from_user.first_name, query.data, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def help(update, context):
    if not authorized_check(update):
        return

    help_message = """
    欢迎使用榴莲BOT！\n输入 /start 召唤菜单。\n菜单功能介绍如果下：\n开启：开启接码模式\n关闭：关闭接码模式\n账户：查询账号当前剩余积分等信息\n重启：重启BOT\nGV：Google Voice 接码\n验证码：获取以获取到的手机号的验证码\n点击GMAIL、AZURE、OPENAI等其他按钮后会弹出国家按钮，选择国家后开始获取手机号
    """
    update.message.reply_text(help_message)
    logging.info("User %s (id=%d, %s) requested help at %s", update.message.from_user.username, update.message.from_user.id, update.message.from_user.first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def error(update, context):
    if update is None or update.message is None:
        return
    logger.warning('Update "%s" caused error "%s" at "%s"', update, context.error, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def main():
    global bot
    updater = Updater(bot_token, use_context=True)
    bot = updater.bot
    dp = updater.dispatcher

    commands = [BotCommand("start", "开启菜单"), BotCommand("help", "获取帮助信息")]
    updater.bot.set_my_commands(commands)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler("help", help))
    dp.add_error_handler(error)

    #updater.dispatcher.add_handler(CommandHandler('start', start))
    #updater.dispatcher.add_handler(CommandHandler('help', help))

    logging.info("Bot started at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        updater.start_polling()
        updater.idle()
    except KeyboardInterrupt:
        pass
    finally:
        sys_status = False
        updater.stop()

if __name__ == '__main__':
    main()
