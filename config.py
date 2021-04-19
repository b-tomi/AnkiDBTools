# anki stuff
anki_dir = "C:/Users/tommy/AppData/Roaming/Anki2/"
# default user's database file
live_db = anki_dir + "User 1/collection.anki2"

# project stuff
project_dir = "C:/Users/tommy/PycharmProjects/AnkiDBTools/"
backup_db = project_dir + "collection.anki2.backup"
temp_db = project_dir + "collection.anki2"
gui_db = project_dir + "collection.anki2.gui"

# input text files
# the kana file also includes romaji, numbers, various punctuation, etc.
kana = project_dir + "KanaList.txt"
joyo = project_dir + "KanjiListJoyo.txt"
# 633 characters which do not appear in the list of jōyō kanji (regular-use kanji).
# 18 of these have a variant, bringing the number of character forms to 651.
jin1 = project_dir + "KanjiListJinmeiyo1.txt"
# 212 characters which are traditional forms (kyūjitai) of characters present in the list of jōyō kanji.
jin2 = project_dir + "KanjiListJinmeiyo2.txt"
# 2501 kanji ordered by frequency of use
freq = project_dir + "KanjiListFrequency.txt"
# words list from wiktionary
# https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Japanese
words10k = project_dir + "Words10k.txt"
# https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/Japanese10001-20000
words20k = project_dir + "Words20k.txt"

# kanji lists by JLPT levels
jlpt_n5 = project_dir + "KanjiListJLPTN5.txt"
jlpt_n4 = project_dir + "KanjiListJLPTN4.txt"
jlpt_n3 = project_dir + "KanjiListJLPTN3.txt"
jlpt_n2 = project_dir + "KanjiListJLPTN2.txt"
jlpt_n1 = project_dir + "KanjiListJLPTN1.txt"

# output text files
cleanup_txt = project_dir + "OUTPUT-CleanList.txt"
kanji_txt = project_dir + "OUTPUT-KanjiList.txt"
missing_txt = project_dir + "OUTPUT-MissingKanjiList.txt"
