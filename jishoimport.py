from shared import *
import shutil
import requests
from bs4 import BeautifulSoup


def get_categories(word_in):
    response = requests.get("https://jisho.org/word/" + word_in)
    soup = BeautifulSoup(response.text, "html.parser")
    cat_list = soup.select(".meaning-tags")
    return merge_cats(cat_list)


def merge_cats(list_in):
    if len(list_in) == 0:
        return ""
    elif len(list_in) == 1:
        return list_in[0].text
    else:
        list_out = []
        for line in list_in:
            split_cats = line.text.split(", ")
            for category in split_cats:
                # ignore certain entries
                if category not in list_out and category != "Other forms" and category != "Notes" \
                        and category != "Place" and category != "Wikipedia definition":
                    list_out.append(category)
        text_out = ", ".join(list_out)
        return text_out


def get_definition(character_in):
    response = requests.get("https://jisho.org/search/" + character_in + "%20%23kanji")
    soup = BeautifulSoup(response.text, "html.parser")
    definition_list = soup.select(".kanji-details__main-meanings")
    # return empty string if character was not found
    if len(definition_list) > 0:
        # clean up the returned string
        definition_out = definition_list[0].text.replace("\n", "")
        definition_out = definition_out.strip(" ")
        return definition_out
    else:
        return ""


def get_nanori(character_in):
    response = requests.get("https://jisho.org/search/" + character_in + "%20%23kanji")
    soup = BeautifulSoup(response.text, "html.parser")
    nanori_list = soup.select(".nanori")
    # return empty string if character was not found
    # print(nanori_list)
    if len(nanori_list) > 0:
        # clean up the returned string
        nanori_out = nanori_list[0].text.replace("Japanese names:", "")
        nanori_out = nanori_out.replace("\n", "")
        nanori_out = nanori_out.strip(" ")
        return nanori_out
    else:
        return ""


def get_common_vocab(start_page=1, end_page=1054):
    with sqlite3.connect("_common_vocab.db") as conn:
        start_time = time()
        # create the database at first run
        # sql_command = "CREATE TABLE common (vocab TEXT, definition TEXT, category TEXT, full TEXT)"
        # cursor = conn.execute(sql_command)
        # conn.commit()
        vocab_count = 0
        sql_command = "SELECT vocab FROM common"
        cursor = conn.execute(sql_command)
        # returns a tuple for some reason, with the second field empty?
        current_list = list(cursor.fetchall())
        fixed_list = strip_list(current_list)
        for page in range(start_page, end_page + 1):
            response = requests.get("https://jisho.org/search/%23word%20%23common?page=" + str(page))
            soup = BeautifulSoup(response.text, "html.parser")
            page_list = soup.select(".concept_light")
            for entry in page_list:
                soup2 = BeautifulSoup(str(entry), "html.parser")
                vocab_list = soup2.select(".text")
                meaning_list = soup2.select(".meaning-meaning")
                category_list = soup2.select(".meaning-tags")
                vocab = str(vocab_list[0].text.strip())
                if vocab not in fixed_list:
                    print(vocab)
                    definition = str(meaning_list[0].text.strip())
                    # in the rare case there isn't any category
                    if len(category_list) == 0:
                        category = "None"
                    else:
                        category = str(category_list[0].text.strip())
                    full = str(entry)
                    sql_command = f"INSERT INTO common VALUES ('{fix_sql(vocab)}', '{fix_sql(definition)}'," \
                                  f"'{fix_sql(category)}', '{fix_sql(full)}')"
                    conn.execute(sql_command)
                    # add to the list, so it doesn't get added to be DB again
                    fixed_list.append(vocab)
                    vocab_count += 1
            conn.commit()
            print(f"Page {page} | Total new entries {vocab_count}.")
        print(f"Found {vocab_count} new entries in {calculate_time(start_time)}.")


def create_db_for_tag(tag_in):
    with sqlite3.connect("_common_vocab.db") as conn:
        sql_command = f"CREATE TABLE \"{tag_in}\" (\"vocab\" TEXT NOT NULL UNIQUE, \"definition\" TEXT, " \
                      f"\"category\" TEXT, \"full\" TEXT, \"meanings\" TEXT, \"cats\" TEXT)"
        conn.execute(sql_command)
        conn.commit()


def get_vocab_with_tag(tag_in):
    with sqlite3.connect("_common_vocab.db") as conn:
        start_time = time()
        vocab_count = 0
        sql_command = f"SELECT vocab FROM '{tag_in}'"
        cursor = conn.execute(sql_command)
        # returns a tuple for some reason, with the second field empty?
        current_list = list(cursor.fetchall())
        fixed_list = strip_list(current_list)
        response = requests.get(f"https://jisho.org/search/%23word%20%23{tag_in}")
        soup = BeautifulSoup(response.text, "html.parser")
        total_words = soup.select_one(".result_count")
        total_words_text = total_words.text.strip(" — ")
        total_words_text = total_words_text.strip(" found")
        # floor division - throws away anything past the decimal point
        total_pages = int(total_words_text) // 20
        for page in range(1, total_pages + 1):
            response = requests.get(f"https://jisho.org/search/%23word%20%23{tag_in}?page= + {page}")
            soup = BeautifulSoup(response.text, "html.parser")
            page_list = soup.select(".concept_light")
            for entry in page_list:
                soup2 = BeautifulSoup(str(entry), "html.parser")
                vocab_list = soup2.select(".text")
                meaning_list = soup2.select(".meaning-meaning")
                category_list = soup2.select(".meaning-tags")
                vocab = str(vocab_list[0].text.strip())
                if vocab not in fixed_list:
                    print(vocab)
                    definition = str(meaning_list[0].text.strip())
                    # in the rare case there isn't any category
                    if len(category_list) == 0:
                        category = "None"
                    else:
                        category = str(category_list[0].text.strip())
                    full = str(entry)
                    sql_command = f"INSERT INTO '{tag_in}' VALUES ('{fix_sql(vocab)}', '{fix_sql(definition)}'," \
                                  f"'{fix_sql(category)}', '{fix_sql(full)}', '', '')"
                    conn.execute(sql_command)
                    # add to the list, so it doesn't get added to be DB again
                    fixed_list.append(vocab)
                    vocab_count += 1
            conn.commit()
            print(f"Tag {tag_in} | Page {page}/{total_pages} | Total new entries {vocab_count}.")
        print(f"Found {vocab_count} new entries in {calculate_time(start_time)} with tag {tag_in}.")
        return tag_in, vocab_count, total_words_text


def compare_common(note_type):
    start_time = time()
    vocab_count = 0
    with sqlite3.connect("_common_vocab.db") as conn:
        sql_command = "SELECT vocab, definition, category FROM common"
        cursor = conn.execute(sql_command)
        common_list = list(cursor.fetchall())
    with sqlite3.connect(config.temp_db) as conn:
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(note_type, note_types_dict)}"
        cursor = conn.execute(sql_command)
        notes_list = list(cursor.fetchall())
        for line in notes_list:
            split_line = line[2].split("\x1f")
            for common_line in common_list:
                if split_line[0] == common_line[0]:
                    common_list.remove(common_line)
                    vocab_count += 1
        print(f"Found {vocab_count} matches out of {len(common_list) + vocab_count} in {calculate_time(start_time)}.")
    return common_list


def copy_common_vocab(missing_list):
    with sqlite3.connect("_common_vocab.db") as conn:
        start_time = time()
        vocab_count = 0
        sql_command = "SELECT vocab, definition FROM common"
        cursor = conn.execute(sql_command)
        source_list = list(cursor.fetchall())
        sql_command = "SELECT vocab, definition FROM missing"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        target_list = strip_list(target_list)
        for missing_line in missing_list:
            match = False
            for source_line in source_list:
                if missing_line[0] == source_line[0] and missing_line[0] not in target_list:
                    match = True
                    break
            if match:
                sql_command = f"INSERT INTO missing VALUES ('{fix_sql(missing_line[0])}'," \
                              f"'{fix_sql(missing_line[1])}', '{fix_sql(missing_line[2])}', '')"
                conn.execute(sql_command)
                vocab_count += 1
        conn.commit()
        print(f"Copied {vocab_count} entries in {calculate_time(start_time)}.")


def compare_missing(note_type):
    start_time = time()
    vocab_count = 0
    with sqlite3.connect(config.temp_db) as conn:
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(note_type, note_types_dict)}"
        cursor = conn.execute(sql_command)
        notes_list = list(cursor.fetchall())
    with sqlite3.connect("_common_vocab.db") as conn:
        sql_command = "SELECT oid, vocab, definition, category, tags FROM missing"
        cursor = conn.execute(sql_command)
        missing_list = list(cursor.fetchall())
        for line in notes_list:
            split_line = line[1].split("\x1f")
            for missing_line in missing_list:
                if split_line[0] == missing_line[1]:
                    # delete ones that are not missing anymore
                    sql_command = f"DELETE FROM missing WHERE oid = {missing_line[0]}"
                    conn.execute(sql_command)
                    missing_list.remove(missing_line)
                    vocab_count += 1
        if vocab_count > 0:
            conn.commit()
            print(f"Found and deleted {vocab_count} matches out of {len(missing_list) + vocab_count} "
                  f"in {calculate_time(start_time)}.")
        else:
            print("No matches found.")
    return missing_list


def delete_duplicates(table_in):
    with sqlite3.connect("_common_vocab.db") as conn:
        start_time = time()
        unique_list = []
        duplicate_count = 0
        sql_command = f"SELECT oid, vocab FROM {table_in}"
        cursor = conn.execute(sql_command)
        current_list = list(cursor.fetchall())
        for current_line in current_list:
            # delete if already on the unique list
            if current_line[1] in unique_list:
                sql_command = f"DELETE FROM {table_in} WHERE oid = {current_line[0]}"
                conn.execute(sql_command)
                duplicate_count += 1
            else:
                unique_list.append(current_line[1])
        if duplicate_count > 0:
            conn.commit()
            print(f"Found and deleted {duplicate_count} duplicates out of {len(unique_list) + duplicate_count} "
                  f"in table {table_in} in {calculate_time(start_time)}.")
        else:
            print(f"No duplicates found in table {table_in}.")


def process_vocab(name_in):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        field_pos = category_position_dict.get(name_in) - 1
        vocab_count = 0
        processed_count = 0
        vocab_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(vocab_command)
        vocab_list = list(cursor.fetchall())
        for vocab_line in vocab_list:
            processed_count += 1
            split_vocab_line = vocab_line[2].split("\x1f")
            new_cat = get_categories(split_vocab_line[0])
            # position depending on the type of the note
            # don't replace any existing one with an empty string, and skip if the same
            if new_cat != "" and new_cat != split_vocab_line[field_pos]:
                print(f"{split_vocab_line[0]}: {split_vocab_line[field_pos]} => {new_cat} [#{processed_count}]")
                split_vocab_line[field_pos] = new_cat
                new_line = "\x1f".join(split_vocab_line)
                command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = '{str(vocab_line[0])}'"
                conn.execute(command)
                vocab_count += 1
        if vocab_count > 0:
            conn.commit()
        print(f"{vocab_count}/{len(vocab_list)} notes processed for {name_in} in {calculate_time(start_time)}.")


def process_kanji(name_in, update=False):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        field_pos = definition_position_dict.get(name_in) - 1
        kanji_count = 0
        processed_count = 0
        changes_list = []
        vocab_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(vocab_command)
        kanji_list = list(cursor.fetchall())
        for kanji_line in kanji_list:
            processed_count += 1
            split_kanji_line = kanji_line[2].split("\x1f")
            # only do ones where there's no full meaning set, or force update
            if split_kanji_line[field_pos] == "" or update:
                new_def = get_definition(split_kanji_line[0])
                # don't replace any existing one with an empty string
                if new_def == "":
                    pass
                    # print(f"{split_kanji_line[0]}: Kanji not found. [#{processed_count}]")
                # and skip if the same (deal with how Anki stores the & sign)
                elif new_def.replace("&", "&amp;") == split_kanji_line[field_pos]:
                    # pass
                    print(f"{split_kanji_line[0]}: No change. [#{processed_count}]")
                else:
                    print(f"{split_kanji_line[0]}: {split_kanji_line[field_pos]} => {new_def} [#{processed_count}]")
                    split_kanji_line[field_pos] = new_def
                    # if it's empty, also copy it to the keyword field
                    if split_kanji_line[2] == "":
                        split_kanji_line[2] = new_def
                    new_line = "\x1f".join(split_kanji_line)
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = '{str(kanji_line[0])}'"
                    conn.execute(command)
                    kanji_count += 1
                    changes_list.append(split_kanji_line[0])
        if kanji_count > 0:
            conn.commit()
        print(changes_list)
        print(f"{kanji_count}/{len(kanji_list)} notes processed for {name_in} in {calculate_time(start_time)}.")


def process_kanji_nanori(name_in, update=False):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        field_pos = nanori_position_dict.get(name_in) - 1
        kanji_count = 0
        processed_count = 0
        changes_list = []
        vocab_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(vocab_command)
        kanji_list = list(cursor.fetchall())
        for kanji_line in kanji_list:
            processed_count += 1
            # ignore images
            if kanji_line[1].find("<img") == -1:
                split_kanji_line = kanji_line[2].split("\x1f")
                # only do notes with a certain tag
                # if kanji_line[1].find("KD_Nanori") > -1:
                # skip existing ones, unless forcing a full update
                if split_kanji_line[field_pos] == "" or update:
                    new_nanori = get_nanori(split_kanji_line[0])
                    # add something if no nanori found, just so it gets skipped next time
                    if new_nanori == "":
                        print(f"{split_kanji_line[0]}: {split_kanji_line[field_pos]} => - [#{processed_count}]")
                        # this shouldn't break any formatting
                        split_kanji_line[field_pos] = "<span style=\"opacity:0\">-</span>"
                    else:
                        # print for reference
                        print(
                            f"{split_kanji_line[0]}: {split_kanji_line[field_pos]} "
                            f"=> {new_nanori} [#{processed_count}]")
                        split_kanji_line[field_pos] = new_nanori
                    new_line = "\x1f".join(split_kanji_line)
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = '{str(kanji_line[0])}'"
                    conn.execute(command)
                    kanji_count += 1
                    changes_list.append(split_kanji_line[0])
            # just to see if anything's happening
            if processed_count % 500 == 0:
                print(f"Processed {processed_count} kanji.")
        if kanji_count > 0:
            conn.commit()
        print(changes_list)
        print(f"{kanji_count}/{len(kanji_list)} notes processed for {name_in} in {calculate_time(start_time)}.")


def process_vocab_with_tag(tag_in, update=False):
    with sqlite3.connect("_common_vocab.db") as conn:
        start_time = time()
        vocab_count = 0
        sql_command = f"SELECT oid, vocab, full, meanings FROM '{tag_in}'"
        cursor = conn.execute(sql_command)
        vocab_list = list(cursor.fetchall())
        for line in vocab_list:
            # only do if no definitions, or force update
            if update or line[3] == "":
                soup = BeautifulSoup(line[2], "html.parser")
                # meanings = soup.select_one(".meanings-wrapper")
                meanings = format_meanings(soup.select(".meaning-meaning"))
                # print(meanings)
                cats = merge_cats(soup.select(".meaning-tags"))
                # print(cats)
                # cats = soup.select(".meaning-tags")
                # for c in cats:
                #     print(c.text)
                # for entry in page_list:
                #     soup2 = BeautifulSoup(str(entry), "html.parser")
                #     vocab_list = soup2.select(".text")
                #     meaning_list = soup2.select(".meaning-meaning")
                #     category_list = soup2.select(".meaning-tags")
                #     vocab = str(vocab_list[0].text.strip())
                command = f"UPDATE '{tag_in}' SET meanings = '{fix_sql(meanings)}', cats = '{fix_sql(cats)}' " \
                          f"WHERE oid = {line[0]}"
                conn.execute(command)
                vocab_count += 1
        if vocab_count > 0:
            conn.commit()
        print(f"Processed {vocab_count} entries in {calculate_time(start_time)} with tag {tag_in}.")
        return vocab_count


def format_meanings(list_in):
    if len(list_in) > 1:
        text_out = ""
        for line in list_in:
            text_out += f"<div>‣ {line.text}</div>"
        return text_out
    else:
        return list_in[0].text


def add_tags_from_db(note_type, tag_in):
    start_time = time()
    # list of tables for dict
    # "common", "comp", "col", "derog", "chn", "fam", "fem", "bus", "econ", "finc", "food", "ksb", "m-sl",
    # "joc", "male", "vulg", "net-sl", "wasei", "X", "yoji", "sens", "exp", "med"
    # the extra space after is needed for Anki
    # TODO: Add whatever else will be needed
    tags_dict = {"common": "Common ",
                 "comp": "IT ",
                 "col": "Colloquialism ",
                 "food": "Cuisine ",
                 "wasei": "Wasei ",
                 "exp": "Expression ",
                 "math": "Math ",
                 "jlpt-n2": "JLPT_N2 ",
                 "jlpt-n1": "JLPT_N1 "}
    processed_count = 0
    updated_count = 0
    with sqlite3.connect("_common_vocab.db") as conn:
        sql_command = f"SELECT vocab, definition, category FROM {tag_in}"
        cursor = conn.execute(sql_command)
        imported_list = list(cursor.fetchall())
    with sqlite3.connect(config.temp_db) as conn:
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(note_type, note_types_dict)}"
        cursor = conn.execute(sql_command)
        notes_list = list(cursor.fetchall())
        for line in notes_list:
            split_line = line[2].split("\x1f")
            for imported_line in imported_list:
                # either the vocab field matches, or the "Other forms" one, to include words written in kana
                # notes with multiple forms in the "Other forms" field will have to be checked manually
                if split_line[0] == imported_line[0] or split_line[3] == imported_line[0]:
                    # add the relevant tag to the notes, if missing
                    if line[1].find(tags_dict.get(tag_in)) == -1:
                        if line[1] == "":
                            # Anki expects a space in front, make sure it's there
                            new_tag = f" {tags_dict.get(tag_in)}"
                        else:
                            # existing entries should already have the extra space
                            new_tag = f"{line[1]} {tags_dict.get(tag_in)}"
                        command = f"UPDATE notes SET tags = '{fix_sql(new_tag)}' WHERE id = {line[0]}"
                        conn.execute(command)
                        # print for reference, the missing space before "tag" is intentional
                        # since the dictionary values already include a space
                        print(f"Added {tags_dict.get(tag_in)}tag to {split_line[0]}.")
                        updated_count += 1
                    # imported_list.remove(imported_line)
                    processed_count += 1
        if updated_count > 1:
            conn.commit()
        print(f"Updated {updated_count}/{processed_count} notes with {tags_dict.get(tag_in)}tag "
              f"in {calculate_time(start_time)}.")
    return imported_list


def main():
    # get nanori readings for kanji
    process_kanji_nanori("KanjiDamage+", update=False)
    # compare the common list with the ones in anki and add a tag to the notes
    add_tags_from_db("Advanced Japanese", "common")
    print()


# position of Category field
category_position_dict = {"Advanced Japanese": 8,
                          "WK Ultimate Vocab": 4,
                          "Core 6k Optimized": 6,
                          "Audio Vocabulary": 6}

# position of Full meaning field
definition_position_dict = {"KanjiDamage+": 5}
# position of Nanori field
nanori_position_dict = {"KanjiDamage+": 9}

note_types_dict = get_nid_dict()

if __name__ == "__main__":
    begin_time = time()
    shutil.copy(config.live_db, config.temp_db)

    # get the categories for vocab
    # process_vocab("Core 6k Optimized")
    # process_vocab("Audio Vocabulary")

    # get the definitions for kanji
    # set update=True to also check notes that already have a meaning set
    # process_kanji("KanjiDamage+", update=True)

    # force update of nanori fields
    # process_kanji_nanori("KanjiDamage+", update=True)

    # get everything with the "common" tag from jisho, and save to separate DB
    # pretty much obsolete now, the other can handle "common" words too
    # get_common_vocab(start_page=1)

    # get all entries with a specific tag
    # list of tags: https://jisho.org/docs
    # create_db_for_tag("jlpt-n2")
    # create_db_for_tag("jlpt-n1")
    # get_vocab_with_tag("med")

    # list of useful tags
    tag_list = ["common", "comp", "col", "derog", "chn", "fam", "fem", "bus", "econ", "finc", "food", "ksb", "m-sl",
                "joc", "male", "vulg", "net-sl", "wasei", "X", "yoji", "sens", "exp", "med", "math", "jlpt-n2",
                "jlpt-n1"]
    short_list = ["math", "jlpt-n2", "jlpt-n1"]
    result_list = []
    for tag in tag_list:
        result_list.append(get_vocab_with_tag(tag))
    print()
    for result in result_list:
        print(result)
    print()

    # fill in the meanings and cats fields
    total = 0
    for tag in tag_list:
        total += process_vocab_with_tag(tag, update=False)
    print(f"Processed {total} entries in total.")

    # compare the common list with the ones in anki
    # optionally also add a tag to the notes
    # compare_common("Advanced Japanese")

    # compare the common list with the ones in anki and add a tag to the notes
    # add_tags_from_db("Advanced Japanese", "common")

    # compare and copy missing ones to the other table
    # copy_common_vocab(compare_common("Advanced Japanese"))

    # compare the missing list with ones in anki
    # compare_missing("Advanced Japanese")

    # delete duplicates in tables, obsolete now
    # delete_duplicates("common")
    # delete_duplicates("missing")

    # main()

    print(f"\nCompleted in {calculate_time(begin_time)}.\n")

    # if input("Update the live Anki database? (y/n)> ").lower() == "y":
    #     shutil.copy(config.temp_db, config.live_db)
    #     print("Live Anki database updated.")
    # else:
    #     print("Live Anki database NOT updated.")
