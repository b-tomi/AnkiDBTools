import shutil

from shared import *


def process_sentences(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        src_fld_list = sentences_pos_dict.get(source)
        tgt_fld_list = sentences_pos_dict.get(target)
        notes_count = 0
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(sql_command)
        src_list = list(cursor.fetchall())
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        tgt_list = list(cursor.fetchall())
        for src_line in src_list:
            split_src_line = src_line[1].split("\x1f")
            for tgt_line in tgt_list:
                split_tgt_line = tgt_line[1].split("\x1f")
                if source == "Core 6k Optimized":
                    if split_src_line[0] == split_tgt_line[0]:
                        changed = False
                        # find the next next (if any) empty position for the sentence
                        f_pos = find_next_position(tgt_line[1], tgt_fld_list)
                        # do 10+12 unless 10 is empty then do 9+12 (unless 9 empty too)
                        if f_pos != 0 and split_src_line[10 - 1] != "":
                            # so 0+1 unless 0 empty then do 2+3
                            split_tgt_line[f_pos - 1] = split_src_line[src_fld_list[0] - 1]
                            split_tgt_line[f_pos] = split_src_line[src_fld_list[1] - 1]
                            changed = True
                        elif f_pos != 0 and split_src_line[9 - 1] != "":
                            split_tgt_line[f_pos - 1] = split_src_line[src_fld_list[2] - 1]
                            split_tgt_line[f_pos] = split_src_line[src_fld_list[3] - 1]
                            changed = True
                        if changed:
                            new_line = "\x1f".join(split_tgt_line)
                            command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {tgt_line[0]}"
                            conn.execute(command)
                            notes_count += 1
                else:
                    if split_src_line[0] == split_tgt_line[0]:
                        changed = False
                        # find the next next (if any) empty position for the sentence
                        f_pos = find_next_position(tgt_line[1], tgt_fld_list)
                        # if all fields empty, copy all 6 fields (even if empty?)
                        if f_pos == tgt_fld_list[0] and split_src_line[src_fld_list[0] - 1] != "":
                            # so 0+1 unless 0 empty then do 2+3
                            # also add <b> </b> around the word to JP sentences
                            # only works for lines with no furigana
                            split_tgt_line[f_pos - 1] = mk_bold(split_src_line[src_fld_list[0] - 1], split_src_line[0])
                            split_tgt_line[f_pos] = split_src_line[src_fld_list[1] - 1]
                            split_tgt_line[f_pos + 1] = mk_bold(split_src_line[src_fld_list[2] - 1], split_src_line[0])
                            split_tgt_line[f_pos + 2] = split_src_line[src_fld_list[3] - 1]
                            split_tgt_line[f_pos + 3] = mk_bold(split_src_line[src_fld_list[4] - 1], split_src_line[0])
                            split_tgt_line[f_pos + 4] = split_src_line[src_fld_list[5] - 1]
                            changed = True
                        # if 2 fields taken, copy first 4 fields (even if empty?)
                        elif f_pos == tgt_fld_list[2] and split_src_line[src_fld_list[0] - 1] != "":
                            split_tgt_line[f_pos - 1] = mk_bold(split_src_line[src_fld_list[0] - 1], split_src_line[0])
                            split_tgt_line[f_pos] = split_src_line[src_fld_list[1] - 1]
                            split_tgt_line[f_pos + 1] = mk_bold(split_src_line[src_fld_list[2] - 1], split_src_line[0])
                            split_tgt_line[f_pos + 2] = split_src_line[src_fld_list[3] - 1]
                            changed = True
                        # if 4 fields taken, copy first 2 fields (even if empty?)
                        elif f_pos == tgt_fld_list[4] and split_src_line[src_fld_list[0] - 1] != "":
                            split_tgt_line[f_pos - 1] = mk_bold(split_src_line[src_fld_list[0] - 1], split_src_line[0])
                            split_tgt_line[f_pos] = split_src_line[src_fld_list[1] - 1]
                            changed = True
                        if changed:
                            new_line = "\x1f".join(split_tgt_line)
                            command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {tgt_line[0]}"
                            conn.execute(command)
                            notes_count += 1
        if notes_count > 0:
            conn.commit()
            print(f"{notes_count}/{len(src_list)} notes processed from {source} in {calculate_time(start_time)}.")
        else:
            print("No changes.")


def find_next_position(line_in, list_in):
    split_line = line_in.split("\x1f")
    for pos in list_in:
        if split_line[pos - 1] == "":
            return pos
    # if no empty line
    return 0


def fix_duplicates(note_type):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        notes_count = 0
        fields_list = sentences_pos_dict.get(note_type)
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(note_type, note_types_dict)}"
        cursor = conn.execute(sql_command)
        notes_list = list(cursor.fetchall())
        for line in notes_list:
            changed = False
            split_line = line[1].split("\x1f")
            # skip notes with no sentences, and notes with just one
            if split_line[fields_list[0] - 1] != "" and split_line[fields_list[2] - 1] != "":
                # compare the english lines EN2 with EN1
                # fields_list[3] with fields_list[1]
                if split_line[fields_list[3] - 1] == split_line[fields_list[1] - 1]:
                    split_line[fields_list[2] - 1] = ""
                    split_line[fields_list[3] - 1] = ""
                    changed = True
                # then EN3 with EN2 & EN1
                # fields_list[5] with fields_list[3] & fields_list[1]
                elif split_line[fields_list[5] - 1] == split_line[fields_list[3] - 1] \
                        or split_line[fields_list[5] - 1] == split_line[fields_list[1] - 1]:
                    split_line[fields_list[4] - 1] = ""
                    split_line[fields_list[5] - 1] = ""
                    changed = True
                if changed:
                    # print(line[1])
                    # print(new_line)
                    new_line = "\x1f".join(move_sentences_up(split_line, fields_list))
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {line[0]}"
                    conn.execute(command)
                    notes_count += 1
        if notes_count > 0:
            conn.commit()
            print(f"{notes_count}/{len(notes_list)} notes cleaned of duplicates in {note_type} "
                  f"in {calculate_time(start_time)}.")
        else:
            print("No duplicates found.")


# find and remove cringy example sentences
def purge_cringe(target):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        notes_count = 0
        fields_list = sentences_pos_dict.get(target)
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        notes_list = list(cursor.fetchall())
        for line in notes_list:
            changed = False
            split_line = line[1].split("\x1f")
            # see if the EN line is cringy, and delete both lines
            if find_cringe(split_line[fields_list[1] - 1]):
                split_line[fields_list[0] - 1] = ""
                split_line[fields_list[1] - 1] = ""
                changed = True
            if find_cringe(split_line[fields_list[3] - 1]):
                split_line[fields_list[2] - 1] = ""
                split_line[fields_list[3] - 1] = ""
                changed = True
            if find_cringe(split_line[fields_list[5] - 1]):
                split_line[fields_list[4] - 1] = ""
                split_line[fields_list[5] - 1] = ""
                changed = True
            if changed:
                # make sure that the example sentences fill the earlier fields
                new_line = "\x1f".join(move_sentences_up(split_line, fields_list))
                command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {line[0]}"
                conn.execute(command)
                notes_count += 1
        if notes_count > 0:
            conn.commit()
            print(f"{notes_count}/{len(notes_list)} notes purged of cringe in {target} "
                  f"in {calculate_time(start_time)}.")
        else:
            print(f"No cringy example sentences in {target}.")


def find_cringe(line_in):
    if line_in.find("Tofugu") > -1 or line_in.find("Koichi") > -1 or line_in.find("Viet") > -1 \
            or line_in.find("Fugu") > -1 or line_in.find("WaniKani") > -1 or line_in.find("TextFugu") > -1:
        return True
    return False


def move_sentences_up(line_list_in, field_list_in):
    # if empty, fill the lines for the first example sentence
    if line_list_in[field_list_in[0] - 1] == "" and line_list_in[field_list_in[2] - 1] != "":
        line_list_in[field_list_in[0] - 1] = line_list_in[field_list_in[2] - 1]
        line_list_in[field_list_in[1] - 1] = line_list_in[field_list_in[3] - 1]
        line_list_in[field_list_in[2] - 1] = ""
        line_list_in[field_list_in[3] - 1] = ""
    elif line_list_in[field_list_in[0] - 1] == "" and line_list_in[field_list_in[4] - 1] != "":
        line_list_in[field_list_in[0] - 1] = line_list_in[field_list_in[4] - 1]
        line_list_in[field_list_in[1] - 1] = line_list_in[field_list_in[5] - 1]
        line_list_in[field_list_in[4] - 1] = ""
        line_list_in[field_list_in[5] - 1] = ""
    # if still empty, fill the lines for the second example sentence
    if line_list_in[field_list_in[2] - 1] == "" and line_list_in[field_list_in[4] - 1] != "":
        line_list_in[field_list_in[2] - 1] = line_list_in[field_list_in[4] - 1]
        line_list_in[field_list_in[3] - 1] = line_list_in[field_list_in[5] - 1]
        line_list_in[field_list_in[4] - 1] = ""
        line_list_in[field_list_in[5] - 1] = ""
    return line_list_in


def tatoeba_copy(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        notes_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(sql_command)
        src_list = list(cursor.fetchall())
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        tgt_list = list(cursor.fetchall())
        for src_line in src_list:
            # just the 6k ones, not the extra
            if src_line[1].find("Vocab_Core6k") > -1 and src_line[1].find("Extra") == -1:
                split_src_line = src_line[2].split("\x1f")
                for tgt_line in tgt_list:
                    split_tgt_line = tgt_line[1].split("\x1f")
                    # id
                    split_tgt_line[0] = split_src_line[14]
                    # jpn - also remove the <b></b> maybe?
                    split_tgt_line[1] = split_src_line[8]
                    # en
                    split_tgt_line[2] = split_src_line[11]
                    # audio
                    split_tgt_line[3] = split_src_line[13]
                    new_line = "\x1f".join(split_tgt_line)
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {tgt_line[0]}"
                    conn.execute(command)
                    notes_count += 1
                    tgt_list.remove(tgt_line)
                    break
        if notes_count > 0:
            conn.commit()
            print(f"{notes_count} notes copied in {calculate_time(start_time)}.")


begin_time = time()
shutil.copy(config.live_db, config.temp_db)

# as pair of: JP1, EN1; JP2, EN2; JP3, EN3
# in 6k deck: Furigana, EN and Kanji, EN
sentences_pos_dict = {"Advanced Japanese": [11, 12, 13, 14, 15, 16],
                      "WK Ultimate Vocab": [5, 6, 7, 8, 9, 10],
                      "Core 6k Optimized": [10, 12, 9, 12]}

note_types_dict = get_nid_dict()

# copied to main.py
# process_sentences(source="Core 6k Optimized", target="Advanced Japanese")
# process_sentences(source="WK Ultimate Vocab", target="Advanced Japanese")
#
# fix_duplicates("Advanced Japanese")

# already cleaned, no need to run these again, really (for now)
# purge_cringe("WK Ultimate Vocab")
# purge_cringe("Advanced Japanese")

# already done, copy to the tatoeba listening deck
# tatoeba_copy(source="Core 6k Optimized", target="Audio Listening")


print(f"\nCompleted in {calculate_time(begin_time)}.\n")
if input("Update the live Anki database? (y/n)> ").lower() == "y":
    shutil.copy(config.temp_db, config.live_db)
    print("Live Anki database updated.")
else:
    print("Live Anki database NOT updated.")
