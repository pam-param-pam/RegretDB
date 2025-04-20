def visualize_table(tables):
    for table_name, table in tables.items():
        columns = table[0]
        rows = table[1:]

        col_widths = [len(col) for col in columns]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        def divider():
            return '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'

        def format_row(row_data):
            return '| ' + ' | '.join(f"{str(val).ljust(col_widths[i])}" for i, val in enumerate(row_data)) + ' |'

        print(f"\nTable: {table_name}")
        print(divider())
        print(format_row(columns))
        print(divider())
        for row in rows:
            print(format_row(row))
        print(divider())


# Example tables
tables = {
    "players": [
        ("id", "name", "age"),
        (1, "Pam", 19),
        (2, "Guard", 20),
        (3, "Player738", 17)
    ],
    "clans": [
        ("id", "name"),
        (1, "_Elite"),
        (2, "Entity"),
        (3, "")
    ]
}

visualize_table(tables)



