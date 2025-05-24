"""
Calculate trelliTime
"""
import os
import json
import sqlite3
import requests
import logging
from os.path import isfile, join
from datetime import timedelta
if os.name == "posix":
    import shlex


def format_timedelta(td):
    """Format timedelta values to not have days, only hours, minutes and seconds"""
    #logging.info("format_timedelta function td: %s", td)
    minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
    hours, minutes = divmod(minutes, 60)
    return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)

def substring_after(sentence, delim):
    """Get words after delimiter if exists"""
    return sentence.partition(delim)[2]


def calc_percentage_diff(trell_time, hltb_time):
    """Returns percent difference between trelliTime and HLTB avg time"""
    return ((trell_time / hltb_time) * 100) - 100

def get_hltb_averagetime(name):
    """Gets average main story beat time for the specified game from howlongtobeat api"""
    url = "https://howlongtobeat.com/api/seek/d4b2e330db04dbf3"
    headers = {
        "Referer": "https://howlongtobeat.com/?q=",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
    }
    body1 = '{"searchType":"games","searchTerms":"","searchPage":1,"size":20,"searchOptions":{"games":{"userId":0,"platform":"","sortCategory":"popular","rangeCategory":"main","rangeTime":{"min":null,"max":null},"gameplay":{"perspective":"","flow":"","genre":"","difficulty":""},"rangeYear":{"min":"","max":""},"modifier":""},"users":{"sortCategory":"postcount"},"lists":{"sortCategory":"follows"},"filter":"","sort":0,"randomizer":0},"useCache":true}'
    game_data = name.lower().split(" ")
    bod = json.loads(body1)
    bod["searchTerms"] = game_data
    body = json.dumps(bod)
    try:
        search = session.post(url, headers=headers, data=body)
        search.raise_for_status()
        contents = search.json()
    except requests.exceptions.HTTPError as err:
        logging.error("get_hltb_averagetime request httoerror: %s", err)
    try:
        finish_time = contents["data"][0]["comp_main"]
        logging.info("HLTB got finish time: %s", finish_time)
        return finish_time
    except IndexError:
        logging.error("get_hltb_averagetime indexError")
        return None


def create_conn(db_file):
    """create a database connection to the SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as err:
        logging.error("create_conn sqlite3 connect error: %s", err)
    return conn


THREAD_POOL = 10
session = requests.Session()
session.mount(
    "https://",
    requests.adapters.HTTPAdapter(
        pool_maxsize=THREAD_POOL, max_retries=3, pool_block=True
    ),
)
logging.basicConfig(
    filename="trelli_time.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d/%m/%Y, %H:%M:%S",
)
db_file = "./game_ids.db"
conn = create_conn(db_file)
cur = conn.cursor()
# directory that holds all times specified in minutes
# See: finished/example
os.chdir("finished")
# Gather all files in the directory
file_ls = [f for f in os.listdir(".") if isfile(join(".", f))]
total_games = 0
total_percentage_diff = 0
total_trelli_time = 0
for file1 in file_ls:
    total_time = 0
    cur.execute("SELECT name FROM game_ids WHERE id like ? ", [file1])
    game_name1 = cur.fetchall()
    game_name = game_name1[0][0]
    # Get average game clear time from HLTB
    hltb_time1 = get_hltb_averagetime(game_name)
    # If not found default to 0 seconds
    if hltb_time1 is None:
        hltb_time = 0
    else:
        hltb_time = int(hltb_time1)
    with open(f"{file1}", "r", encoding="utf-8") as game_time_data_file:
        for time_value in game_time_data_file:
            if os.name == "posix":
                # Only works in unix systems
                lex = shlex.shlex(time_value)
                lex.whitespace = ""  # if you want to strip newlines, use '\n'
                time_value = "".join(list(lex))
            else:
                time_value = time_value.split('#',1)[0].strip()
            if not time_value:
                continue
            try:
                # Handle time that is in hour:minute:second format
                hour1, minut1, sec1 = time_value.split(":")
                if sec1[:1] == "0":
                    sec1 = sec1[1:]
                sec1 = int(sec1)
                minut1 = int(minut1) * 60
                hour1 = int(hour1) * 3600
                total_time += (hour1 + minut1 + sec1)
                # print(total_time)
            except Exception:
                # Otherwise handle it in minutes
                time_value1 = int(time_value) * 60
                total_time += time_value1

    trelli_time = total_time - hltb_time
    if hltb_time < 1:
        formated_total_time = format_timedelta(timedelta(seconds=total_time))
        print(
            f"Game: {game_name} | Finish time: {formated_total_time}\nHow Long To Beat average main story time: no data\ntrelliTime: -\n--------------------------------------------------"
        )
    else:
        # Calculate percentage compared to HLTB time
        temp_time = (total_time / hltb_time) * 100
        trelli_time_percents = round(temp_time)
        percentage_diff = calc_percentage_diff(
            total_time, hltb_time)
        formated_total_time = format_timedelta(timedelta(seconds=total_time))
        formated_trelli_time = format_timedelta(timedelta(seconds=trelli_time))
        formated_hltb_time = format_timedelta(timedelta(seconds=hltb_time))
        print(
            f"Game: {game_name} | Finish time: {formated_total_time}\nHow Long To Beat average main story time: {formated_hltb_time}\ntrelliTime: {formated_trelli_time} | {trelli_time_percents}% compared to HLTB's time\n--------------------------------------------------"
        )
        total_trelli_time += trelli_time
        total_games += 1
        total_percentage_diff += percentage_diff

percentage_est = round(total_percentage_diff / total_games)
print(
    f"--------------------------------------------------\ntrelliTime percentage estimate: {percentage_est}%"
)
