import shutil

from shared import *
from jishoimport import main as jishoimport
from wkmerge import main as wkmerge
from vocabmerge import main as vocabmerge


def get_kanji(name_in, include_radicals=False):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        kanji_list_out = []
        kanji_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for note_line in note_list:
            split_note_line = note_line[2].split("\x1f")
            # filter out ones with images and specifically ignored characters
            if include_radicals and split_note_line[0].find("<img") == -1 and \
                    split_note_line[0] not in ignored_characters_list:
                dict_entry = (split_note_line[0], split_note_line[2])
                kanji_list_out.append(dict_entry)
            # the "Kanji_RADICAL" tag already includes all images and ignored characters
            elif note_line[1].find("Kanji_RADICAL") == -1:
                dict_entry = (split_note_line[0], split_note_line[2])
                kanji_list_out.append(dict_entry)
        print(f"{len(kanji_list_out)}/{len(note_list)} kanji analyzed in {calculate_time(start_time)}.")
        return kanji_list_out


def process_vocab(name_in, overwrite=False):
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        field_pos = keywords_pos_dict.get(name_in) - 1
        vocab_count = 0
        vocab_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(name_in, note_types_dict)}"
        cursor = conn.execute(vocab_command)
        vocab_list = list(cursor.fetchall())
        for vocab_line in vocab_list:
            # skip if has a certain tag
            if vocab_line[1].find("Phrase") == -1:
                split_vocab_line = vocab_line[2].split("\x1f")
                # position depending on the type of the note
                if split_vocab_line[field_pos] == "" or overwrite:
                    split_vocab_line[field_pos] = generate_keywords(split_vocab_line[0])
                    new_line = "\x1f".join(split_vocab_line)
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {vocab_line[0]}"
                    conn.execute(command)
                    vocab_count += 1
        if vocab_count > 0:
            conn.commit()
        print(f"{vocab_count}/{len(vocab_list)} notes processed for {name_in} in {calculate_time(start_time)}.")


def generate_keywords(vocab_in):
    keywords_out = ""
    for character in vocab_in:
        keyword = str(kanji_dict.get(character))
        if keyword != "None":
            if keywords_out == "":
                # if it's the first keyword
                keywords_out += character + " [" + keyword + "]"
            else:
                # separate any additional ones
                keywords_out += ", " + character + " [" + keyword + "]"
        else:
            if character not in kana_list and character not in missing_kanji_dict:
                # missing_kanji_list.append(character)
                missing_kanji_dict[character] = 1
            elif character not in kana_list and character in missing_kanji_dict:
                missing_kanji_dict[character] += 1
    return keywords_out


def generate_txt(kanji_list_in, formatted=False):
    text_out = ""
    for line in kanji_list_in:
        if formatted:
            text_out += line[0] + " [" + line[1] + "]\n"
        else:
            text_out += line[0]
    try:
        config.kanji_txt.write_text(text_out, "utf-8")
        print(f"{len(kanji_list_in)} kanji found. Text file generated.")
    except UnicodeError as ex:
        print(ex)


def pre_cleanup():
    with sqlite3.connect(config.temp_db) as conn:
        start_time = time()
        cleaned_count = 0
        cursor = conn.execute(f"SELECT id, mid, tags, flds FROM notes")
        notes_list = list(cursor.fetchall())
        for line in notes_list:
            # remove the special space character from everywhere
            if line[3].find("&nbsp;") > -1:
                cleaned_line = line[3].replace("&nbsp;", " ")
                conn.execute(f"UPDATE notes SET flds = '{fix_sql(cleaned_line)}' WHERE id = {line[0]}")
                cleaned_count += 1
        if cleaned_count > 0:
            conn.commit()
            print(f"{cleaned_count}/{len(notes_list)} notes cleaned in {calculate_time(start_time)}.")
        else:
            print("No initial clean up needed.")


def cleanup():
    start_time = time()
    punctuation_list = ["。", "？", "！", "」"]
    cleaned_count = 0
    with sqlite3.connect(config.temp_db) as conn:
        cursor = conn.execute(f"SELECT id, mid, tags, flds FROM notes")
        notes_list = list(cursor.fetchall())
        # this just checks the first field for html tags, puts them in the text file for manual review
        find_html_tags(notes_list)
        for line in notes_list:
            note_cleaned = False
            # clean up the Advanced Japanese notes
            # just skip the temporary WK ones for now
            if line[1] == get_mid("Advanced Japanese", note_types_dict) and line[2].find("WK_Textonly") == -1:
                definition_cleaned = False
                sentence_cleaned = False
                split_line = line[3].split("\x1f")
                # clean all notes of <br> and possible <div><div> before doing anything else
                if split_line[6].find("<br>") > -1 or split_line[6].find("<div><div>") > 1:
                    cleaned_line = remove_html_tags(split_line[6])
                    split_line[6] = cleaned_line
                    definition_cleaned = True
                # clean up notes with multiple definition entries
                # skip if the first chars are "<div>‣ ", those should be fine
                if split_line[6].find("‣ ") > -1 and str(split_line[6])[0:7] != "<div>‣ ":
                    # clean HTML tags then re-add them to the bullet points
                    cleaned_line = remove_html_tags(split_line[6], add_bullets=True)
                    # for reference
                    print(cleaned_line)
                    split_line[6] = cleaned_line
                    definition_cleaned = True
                # clean the <div> tags in the other notes
                elif split_line[6].find("‣ ") == -1 and split_line[6].find("<div>") > -1:
                    cleaned_line = remove_html_tags(split_line[6])
                    # for reference
                    print(cleaned_line)
                    split_line[6] = cleaned_line
                    definition_cleaned = True
                if definition_cleaned:
                    new_line = "\x1f".join(split_line)
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {line[0]}"
                    conn.execute(command)
                    note_cleaned = True
                # example sentences are in fields # 11-16, so range(11-1, 17-1)
                for num in range(10, 16):
                    # fix extra space at the beginning and end of sentences
                    if split_line[num] != "" and str(split_line[num])[0] == " ":
                        cleaned_line = str(split_line[num])[1:]
                        split_line[num] = cleaned_line
                        sentence_cleaned = True
                    if split_line[num] != "" and str(split_line[num])[len(split_line[num]) - 1] == " ":
                        cleaned_line = str(split_line[num])[:-1]
                        split_line[num] = cleaned_line
                        sentence_cleaned = True
                    # remove unnecessary HTML tags
                    if split_line[num].find("<div>") > -1 or split_line[num].find("<br>") > -1:
                        cleaned_line = remove_html_tags(split_line[num])
                        split_line[num] = cleaned_line
                        sentence_cleaned = True
                    # if missing, try to add <b></b> to example sentences, if there is no furigana (just to be safe)
                    if (num == 10 or num == 12 or num == 14) and split_line[num] != "" and \
                            split_line[num].find("[") == -1 and split_line[num].find("<b>") == -1:
                        # does nothing if the vocab is conjugated
                        cleaned_line = mk_bold(split_line[num], split_line[0])
                        # so it doesn't count if no change
                        if cleaned_line != split_line[num]:
                            split_line[num] = cleaned_line
                            sentence_cleaned = True
                    # fix the unnecessary space in imported example sentences
                    if (num == 10 or num == 12 or num == 14) and split_line[num].find("<b> ") > -1:
                        cleaned_line = split_line[num].replace("<b> ", "<b>")
                        split_line[num] = cleaned_line
                        sentence_cleaned = True
                    # fix missing periods a the end of JP sentences if last char is not a punctuation mark
                    if (num == 10 or num == 12 or num == 14) and split_line[num] != "" and \
                            str(split_line[num])[len(split_line[num]) - 1] not in punctuation_list:
                        cleaned_line = split_line[num] + "。"
                        split_line[num] = cleaned_line
                        # print for reference
                        print(f"Fixed punctuation in: {cleaned_line}")
                        sentence_cleaned = True
                    if sentence_cleaned:
                        new_line = "\x1f".join(split_line)
                        command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {line[0]}"
                        conn.execute(command)
                        note_cleaned = True
                # clean up the category field
                if split_line[7].find("<div>") > -1 or split_line[7].find("<br>") > -1:
                    cleaned_line = remove_html_tags(split_line[7])
                    split_line[7] = cleaned_line
                    new_line = "\x1f".join(split_line)
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {line[0]}"
                    conn.execute(command)
                    note_cleaned = True
                # one-time stuff for Try! N1-N2 notes to clean the comment field
                # if line[2].find("DELETEFIELD8") > -1:
                #     split_line = line[3].split("\x1f")
                #     split_line[8] = ""
                #     new_line = "\x1f".join(split_line)
                #     command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' WHERE id = {line[0]}"
                #     conn.execute(command)
                #     print(f"Cleaned comment in {new_line}")
                #     note_cleaned = True
            # so a note is only counted once, even if it has multiple changes
            if note_cleaned:
                cleaned_count += 1
        if cleaned_count > 0:
            conn.commit()
            print(f"{cleaned_count}/{len(notes_list)} notes cleaned up in {calculate_time(start_time)}.")
        else:
            print("No clean up needed.")


def find_html_tags(list_in):
    text_out = ""
    found = 0
    # the number of the field (in Anki) to analyze, starts with 0
    # make sure this exists in ALL scanned notes!!! (0-2)
    # could filter by tag now, line[1]
    field_id = 0
    for line in list_in:
        split_line = line[3].split("\x1f")
        # find tags in field #line_id
        if split_line[field_id].find("<div>") > -1 or split_line[field_id].find("<br>") > -1:
            text_out += split_line[field_id] + "\n"
            found += 1
    if found > 0:
        try:
            config.cleanup_txt.write_text(text_out, "utf-8")
            print(f"{found} lines with HTML tags found. Text file generated.")
        except UnicodeError as ex:
            print(ex)
    else:
        print("No lines with HTML tags found.")


def get_kana_list(txt_file_in):
    list_out = []
    with codecs.open(txt_file_in, encoding='utf-8') as file:
        for line in file:
            for char in line:
                if char != "\r" and char != "\n":
                    list_out.append(char)
    return list_out


def generate_missing_txt(dict_in):
    # load kanji lists from the text files
    joyo_list = get_kanji_list(config.joyo)
    jin1_list = get_kanji_list(config.jin1)
    jin2_list = get_kanji_list(config.jin2)
    # vales: joyo, jin1, jin2, other
    count_list = [0, 0, 0, 0]
    text_out = ""
    # sort the kanji by number of times encountered
    for kanji, times in sorted(dict_in.items(), key=lambda item: item[1], reverse=True):
        text_out += f"{kanji}: {times}"
        if kanji in joyo_list:
            text_out += " (Joyo)\n"
            count_list[0] += 1
        elif kanji in jin1_list:
            text_out += " (Jinmeiyo)\n"
            count_list[1] += 1
        elif kanji in jin2_list:
            text_out += " (Jinmeiyo-traditional)\n"
            count_list[2] += 1
        else:
            text_out += "\n"
            count_list[3] += 1
    try:
        text_out = f"Found {count_list[0]} Joyo, {count_list[1]} Jinmeiyo, {count_list[2]} Jinmeiyo-traditional " \
                    f"and {count_list[3]} other Kanji.\n" + text_out
        config.missing_txt.write_text(text_out, "utf-8")
        print(f"{len(dict_in)} missing kanji found. Text file generated.")
    except UnicodeError as ex:
        print(ex)


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
                            command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' " \
                                      f"WHERE id = '{str(tgt_line[0])}'"
                            conn.execute(command)
                            notes_count += 1
                else:
                    # also include the entries with "する"
                    if split_src_line[0] == split_tgt_line[0] or (split_src_line[0] == split_tgt_line[0] + "する"):
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
            print(f"{notes_count}/{len(src_list)} sentences processed from {source} in {calculate_time(start_time)}.")
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
                    new_line = "\x1f".join(move_sentences_up(split_line, fields_list))
                    command = f"UPDATE notes SET flds = '{fix_sql(new_line)}' " \
                              f"WHERE id = {line[0]}"
                    conn.execute(command)
                    notes_count += 1
        if notes_count > 0:
            conn.commit()
            print(f"{notes_count}/{len(notes_list)} notes cleaned of duplicate sentences in {note_type} "
                  f"in {calculate_time(start_time)}.")
        else:
            print("No duplicate sentences found.")


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


begin_time = time()
shutil.copy(config.live_db, config.backup_db)
shutil.copy(config.live_db, config.temp_db)

# process the external stuff
jishoimport()
wkmerge()
vocabmerge()

# ignore the katakana characters that are used as radicals, and the obsolete notes
# used when generating the EXISTING kanji list from the kanji deck
ignored_characters_list = ["L", "マ", "ラ", "ヰ", "x"]

# include space characters to ignore when generating the missing kanji list
kana_list = get_kana_list(config.kana) + [" ", "　"]
# misc characters from some notes that are not kana but also need to be excluded
# used when generating the MISSING kanji list, so needs to be separate from the ignored_characters_list above
misc_chars = "ゝ゛゜ヽ゛゜ーＴ〇４１５０９10（）ABＹ！／LINEｘ962D８ＰＢＷ/ＳＥＭTPO．ＩＯＣＲＤＧ<sub>・(R)~VMalt.r,3CG２３ＪＫＬ" \
             "々～〜…？!，、。Ｆ；SＡＮＵ７６ＸΑΒΓΔΩ＆ＶＨｉ"
# probably it's not even necessary to still ignore some of these, but might as well add them anyway
for misc_char in misc_chars:
    kana_list.append(misc_char)

keywords_pos_dict = {"Advanced Japanese": 10,
                     "WK Ultimate Vocab": 11,
                     "Core 6k Optimized": 8}

# fields for the example sentences
# as pair of: JP1, EN1; JP2, EN2; JP3, EN3
# in 6k deck: Furigana, EN and Kanji, EN
sentences_pos_dict = {"Advanced Japanese": [11, 12, 13, 14, 15, 16],
                      "WK Ultimate Vocab": [5, 6, 7, 8, 9, 10],
                      "Core 6k Optimized": [10, 12, 9, 12]}

note_types_dict = get_nid_dict()

kanji_list = get_kanji("KanjiDamage+", include_radicals=True)
kanji_dict = dict(kanji_list)

# save the kanji list in a text file
generate_txt(kanji_list, formatted=True)

# dictionary of kanji used in vocab but not present in the kanji deck, and times encountered
missing_kanji_dict = {}

process_vocab("Advanced Japanese", overwrite=True)
process_vocab("WK Ultimate Vocab", overwrite=True)
process_vocab("Core 6k Optimized", overwrite=True)

# save the missing kanji list in a text file
generate_missing_txt(missing_kanji_dict)
print()

# replace any "&nbsp;" with normal spaces
pre_cleanup()

# copy example sentences from source to target notes, then clean up duplicates so there's room for more
process_sentences(source="Core 6k Optimized", target="Advanced Japanese")
fix_duplicates("Advanced Japanese")
process_sentences(source="WK Ultimate Vocab", target="Advanced Japanese")
fix_duplicates("Advanced Japanese")

#  clean up example sentences, etc.
cleanup()

print(f"\nCompleted in {calculate_time(begin_time)}.\n")
# just update the live DB right away
shutil.copy(config.temp_db, config.live_db)
print("Live Anki database updated.")

# if input("Update the live Anki database? (y/n)> ").lower() == "y":
#     shutil.copy(config.temp_db, config.live_db)
#     print("Live Anki database updated.")
# else:
#     print("Live Anki database NOT updated.")
