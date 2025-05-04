def get_pretty_error(sql, tokens, pos, adjust_pos=0):
    try:
        offset = tokens[pos + adjust_pos].offset
        adjust = 0
    except IndexError:
        offset = len(sql)
        adjust = 1

    return sql + "\n" + (offset + adjust) * " " + "^"

def format_options(options):
    """Formats a list like ['ADD', 'DROP', 'RENAME'] into: 'ADD', 'DROP' or 'RENAME'"""
    quoted = [f"'{opt}'" for opt in options]
    if len(quoted) == 1:
        return quoted[0]
    return ", ".join(quoted[:-1]) + " or " + quoted[-1]
