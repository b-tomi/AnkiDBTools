import config
import sqlite3
from time import time
import codecs


def get_nid_dict():
    with sqlite3.connect(config.temp_db) as conn:
        select_command = "SELECT id, name FROM notetypes"
        cursor = conn.execute(select_command)
        return dict(cursor.fetchall())


def get_mid(name_in, dict_in):
    key_list = list(dict_in.keys())
    val_list = list(dict_in.values())
    return key_list[val_list.index(name_in)]


def fix_sql(line_in):
    # SQL needs '' to deal with '
    if line_in.find("'") > -1:
        line_in = line_in.replace("'", "''")
    return line_in


def calculate_time(start_time_in):
    current_time = time()
    time_seconds = current_time - start_time_in
    time_out = ""
    minutes_out, seconds_out = divmod(time_seconds, 60)
    hours_out, minutes_out = divmod(minutes_out, 60)
    if hours_out == 1:
        time_out += str(round(hours_out)) + " hour, "
    elif hours_out > 1:
        time_out += str(round(hours_out)) + " hours, "
    if minutes_out == 1:
        time_out += str(round(minutes_out)) + " minute and "
    elif minutes_out > 1:
        time_out += str(round(minutes_out)) + " minutes and "
    if seconds_out == 1:
        time_out += str(round(seconds_out)) + " second"
    else:
        time_out += str(round(seconds_out, 2)) + " seconds"
    return time_out


def mk_bold(line_in, vocab_in):
    line_out = line_in.replace(str(vocab_in), f"<b>{str(vocab_in)}</b>")
    return line_out


def remove_html_tags(line_in, add_bullets=False):
    # no idea what this char is, but it showed up in some notes, probably some copy/paste remnant
    line_out = str(line_in).replace("​", "")
    line_out = line_out.replace("<div>", "")
    line_out = line_out.replace("</div>", "")
    line_out = line_out.replace("<br>", "")
    # to re-add the tags to definitions with bullet points
    if add_bullets:
        # just replace all, then fix the first and last
        line_out = line_out.replace("‣ ", "</div><div>‣ ")
        line_out = line_out[6:] + "</div>"
    return line_out


def strip_list(list_in, index=0):
    # strips list of tuples, etc. to a single entry (the first, or whatever provided index)
    list_out = []
    for line in list_in:
        list_out.append(line[index])
    return list_out


def cards_seen(note_id):
    with sqlite3.connect(config.temp_db) as conn:
        sql_command = f"SELECT id, queue, reps FROM cards WHERE nid = {note_id}"
        cursor = conn.execute(sql_command)
        cards_list = list(cursor.fetchall())
        for card in cards_list:
            # return True if any of the cards has any reps
            if card[2] > 0:
                return True
        return False


def cards_toggle_suspend(note_id, suspend=False):
    with sqlite3.connect(config.temp_db) as conn:
        sql_command = f"SELECT id, queue, reps FROM cards WHERE nid = {note_id}"
        cursor = conn.execute(sql_command)
        cards_list = list(cursor.fetchall())
        for card in cards_list:
            if suspend:
                command = f"UPDATE cards SET queue = -1 WHERE id = {card[0]}"
            else:
                # for seen cards
                if card[2] > 0:
                    command = f"UPDATE cards SET queue = 2 WHERE id = {card[0]}"
                # for unseen cards
                else:
                    command = f"UPDATE cards SET queue = 0 WHERE id = {card[0]}"
            conn.execute(command)
        conn.commit()


def get_kanji_list(txt_file_in):
    list_out = []
    with codecs.open(txt_file_in, encoding='utf-8') as file:
        for line in file:
            for char in line:
                if char != "\r" and char != "\n":
                    list_out.append(char)
    return list_out
