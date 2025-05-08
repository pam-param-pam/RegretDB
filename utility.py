def get_pretty_error(sql, tokens, pos, adjust_pos=0):
    try:
        adjust = 0
        if tokens:
            token = tokens[pos + adjust_pos]
            offset = token.offset
            token_length = len(token.value)
            if token.type == 'STRING':  # adjust for '
                adjust += 1
        else:
            offset = adjust_pos
            token_length = 1
    except IndexError:
        offset = len(sql)
        adjust = 1
        token_length = 1
    return sql + "\n" + (offset + adjust) * " " + "^" * token_length

def format_options(options):
    """Formats a list like ['ADD', 'DROP', 'RENAME'] into: 'ADD', 'DROP' or 'RENAME'"""
    quoted = [f"'{opt}'" for opt in options]
    if len(quoted) == 1:
        return quoted[0]
    return ", ".join(quoted[:-1]) + " or " + quoted[-1]

def indent(level=0):
    return "  " * (level + 1)

def parse_boolean(boolean_str):
    return boolean_str.upper() == "TRUE"
