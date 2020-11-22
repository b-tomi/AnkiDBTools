from shared import *
import shutil


def find_missing_vocab(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        matches_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(sql_command)
        source_list = list(cursor.fetchall())
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        for target_line in target_list:
            split_target_line = target_line[2].split("\x1f")
            for source_line in source_list:
                # if it has the DUPE tag, just remove it right away
                if source_line[1].find("Vocab_Core_DUPE") > -1:
                    source_list.remove(source_line)
                else:
                    split_source_line = source_line[2].split("\x1f")
                    # keep the note if it's in the suspended deck
                    if split_source_line[0] == split_target_line[0] and target_line[1].find("TEMP") == -1:
                        matches_count += 1
                        source_list.remove(source_line)
        if matches_count > 0:
            print(f"{matches_count} matches found in {source} in {calculate_time(start_time)}.")
        print(f"{len(source_list)} missing vocab found.")
        return source_list


def check_if_seen(list_in):
    list_out = []
    for line in list_in:
        if cards_seen(line[0]):
            list_out.append(line)
    print(f"{len(list_out)} seen vocab found.")
    return list_out


def copy_notes(source_list, target):
    with sqlite3.connect(config.temp_db) as conn:
        copied_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        for source_line in source_list:
            split_source_line = source_line[2].split("\x1f")
            for target_line in target_list:
                split_target_line = target_line[2].split("\x1f")
                # japanese
                split_target_line[0] = split_source_line[0]
                # furigana
                split_target_line[1] = split_source_line[1]
                # kana
                split_target_line[2] = split_source_line[2]
                # opt kanji
                split_target_line[3] = split_source_line[3]
                # meaning
                split_target_line[6] = split_source_line[4]
                # category
                split_target_line[7] = split_source_line[5]
                # note
                split_target_line[8] = split_source_line[6]
                # sentence JP
                split_target_line[10] = split_source_line[9]
                # sentence EN
                split_target_line[11] = split_source_line[11]
                new_line = "\x1f".join(split_target_line)
                command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {target_line[0]}"
                conn.execute(command)
                # commit now so it can also un-suspend the cards
                conn.commit()
                cards_toggle_suspend(target_line[0], suspend=False)
                # print for reference
                print(split_source_line[0])
                copied_count += 1
                target_list.remove(target_line)
                break
        if copied_count > 0:
            # conn.commit()
            print(f"{copied_count}/{copied_count + len(target_list)} notes filled.")
        else:
            print("No notes copied.")


def update_wk_vocab(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        updated_count = 0
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(sql_command)
        source_list = list(cursor.fetchall())
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        for target_line in target_list:
            # just do the ones with the tag
            if target_line[1].find("WK_Textonly") > -1:
                split_target_line = target_line[2].split("\x1f")
                for source_line in source_list:
                    split_source_line = source_line[2].split("\x1f")
                    if split_target_line[0] == split_source_line[0]:
                        split_target_line[6] = split_source_line[2]
                        new_line = "\x1f".join(split_target_line)
                        command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {target_line[0]}"
                        conn.execute(command)
                        updated_count += 1
        if updated_count > 0:
            # conn.commit()
            print(f"{updated_count} notes updated from {source} in {calculate_time(start_time)}.")
        return source_list


def copy_hj_vocab(source, target):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        updated_count = 0
        # just do the ones with the tag
        sql_command = f"SELECT id, tags, flds FROM notes WHERE tags LIKE '%TOCOPY%'"
        cursor = conn.execute(sql_command)
        source_list = list(cursor.fetchall())
        print(len(source_list))
        sql_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(target, note_types_dict)}"
        cursor = conn.execute(sql_command)
        target_list = list(cursor.fetchall())
        print(len(target_list))
        for source_line in source_list:
            for target_line in target_list:
                new_tags = source_line[1]
                new_line = source_line[2]
                command = f"UPDATE notes SET tags = '{fix_sql(new_tags)}', flds = '{fix_sql(new_line)}' " \
                          f"WHERE id = {target_line[0]}"
                conn.execute(command)
                updated_count += 1
                target_list.remove(target_line)
                break
        if updated_count > 0:
            conn.commit()
            print(f"{updated_count} notes updated from {source} in {calculate_time(start_time)}.")
        return


def main():
    missing_list = find_missing_vocab(source="Core 6k Optimized", target="Advanced Japanese")
    seen_missing_list = check_if_seen(missing_list)
    copy_notes(seen_missing_list, target="AJTEMP")
    update_wk_vocab(source="WK Ultimate Vocab", target="Advanced Japanese")
    print()


note_types_dict = get_nid_dict()

if __name__ == "__main__":
    begin_time = time()
    shutil.copy(config.live_db, config.temp_db)

    main()

    # one-time stuff to re-use the old HJ/HJI/etc. notes
    # copy_hj_vocab(source="Core 6k Optimized", target="Core 6k TEMP")

    print(f"\nCompleted in {calculate_time(begin_time)}.\n")

    if input("Update the live Anki database? (y/n)> ").lower() == "y":
        shutil.copy(config.temp_db, config.live_db)
        print("Live Anki database updated.")
    else:
        print("Live Anki database NOT updated.")
