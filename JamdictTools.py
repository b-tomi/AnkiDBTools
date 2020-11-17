from jamdict import Jamdict


# for https://pypi.org/project/jamdict/
jmd = Jamdict()

# use wildcard matching to find anything starts with 食べ and ends with る: "食べ%る"
result = jmd.lookup("素人")
for entry in result.entries:
    print(entry)
    for i in range(0, len(entry.kanji_forms)):
        for j in range(0, len(entry.kana_forms)):
            for k in range(0, len(entry.senses)):
                print(f"{entry.kanji_forms[i]} {entry.kana_forms[j]} {entry.senses[k]}")

# result = jmd.lookup("%智%")
# result = jmd.lookup("瑛")
# print(result)
# print(result.chars)
# for entry in result.names:
#     # print(entry)
#     # print(len(entry.kanji_forms))
#     # print(len(entry.kana_forms))
#     # print(len(entry.senses))
#     e = str(entry.senses[0])
#     if e.find("place name") == -1 and e.find("particular person") == -1 and e.find("railway station") == -1:
#         print(f"{entry.kanji_forms[0]}[{entry.kana_forms[0]}] {entry.senses[0]}")
