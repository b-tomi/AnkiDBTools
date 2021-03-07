import shutil
from tkinter import *

from shared import *


def lookup_vocab(from_clipboard=False):
    # fields
    vocab_label = Label(output_frame, text="Japanese", width=8)
    vocab_label.grid(row=0, column=0, pady=2)
    furigana_label = Label(output_frame, text="Furigana", width=8)
    furigana_label.grid(row=1, column=0, pady=2)
    opt_kanji_label = Label(output_frame, text="OPT Kanji", width=8)
    opt_kanji_label.grid(row=2, column=0, pady=2)
    meaning_label = Label(output_frame, text="Meaning", width=8)
    meaning_label.grid(row=3, column=0, rowspan=3, pady=2)
    category_label = Label(output_frame, text="Category", width=8)
    category_label.grid(row=6, column=0, pady=2)
    note_label = Label(output_frame, text="Note", width=8)
    note_label.grid(row=7, column=0, pady=2)
    tags_label = Label(output_frame, text="Tags", width=8)
    tags_label.grid(row=8, column=0, pady=2)
    # text boxes
    vocab_field = Text(output_frame, width=32, height=1)
    vocab_field.grid(row=0, column=1, padx=20, pady=2)
    furigana_field = Text(output_frame, width=32, height=1)
    furigana_field.grid(row=1, column=1, padx=20, pady=2)
    opt_kanji_field = Text(output_frame, width=32, height=1)
    opt_kanji_field.grid(row=2, column=1, padx=20, pady=2)
    meaning_field = Text(output_frame, width=32, height=8)
    meaning_field.grid(row=3, column=1, rowspan=3, padx=25, pady=2)
    category_field = Text(output_frame, width=32, height=1)
    category_field.grid(row=6, column=1, padx=20, pady=2)
    note_field = Text(output_frame, width=32, height=1)
    note_field.grid(row=7, column=1, padx=20, pady=2)
    tags_field = Text(output_frame, width=32, height=1)
    tags_field.grid(row=8, column=1, padx=20, pady=2)

    # copy to clipboard
    vocab_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[0]), width=6)
    vocab_button.grid(row=0, column=2, pady=1)
    furigana_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[1]), width=6)
    furigana_button.grid(row=1, column=2, pady=1)
    opt_kanji_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[2]), width=6)
    opt_kanji_button.grid(row=2, column=2, pady=1)
    meaning_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[3]), height=1, width=6)
    meaning_button.grid(row=3, column=2, pady=1)
    meaning_button2 = Button(output_frame, text="for WK", bg="#c5ced2", height=2, width=6,
                             command=lambda: to_clipboard(result_list[3], target="WK"))
    meaning_button2.grid(row=4, column=2, pady=1)
    meaning_button2 = Button(output_frame, text="for KD", bg="#a8b6bc", height=2, width=6,
                             command=lambda: to_clipboard(result_list[3], target="KD", furigana=result_list[1]))
    meaning_button2.grid(row=5, column=2, pady=1)
    category_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[4]), width=6)
    category_button.grid(row=6, column=2, pady=1)
    note_button = Button(output_frame, text="copy", command=lambda: to_clipboard(result_list[5]), width=6)
    note_button.grid(row=7, column=2, pady=1)

    source_name = input_source.get()
    if from_clipboard:
        vocab_input = input_frame.clipboard_get()
        # clear the input and insert the searched string
        entry_box.delete(0, END)
        entry_box.insert(0, vocab_input)
    elif entry_box.get() != "":
        vocab_input = entry_box.get()
    else:
        # just to avoid errors
        vocab_input = "None"
    with sqlite3.connect(config.gui_db) as conn:
        # start with an empty list just to be safe
        result_list = ["", "", "", "", "", "", ""]
        kanji_command = f"SELECT id, tags, flds FROM notes WHERE mid = {get_mid(source_name, note_types_dict)}"
        cursor = conn.execute(kanji_command)
        note_list = list(cursor.fetchall())
        for note_line in note_list:
            split_note_line = note_line[2].split("\x1f")
            if split_note_line[0] == vocab_input:
                # deal with the different note types
                if source_name == "Advanced Japanese":
                    result_list = [split_note_line[0],
                                   split_note_line[1],
                                   split_note_line[3],
                                   split_note_line[6],
                                   split_note_line[7],
                                   split_note_line[8],
                                   note_line[1]]
                elif source_name == "Core 6k Optimized":
                    result_list = [split_note_line[0],
                                   split_note_line[1],
                                   split_note_line[3],
                                   split_note_line[4],
                                   split_note_line[5],
                                   split_note_line[6],
                                   note_line[1]]
                # fill in the fields
                vocab_field.insert(END, result_list[0])
                furigana_field.insert(END, result_list[1])
                opt_kanji_field.insert(END, result_list[2])
                meaning_field.insert(END, result_list[3])
                # different background for notes with no category set
                if result_list[4] == "":
                    category_field = Text(output_frame, width=32, height=1, bg="#febcd3")
                    category_field.grid(row=6, column=1, padx=20, pady=2)
                else:
                    category_field = Text(output_frame, width=32, height=1, bg="#ffffff")
                    category_field.grid(row=6, column=1, padx=20, pady=2)
                category_field.insert(END, result_list[4])
                note_field.insert(END, result_list[5])
                # strip the initial space
                tags_field.insert(END, result_list[6].strip())

                # if found, copy the meaning to the clipboard right away
                if result_list[0] != "":
                    output_frame.clipboard_clear()
                    output_frame.clipboard_append(result_list[3])
                break


def to_clipboard(text_in, target="", furigana=""):
    output_frame.clipboard_clear()
    if target == "WK":
        text_out = text_in.replace("‣ ", "")
    elif target == "KD":
        # remove the <div> and add a dash
        text_out = text_in.replace("</div><div>‣ ", " / ")
        text_out = text_out.replace("<div>‣ ", "")
        text_out = text_out.replace("</div>", "")
        text_out = text_out.replace("<i>", "")
        text_out = text_out.replace("</i>", "")
        # an initial space wouldn't get copied to clipboard
        text_out = f"{furigana} - {text_out}"
    else:
        text_out = text_in
    output_frame.clipboard_append(text_out)


root = Tk()
root.title("Vocabulary Lookup")
root.iconbitmap("icon.ico")
root.geometry("448x600")

# use a separate copy of the DB
shutil.copy(config.live_db, config.gui_db)

note_types_dict = get_nid_dict()

input_frame = Frame(root)
input_frame.pack()

input_source = StringVar()
input_source.set("Advanced Japanese")
source_label = Label(input_frame, text="Source deck:", width=10)
source_label.grid(row=0, column=0, padx=2, pady=(5, 0))
source_menu = OptionMenu(input_frame, input_source, "Advanced Japanese", "Core 6k Optimized")
source_menu.grid(row=0, column=1, columnspan=2, padx=2, pady=(5, 0), ipadx=40)
entry_box_label = Label(input_frame, text="Search for:", width=8)
entry_box_label.grid(row=1, column=0)
entry_box = Entry(input_frame, width=29)
entry_box.grid(row=1, column=1, padx=10, pady=10, ipadx=22, ipady=2)
search_btn = Button(input_frame, text="Search", command=lookup_vocab, width=5)
search_btn.grid(row=1, column=2, columnspan=2, padx=10, pady=10, ipadx=24)
search_btn2 = Button(input_frame, text="Instant Search from Clipboard",
                     bd=2, bg="#2ecc71", fg="#34495e", height=3, width=14,
                     command=lambda: lookup_vocab(from_clipboard=True))
search_btn2.grid(row=2, column=1, columnspan=2, padx=5, pady=5, ipadx=48)

output_frame = Frame(root, height=380)
output_frame.pack()

# https://pyinstaller.readthedocs.io/en/stable/usage.html
# pyinstaller --onefile --windowed --icon icon.ico GUIsearch.py
root.mainloop()
