ACCOUNTS = {
    "cm":      ("cm@localhost", "1234"),
    "room308": ("room308@localhost", "1234"),
    "room408": ("room408@localhost", "1234"),
    "lobby":   ("lobby@localhost", "1234"),
    "room304": ("room304@localhost", "1234"),
    "room506": ("room506@localhost", "1234"),
    "room701": ("room701@localhost", "1234"),
}

THEMES = {
    "floor 3": {"room304", "room308"},
    "office": {"room304", "room308", "room408"},
    "south exposure": {"room308", "room408"},
    "smart lamp": {"room308", "room506", "room701"},
}


def short_name_from_jid(jid_str: str) -> str:
    return str(jid_str).split("@")[0]
