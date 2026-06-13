def get_pretty_error(sql, tokens, pos, adjust_pos=0, tokens_num=1):
    try:
        start_token = tokens[pos + adjust_pos]
        start_offset = start_token.offset

        if tokens_num <= 1:
            token_length = len(start_token.value)
        else:
            end_idx = pos + adjust_pos + tokens_num - 1
            if end_idx >= len(tokens):
                end_offset = len(sql)
            else:
                end_token = tokens[end_idx]
                end_offset = end_token.offset + len(end_token.value)
            token_length = end_offset - start_offset
    except IndexError:
        start_offset = len(sql) + 1
        token_length = 1

    return sql + "\n" + start_offset * " " + "^" * token_length

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
