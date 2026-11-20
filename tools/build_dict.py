"""Convert the FreeDict fra-eng TEI file into the compact JSON the app loads.

Usage: python3 tools/build_dict.py path/to/fra-eng.tei data/dict.json
Source: https://github.com/freedict/fd-dictionaries/tree/master/fra-eng (GPL-2.0+)
Each output entry is [french, pronunciation, part_of_speech, gender, [english, ...]].
"""
import json
import sys
import xml.etree.ElementTree as ET

NS = {"t": "http://www.tei-c.org/ns/1.0"}
POS = {"n": "noun", "v": "verb", "vi": "verb (intr.)", "vt": "verb (tr.)", "adj": "adjective",
       "adv": "adverb", "art": "article", "conj": "conjunction", "int": "interjection",
       "num": "number", "prep": "preposition", "pron": "pronoun"}
GEN = {"masc": "m", "fem": "f"}


def text(el, path):
    found = el.find(path, NS)
    return (found.text or "").strip() if found is not None else ""


def main(src, dst):
    entries = []
    for e in ET.parse(src).getroot().iterfind(".//t:body/t:entry", NS):
        word = text(e, "t:form/t:orth")
        trans = []
        for q in e.iterfind(".//t:sense//t:cit[@type='trans']/t:quote", NS):
            t = (q.text or "").strip()
            if t and t not in trans:
                trans.append(t)
        if not word or not trans:
            continue
        pos = text(e, "t:gramGrp/t:pos")
        entries.append([word, text(e, "t:form/t:pron"), POS.get(pos, pos),
                        GEN.get(text(e, "t:gramGrp/t:gen"), ""), trans])
    entries.sort(key=lambda x: x[0].lower())
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(entries)} entries -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
