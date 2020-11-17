from shared import *
import shutil


def get_files_list(source, tag=""):
    with sqlite3.connect(config.temp_db) as conn:
        field_pos = audio_pos_dict.get(source) - 1
        files_list = []
        kanji_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for line in note_list:
            # if no tag specified, include all notes
            if tag == "" or line[1].find(tag) > -1:
                split_line = line[2].split("\x1f")
                file_name = str(split_line[field_pos])
                file_name = file_name.replace("[sound:", "")
                file_name = file_name.replace("]", "")
                files_list.append(file_name)
        print(f"{len(files_list)} audio files found.")
        return files_list


def copy_files(files_list):
    for file_name in files_list:
        shutil.copy(config.anki_user_dir / "collection.media" / file_name,
                    config.project_dir / "collection.media" / file_name)


begin_time = time()

shutil.copy(config.anki_db, config.backup_db)

audio_pos_dict = {"Audio Vocabulary": 8}

note_types_dict = get_nid_dict()

audio_files_list = get_files_list("Audio Vocabulary", tag="Vocab_TangoN5")

copy_files(audio_files_list)

print(f"\nCompleted in {calculate_time(begin_time)}.\n")
