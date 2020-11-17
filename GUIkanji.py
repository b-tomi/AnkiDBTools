from shared import *
import shutil
from tkinter import *


def lookup_kanji(by_definition=False, from_clipboard=False):
    # fields
    kanji_label = Label(output_frame, text="Kanji", width=9)
    kanji_label.grid(row=0, column=0, pady=2)
    components_label = Label(output_frame, text="Components", width=9)
    components_label.grid(row=1, column=0, pady=2)
    keyword_label = Label(output_frame, text="Keyword", width=9)
    keyword_label.grid(row=2, column=0, pady=2)
    alt_keyword_label = Label(output_frame, text="Alt Keyword", width=9)
    alt_keyword_label.grid(row=3, column=0, pady=2)
    kanji_meaning_label = Label(output_frame, text="Meaning", width=9)
    kanji_meaning_label.grid(row=4, column=0, rowspan=1, pady=2)
    kanji_tags_label = Label(output_frame, text="Tags", width=9)
    kanji_tags_label.grid(row=5, column=0, pady=2)
    # text boxes
    kanji_field = Text(output_frame, width=32, height=1)
    kanji_field.grid(row=0, column=1, padx=20, pady=2)
    components_field = Text(output_frame, width=32, height=1)
    components_field.grid(row=1, column=1, padx=20, pady=2)
    keyword_field = Text(output_frame, width=32, height=1)
    keyword_field.grid(row=2, column=1, padx=20, pady=2)
    alt_keyword_field = Text(output_frame, width=32, height=1)
    alt_keyword_field.grid(row=3, column=1, padx=20, pady=2)
    kanji_meaning_field = Text(output_frame, width=32, height=6)
    kanji_meaning_field.grid(row=4, column=1, rowspan=1, padx=25, pady=2)
    kanji_tags_field = Text(output_frame, width=32, height=1)
    kanji_tags_field.grid(row=5, column=1, padx=20, pady=2)

    # copy to clipboard
    kanji_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[0]), width=6)
    kanji_button.grid(row=0, column=2, pady=1)
    components_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[1]), width=6)
    components_button.grid(row=1, column=2, pady=1)
    keyword_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[2]), width=6)
    keyword_button.grid(row=2, column=2, pady=1)
    alt_keyword_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[3]), width=6)
    alt_keyword_button.grid(row=3, column=2, pady=1)
    kanji_meaning_button = Button(output_frame, height=1, width=6, text="copy",
                                  command=lambda: to_clipboard(result_list[4]))
    kanji_meaning_button.grid(row=4, column=2, pady=1)

    source_name = "KanjiDamage+"
    # clear everything
    search_input1 = "None"
    search_input2 = "None"
    if from_clipboard:
        search_input1 = input_frame.clipboard_get()
        # clear the input and insert the searched string
        entry_box1.delete(0, END)
        entry_box1.insert(0, search_input1)
    elif by_definition and entry_box2.get() != "":
        search_input2 = entry_box2.get()
    elif entry_box1.get() != "":
        search_input1 = entry_box1.get()
    if search_input1 != "None" or search_input2 != "None":
        with sqlite3.connect(config.gui_db) as conn:
            # start with an empty list just to be safe
            result_list = ["", "", "", "", ""]
            kanji_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source_name, note_types_dict)}"
            cursor = conn.execute(kanji_command)
            note_list = list(cursor.fetchall())
            for note_line in note_list:
                split_note_line = note_line[2].split("\x1f")
                if (by_definition and split_note_line[2] == search_input2) or split_note_line[0] == search_input1:
                    result_list = [split_note_line[0],
                                   split_note_line[1],
                                   split_note_line[2],
                                   split_note_line[3],
                                   split_note_line[4],
                                   note_line[1]]
                    break
            # fill in the fields
            kanji_field.insert(END, result_list[0])
            components_field.insert(END, result_list[1])
            keyword_field.insert(END, result_list[2])
            alt_keyword_field.insert(END, result_list[3])
            kanji_meaning_field.insert(END, result_list[4])
            # strip the initial space
            kanji_tags_field.insert(END, result_list[5].strip())

            # if found, copy the meaning to the clipboard right away
            if result_list[0] != "":
                output_frame.clipboard_clear()
                output_frame.clipboard_append(f"{result_list[0]} ({result_list[2]})")


def to_clipboard(text_in):
    output_frame.clipboard_clear()
    output_frame.clipboard_append(text_in)


root = Tk()
root.title("Kanji Lookup")
root.iconbitmap("icon.ico")
root.geometry("448x600")

# use a separate copy of the DB
shutil.copy(config.anki_db, config.gui_db)

note_types_dict = get_nid_dict()

input_frame = Frame(root)
input_frame.pack()

entry_box1_label = Label(input_frame, text="Search for kanji:", width=18)
entry_box1_label.grid(row=0, column=0)
entry_box1 = Entry(input_frame, width=20)
entry_box1.grid(row=0, column=1, padx=10, pady=10, ipadx=22, ipady=2)
search_btn1 = Button(input_frame, text="Search", width=5,
                     command=lambda: lookup_kanji())
search_btn1.grid(row=0, column=2, columnspan=2, padx=10, pady=10, ipadx=24)

entry_box2_label = Label(input_frame, text="Search for definition:", width=18)
entry_box2_label.grid(row=1, column=0)
entry_box2 = Entry(input_frame, width=20)
entry_box2.grid(row=1, column=1, padx=10, pady=10, ipadx=22, ipady=2)
search_btn2 = Button(input_frame, text="Search", width=5,
                     command=lambda: lookup_kanji(by_definition=True))
search_btn2.grid(row=1, column=2, columnspan=2, padx=10, pady=10, ipadx=24)

search_btn3 = Button(input_frame, text="Instant Search from Clipboard",
                     bd=2, bg="#2ecc71", fg="#34495e", height=3, width=14,
                     command=lambda: lookup_kanji(from_clipboard=True))
search_btn3.grid(row=2, column=1, columnspan=2, padx=0, pady=5, ipadx=48)

output_frame = Frame(root, height=380)
output_frame.pack()

# https://pyinstaller.readthedocs.io/en/stable/usage.html
# pyinstaller --onefile --windowed --icon icon.ico GUIkanji.py
root.mainloop()
