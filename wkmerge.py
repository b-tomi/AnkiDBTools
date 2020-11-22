from shared import *
import shutil


def copy_notes(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        notes_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(sql_command)
        source_list = list(cursor.fetchall())
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        for target_line in target_list:
            skip = False
            for source_line in source_list:
                # only notes with the tag
                if source_line[1].find("WK_Textonly") > -1 and not skip:
                    new_line = source_line[2]
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {target_line[0]}"
                    conn.execute(command)
                    notes_count += 1
                    # remove the line so it's not processed again
                    source_list.remove(source_line)
                    # skip to the next target note, probably there's a better way but whatever
                    skip = True
        if notes_count > 1:
            conn.commit()
            print(f"{notes_count}/{len(source_list)} notes processed from {source} in {calculate_time(start_time)}.")
        else:
            print("No notes copied.")


def check_kanji(target):
    with sqlite3.connect(config.temp_db) as conn:
        notes_count = 0
        star_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        for line in target_list:
            if line[2].find(" ****") > -1:
                cleaned_line = line[2].replace(" ****", "")
                conn.execute(f"UPDATE notes SET flds = '{fix_sql(cleaned_line)}' WHERE id = {line[0]}")
                star_count += 1
            if line[1].find("NOT_IN_KD") > -1:
                notes_count += 1
            if line[2].find(" ****") > -1 and line[1].find("WK_NotInKD") == -1:
                print(line[2])
        print(f"Notes with ****: {star_count}")
        print(f"Notes with WK_NotInKD tag: {notes_count}")
        if star_count > 0:
            conn.commit()


def find_missing_kanji(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        matches_count = 0
        missing_list = []
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(sql_command)
        source_list = list(cursor.fetchall())
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        for src_line in source_list:
            split_src_line = src_line[2].split("\x1f")
            # ignore entries with images
            # if split_src_line[0].find(".jpg") == -1:
            # just skip all radicals instead
            if src_line[1].find("Kanji_RADICAL") == -1:
                # new_entry = [split_src_line[0],
                #              (split_src_line[2] + split_src_line[3]),
                #              split_src_line[5],
                #              split_src_line[6],
                #              split_src_line[8],
                #              split_src_line[1]]
                # just copy the whole thing, to make it easier to clean
                new_entry = src_line
                missing_list.append(new_entry)
            for tgt_line in target_list:
                split_tgt_line = tgt_line[2].split("\x1f")
                if split_src_line[0] == split_tgt_line[0]:
                    matches_count += 1
                    missing_list.remove(new_entry)
        print(f"Found {len(missing_list)} missing kanji.")
        return missing_list


def copy_missing_kanji(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        kanji_count = 0
        unsuspended_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        # the lines in the generated list are already split
        for src_line in source:
            split_src_line = src_line[2].split("\x1f")
            for tgt_line in target_list:
                split_tgt_line = tgt_line[2].split("\x1f")
                # set the kanji field
                split_tgt_line[0] = split_src_line[0]
                # update everything else
                split_tgt_line = copy_fields(split_src_line, split_tgt_line)
                # then add the id number
                split_tgt_line[6] = str(10000 + kanji_count)
                new_line = "\x1f".join(split_tgt_line)
                command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' " \
                          f"WHERE id = '{str(tgt_line[0])}'"
                conn.execute(command)
                # commit here so the DB isn't open before the next step
                conn.commit()
                # un-suspend if the original card has been seen already in the KD+ deck
                if cards_seen(src_line[0]):
                    cards_toggle_suspend(tgt_line[0], suspend=False)
                    unsuspended_count += 1
                target_list.remove(tgt_line)
                kanji_count += 1
                break
        if kanji_count > 0:
            # moved above, so the DB isn't locked when un-suspending cards
            # conn.commit()
            print(f"{kanji_count}/{kanji_count + len(target_list)} kanji copied.")
            print(f"{unsuspended_count}/{kanji_count} kanji set to not suspended.")
        else:
            print("No kanji copied.")


def update_original_kanji(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        kanji_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(sql_command)
        source_list = list(cursor.fetchall())
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        for src_line in source_list:
            split_src_line = src_line[2].split("\x1f")
            for tgt_line in target_list:
                split_tgt_line = tgt_line[2].split("\x1f")
                if split_src_line[0] == split_tgt_line[0]:
                    # the kanji field is already set, update the rest
                    split_tgt_line = copy_fields(split_src_line, split_tgt_line)
                    new_line = "\x1f".join(split_tgt_line)
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' " \
                              f"WHERE id = '{str(tgt_line[0])}'"
                    conn.execute(command)
                    kanji_count += 1
        if kanji_count > 0:
            # conn.commit()
            print(f"Updated {kanji_count}/{len(target_list)} original kanji.")
        else:
            print("No original kanji updated.")


def copy_fields(src_list_in, tgt_list_in):
    tgt_list_in[1] = (src_list_in[2] + src_list_in[3])
    new_on = src_list_in[5]
    if new_on == "":
        new_on = "-"
    tgt_list_in[2] = new_on
    # change kun reading format
    new_kun = src_list_in[6]
    if new_kun == "":
        new_kun = "-"
    else:
        # remove tags and styling
        new_kun = new_kun.replace("<div>", "、")
        new_kun = new_kun.replace("</div>", "")
        new_kun = new_kun.replace("<br>", "")
    tgt_list_in[3] = new_kun
    # update nanori line, no need for it to be invisible
    new_nanori = src_list_in[8]
    if new_nanori.find("<span") > -1:
        new_nanori = "-"
    tgt_list_in[4] = new_nanori
    # update components line
    tgt_list_in[5] = src_list_in[1]
    return tgt_list_in


def update_vocab(source, srcpos, target, tgtpos):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        notes_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(sql_command)
        source_list = list(cursor.fetchall())
        sql_command = f"SELECT id, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        for target_line in target_list:
            split_tgt_line = target_line[1].split("\x1f")
            for source_line in source_list:
                split_src_line = source_line[2].split("\x1f")
                # skip notes with the TEMP tag
                if split_tgt_line[0] == split_src_line[0] and source_line[1].find("TEMP") == -1:
                    # remove the bullet points
                    split_tgt_line[tgtpos - 1] = split_src_line[srcpos - 1].replace("‣ ", "")
                    new_line = "\x1f".join(split_tgt_line)
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {target_line[0]}"
                    conn.execute(command)
                    notes_count += 1
                    source_list.remove(source_line)
        if notes_count > 1:
            conn.commit()
            print(f"{notes_count}/{len(source_list)} notes processed from {source} in {calculate_time(start_time)}.")
        else:
            print("No notes copied.")


def main():
    # updates original WK Kanji entries
    update_original_kanji(source="KanjiDamage+", target="WK Ultimate Kanji")
    # returns missing kanji list
    missing_kanji_list = find_missing_kanji(source="KanjiDamage+", target="WK Ultimate Kanji")
    # updates WK Kanji+ entries from the missing kanji list
    copy_missing_kanji(source=missing_kanji_list, target="WK Ultimate Kanji+")
    print()


note_types_dict = get_nid_dict()

if __name__ == "__main__":
    begin_time = time()
    shutil.copy(config.live_db, config.temp_db)

    # already completed
    # copy_notes(source="Advanced Japanese", target="AJ TEMP")

    # one-time stuff to check if the right notes have the NOT_IN_KD tag
    # ten delete the " ****" from those notes
    # check_kanji("WK Ultimate Kanji")

    # one-time stuff to update the vocab definitions in the WK audio vocab deck
    # the srcpos/tgtpos are positions of the definition field in Anki
    # update_vocab(source="Advanced Japanese", srcpos=7, target="WK Ultimate Vocab", tgtpos=3)

    main()

    print(f"\nCompleted in {calculate_time(begin_time)}.\n")
    if input("Update the live Anki database? (y/n)> ").lower() == "y":
        shutil.copy(config.temp_db, config.live_db)
        print("Live Anki database updated.")
    else:
        print("Live Anki database NOT updated.")

# outdated
# ========
# anki_db = Path("collection.anki2.wkorig")
# temp_db = Path("collection.anki2.wkupdated")
#
# shutil.copy(anki_db, temp_db)
#
# # note_type_id = 3895406222
#
# # to copy certain fields from update WK notes to original ones
# start_time = time()
# with sqlite3.connect(temp_db) as conn:
#     vocab_count = 0
#     select_command = "SELECT flds FROM notes WHERE mid = 3895406222 AND tags LIKE \'%WK_UPD%\'"
#     cursor = conn.execute(select_command)
#     upd_list = list(cursor.fetchall())
#     split_upd_list = []
#     for upd_line in upd_list:
#         split_upd_line = upd_line[0].split("\x1f")
#         split_upd_list.append(split_upd_line)
#     select_command = "SELECT id, flds FROM notes WHERE mid = 3895406222 AND tags LIKE \'%WK_ORIG%\'"
#     cursor = conn.execute(select_command)
#     vocab_list = list(cursor.fetchall())
#     for split_upd_line in split_upd_list:
#         for vocab_line in vocab_list:
#             split_vocab_line = vocab_line[1].split("\x1f")
#             if split_vocab_line[0] == split_upd_line[0]:
#                 split_vocab_line[4] = split_upd_line[4]
#                 split_vocab_line[5] = split_upd_line[5]
#                 split_vocab_line[6] = split_upd_line[6]
#                 split_vocab_line[7] = split_upd_line[7]
#                 split_vocab_line[8] = split_upd_line[8]
#                 split_vocab_line[9] = split_upd_line[9]
#                 split_vocab_line[11] = split_upd_line[11]
#                 split_vocab_line[12] = split_upd_line[12]
#                 new_line = "\x1f".join(split_vocab_line)
#                 if new_line.find("'") > -1:
#                     new_line = new_line.replace("'", "''")
#                 command = f"UPDATE notes SET flds = '{new_line}' WHERE id = '{str(vocab_line[0])}'"
#                 conn.execute(command)
#                 vocab_count += 1
#     if vocab_count > 0:
#         conn.commit()
#     print(f"{vocab_count} vocabulary processed in {calculate_time(start_time)}.")
