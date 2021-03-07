import shutil

import requests
from bs4 import BeautifulSoup

from shared import *


def compare_kanji(name_in, list_in):
    kanji_list = get_kanji_list(list_in)
    missing_list = kanji_list.copy()
    with sqlite3.connect(config.temp_db) as conn:
        matches = 0
        matches_list = []
        kanji_command = f"SELECT flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for note_line in note_list:
            split_note_line = note_line[0].split("\x1f")
            for char in kanji_list:
                if split_note_line[0] == char:
                    matches += 1
                    matches_list.append(char)
                    missing_list.remove(char)

        print(f"{matches}/{len(kanji_list)} matches found.")
        # print(f"Matching characters: {matches_list}")
        if len(missing_list) > 0:
            print(f"Missing characters: {missing_list}")


def get_kanji_list(txt_file_in):
    kanji_list = []
    with codecs.open(txt_file_in, encoding='utf-8') as file:
        for line in file:
            for char in line:
                if char != "\r" and char != "\n":
                    kanji_list.append(char)
    return kanji_list


def find_kana(name_in):
    with sqlite3.connect(config.temp_db) as conn:
        kanji_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for note_line in note_list:
            split_note_line = note_line[1].split("\x1f")
            if split_note_line[6] == "" and split_note_line[7] != "":
                print(split_note_line[0])


def load_frequency_dict(txt_file_in):
    frequency_list = []
    rank = 0
    with codecs.open(txt_file_in, encoding='utf-8') as file:
        for line in file:
            rank += 1
            # remove initial spaces
            line = line.strip()
            split_line = line.split("  ")
            frequency_list.append((split_line[1], rank))
    # turn into a dictionary for easier manipulation
    frequency_dict = dict(frequency_list)
    # print(frequency_dict.get("讓"))
    return frequency_dict


def update_frequency(name_in, dict_in):
    # field 11
    with sqlite3.connect(config.temp_db) as conn:
        updated_count = 0
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(sql_command)
        kanji_list = list(cursor.fetchall())
        for line in kanji_list:
            split_line = line[1].split("\x1f")
            new_rank = str(dict_in.get(split_line[0]))
            # clear any leftover entries in the field
            split_line[11] = ""
            if new_rank != "None":
                split_line[11] = new_rank
            new_line = "\x1f".join(split_line)
            print(f"{split_line[0]} => {split_line[11]}")
            command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {line[0]}"
            conn.execute(command)
            updated_count += 1
    if updated_count > 0:
        conn.commit()
        print(f"Updated {updated_count} cards.")


def compare_frequency(name_in, dict_in):
    with sqlite3.connect(config.temp_db) as conn:
        total = len(dict_in)
        matches = 0
        matches_list = []
        kanji_command = f"SELECT flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for note_line in note_list:
            split_note_line = note_line[0].split("\x1f")
            if str(dict_in.get(split_note_line[0])) != "None":
                matches += 1
                matches_list.append(split_note_line[0])
                dict_in.pop(split_note_line[0])
        print(f"{matches}/{total} matches found.")
        if len(dict_in) > 0:
            line_out = ""
            for kanji in list(dict_in):
                line_out += kanji
            print(f"Not found: {line_out}")


def count_notes(name_in, tag=""):
    with sqlite3.connect(config.temp_db) as conn:
        notes_count = 0
        kanji_command = f"SELECT id, tags FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for note_line in note_list:
            if note_line[1].find(tag) > -1:
                notes_count += 1
        if notes_count > 1:
            print(f"Found {notes_count} with {tag} tag.")
        else:
            print(f"No notes found with {tag} tag.")


def compare_notes_tags(name_in, list_in, tag=""):
    with sqlite3.connect(config.temp_db) as conn:
        kanji_list = get_kanji_list(list_in)
        kanji_count = len(kanji_list)
        missing_list = []
        match_count = 0
        kanji_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for note_line in note_list:
            split_note_line = note_line[2].split("\x1f")
            if note_line[1].find(tag) > -1 and split_note_line[0] in kanji_list:
                match_count += 1
                kanji_list.remove(split_note_line[0])
            elif note_line[1].find(tag) > -1 and split_note_line[0] not in kanji_list:
                missing_list.append(split_note_line[0])
        if match_count > 1:
            print(f"Found {match_count}/{kanji_count} matches with {tag} tag.")
        else:
            print(f"No matches found with {tag} tag.")
        if len(missing_list) > 0:
            print(f"Not in the list: {missing_list}")
            print(f"Missing in deck: {kanji_list}")


def load_word_list(txt_file_in, txt_file_in2):
    word_list = []
    with codecs.open(txt_file_in, encoding='utf-8') as file:
        for line in file:
            clean_line = line.strip("\n")
            clean_line = clean_line.strip("\r")
            word_list.append(clean_line)
    if txt_file_in2 != "":
        with codecs.open(txt_file_in2, encoding='utf-8') as file:
            for line in file:
                clean_line = line.strip("\n")
                clean_line = clean_line.strip("\r")
                word_list.append(clean_line)
    return word_list


def load_word_list_from_db(table_in):
    with sqlite3.connect("_common_vocab.db") as conn:
        sql_command = f"SELECT vocab FROM '{table_in}'"
        cursor = conn.execute(sql_command)
        current_list = list(cursor.fetchall())
        list_out = strip_list(current_list)
        return list_out


def count_frequency(list_in):
    kanji_dict = {}
    for line in list_in:
        for char in line:
            if char not in kanji_dict:
                kanji_dict[char] = 1
            else:
                kanji_dict[char] += 1
    return kanji_dict


def generate_frequency_dict(dict_in):
    kana_list = get_kanji_list(config.kana)
    # add these chars so they don't get counted
    exclude_list = ["☆", "ゞ"]
    for char in exclude_list:
        kana_list.append(char)
    ranked_list = []
    rank = 0
    for kanji, times in sorted(dict_in.items(), key=lambda item: item[1], reverse=True):
        if kanji not in kana_list:
            rank += 1
            ranked_list.append((kanji, rank))
    dict_out = dict(ranked_list)
    return dict_out


def get_linguee_list(extra_pages=0):
    pages_list = ["https://www.linguee.com/japanese-english/topjapanese/1-200.html",
                  "https://www.linguee.com/japanese-english/topjapanese/201-1000.html",
                  "https://www.linguee.com/japanese-english/topjapanese/1001-2000.html",
                  "https://www.linguee.com/japanese-english/topjapanese/2001-3000.html",
                  "https://www.linguee.com/japanese-english/topjapanese/3001-4000.html",
                  "https://www.linguee.com/japanese-english/topjapanese/4001-5000.html"]

    # need to extract the subpages from these
    pages_list_extra = ["https://www.linguee.com/japanese-english/topjapanese/5001-7000.html",
                        "https://www.linguee.com/japanese-english/topjapanese/7001-10000.html",
                        "https://www.linguee.com/japanese-english/topjapanese/10001-20000.html",
                        "https://www.linguee.com/japanese-english/topjapanese/20001-40000.html",
                        "https://www.linguee.com/japanese-english/topjapanese/40001-100000.html",
                        "https://www.linguee.com/japanese-english/topjapanese/100001-200000.html",
                        "https://www.linguee.com/japanese-english/topjapanese/200001-500000.html"]
    word_list = []
    for page in pages_list:
        word_list += process_linguee_page(page)
    if extra_pages > 0:
        for i in range(0, extra_pages):
            extracted_pages_list = extract_linguee_pages(pages_list_extra[i])
            for extracted_page in extracted_pages_list:
                word_list += process_linguee_page(extracted_page)
    print(f"Loaded {len(word_list)} vocab entries.")
    # print some word from the end
    # print(word_list[len(word_list)-3])
    return word_list


def extract_linguee_pages(page_in):
    base_link = "https://www.linguee.com"
    page_list_out = []
    response = requests.get(page_in)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.select_one("table", {"class": "lineItemsTable"})
    entries = table.findAll('a')
    for entry in entries:
        full_link = base_link + entry.get('href')
        page_list_out.append(full_link)
    return page_list_out


def process_linguee_page(page_in):
    list_out = []
    response = requests.get(page_in)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.select_one("table", {"class": "lineItemsTable"})
    entries = table.select("td")
    for entry in entries:
        # split to two parts
        # rank = int(entry.text.split(".: ")[0])
        vocab = entry.text.split(".: ")[1]
        # create a tuple that also includes the rank
        # list_out.append([rank, vocab])
        # or just use the index (+1) as a rank
        list_out.append(vocab)
    return list_out


def write_linguee_list(list_in, table_in):
    with sqlite3.connect("_common_vocab.db") as conn:
        vocab_count = 0
        start_time = time()
        for line in list_in:
            sql_command = f"INSERT INTO {table_in} (vocab) VALUES ('{fix_sql(line)}')"
            conn.execute(sql_command)
            vocab_count += 1
        if vocab_count > 1:
            conn.commit()
            print(f"Wrote {vocab_count} new entries in {calculate_time(start_time)}.")


def add_common_tag(name_in, dict_in):
    # kanji_list = []
    # for key in dict_in:
    #     dict_in.get()
    with sqlite3.connect(config.temp_db) as conn:
        matches = 0
        kanji_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for line in note_list:
            split_line = line[2].split("\x1f")
            # this should be a "truthy" value, unless no such key found
            if dict_in.get(split_line[0]):
                new_tag = line[1] + "KD_COMMON "
                command = f"UPDATE notes SET tags = '{fix_sql(new_tag)}' WHERE id = {line[0]}"
                conn.execute(command)
                matches += 1
        conn.commit()
        print(f"{matches}/{len(note_list)} Updated.")


shutil.copy(config.live_db, config.temp_db)
note_types_dict = get_nid_dict()

# second argument options: config.joyo, config.jin1, config.jin2
compare_kanji("KanjiDamage+", config.joyo)
compare_kanji("KanjiDamage+", config.jin1)
compare_kanji("KanjiDamage+", config.jin2)
print()
compare_kanji("KanjiDamage+", config.jlpt_n5)
compare_kanji("KanjiDamage+", config.jlpt_n4)
compare_kanji("KanjiDamage+", config.jlpt_n3)
compare_kanji("KanjiDamage+", config.jlpt_n2)
compare_kanji("KanjiDamage+", config.jlpt_n1)
print()

# load the word list, 10k, 20k
# unsorted_dict = count_frequency(load_word_list(config.words10k, config.words20k))
# update the live DB
# update_frequency("KanjiDamage+", generate_frequency_dict(unsorted_dict))
# compare with the generated frequency list
# compare_frequency("KanjiDamage+", generate_frequency_dict(unsorted_dict))

# load the words list from the imported jisho DB and compare with live DB
# unsorted_dict_from_db = count_frequency(load_word_list_from_db("common"))
# compare_frequency("KanjiDamage+", generate_frequency_dict(unsorted_dict_from_db))

# same as above, but for the JLPT N2 and N1 tables
# to see if there are any kanji still missing from the deck
unsorted_dict_from_db = count_frequency(load_word_list_from_db("jlpt-n2"))
compare_frequency("KanjiDamage+", generate_frequency_dict(unsorted_dict_from_db))
unsorted_dict_from_db = count_frequency(load_word_list_from_db("jlpt-n1"))
compare_frequency("KanjiDamage+", generate_frequency_dict(unsorted_dict_from_db))

# one-time stuff to add KD_COMMON tag to KD+ deck, using the imported jisho DB
# unsorted_dict_from_db = count_frequency(load_word_list_from_db("common"))
# add_common_tag("KanjiDamage+", unsorted_dict_from_db)

# # compare with the old frequency list
# compare_frequency("KanjiDamage+", get_frequency_dict(config.freq))

# count the number of notes with a certain tag
# count_notes("KanjiDamage+", tag="KD_FromWK")
# count_notes("KanjiDamage+", tag="Kanji_Joyo")
# count_notes("KanjiDamage+", tag="Kanji_Jinmeiyo")
# count_notes("KanjiDamage+", tag="Kanji_Jinmei_Traditional")
# count_notes("KanjiDamage+", tag="Kanji_Hyogai")

# compare notes with a certain tag with a certain list
# compare_notes_tags("KanjiDamage+", config.joyo, tag="Kanji_Joyo")
# compare_notes_tags("KanjiDamage+", config.jin1, tag="Kanji_Jinmeiyo")
# compare_notes_tags("KanjiDamage+", config.jin2, tag="Kanji_Jinmei_Traditional")

# Linguee stuff
# extra_pages=0 will only do the first 5k entries
# possible options: 1=7k, 2=10k, 3=20k, 4=40k, 5=100k, 6=200k, 7=500k
# get_linguee_list(extra_pages=2)
# get and write to the DB
# write_linguee_list(get_linguee_list(extra_pages=7), "linguee1") z 2020.10.15
# write_linguee_list(get_linguee_list(extra_pages=7), "linguee2")

# read the linguee db and compare with live db
# unsorted_dict_from_db = count_frequency(load_word_list_from_db("linguee1"))
# compare_frequency("KanjiDamage+", generate_frequency_dict(unsorted_dict_from_db))


# OBSOLETE
# fix the frequency kanji list
# get_frequency_dict(config.freq)
# read in the frequency list and update the deck
# update_frequency("KanjiDamage+", get_frequency_dict(config.freq))

# just a quick comparison of kana & furigana lines
# find_kana("KanjiDamage+")
