from pathlib import Path


# anki stuff
anki_dir = Path(r"C:\Users\tommy\AppData\Roaming\Anki2")
anki_user_dir = Path(anki_dir / "User 1")
live_db = Path(anki_user_dir / "collection.anki2")

# project stuff
project_dir = Path(r"C:\Users\tommy\PycharmProjects\AnkiDBTools")
backup_db = Path(project_dir / "collection.anki2.backup")
temp_db = Path(project_dir / "collection.anki2")
gui_db = Path(project_dir / "collection.anki2.gui")

# input text files
# the kana file also includes romaji, numbers, various punctuation, etc.
kana = Path(project_dir / "KanaList.txt")
joyo = Path(project_dir / "KanjiListJoyo.txt")
# 633 characters which do not appear in the list of jōyō kanji (regular-use kanji).
# 18 of these have a variant, bringing the number of character forms to 651.
jin1 = Path(project_dir / "KanjiListJinmeiyo1.txt")
# 212 characters which are traditional forms (kyūjitai) of characters present in the list of jōyō kanji.
jin2 = Path(project_dir / "KanjiListJinmeiyo2.txt")
# 2501 kanji ordered by frequency of use
freq = Path(project_dir / "KanjiListFrequency.txt")
# words list from wiktionary
# https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Japanese
words10k = Path(project_dir / "Words10k.txt")
# https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Japanese10001-20000
words20k = Path(project_dir / "Words20k.txt")

# output text files
cleanup_txt = Path(project_dir / "OUTPUT-CleanList.txt")
kanji_txt = Path(project_dir / "OUTPUT-KanjiList.txt")
missing_txt = Path(project_dir / "OUTPUT-MissingKanjiList.txt")
