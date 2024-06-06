import texttable
import csv
import sys


class Comand:
    def __init__(self):
        self.command = None
        self.arg = None

    def __str__(self) -> str:
        return f'{self.command}({self.arg})'

class ParseResult:
    def __init__(self):
        self.subject = None
        self.ex = []
        self.commands = []

    def __str__(self) -> str:
        LINEBREAK = '\n       '
        return f"""Subject: {self.subject}
Exclude: {', '.join(self.ex)}

Query: {LINEBREAK.join(map(str, self.commands))}
"""

class Token:
    def __init__(self) -> None:
        self.kind = None
        self.value = None

    def __str__(self) -> str:
        return f'{self.kind}[{self.value}]'

class Link:
    def __init__(self, subject=None, id=None) -> None:
        self.subject = subject
        self.id = id

class Record:
    def __init__(self, macro=None, arg=None, links=[]):
        self.macro = macro
        self.arg = arg
        self.links = links

    def to_array(self):
        return [self.macro, self.arg]

class Table:
    def __init__(self, header):
        self.header = header
        self.rows = []
        # self.indices = {
        #         'macro': {},
        #         'reverse': {}
        # }

    def add_record(self, record):
        self.rows.append(record)
        return len(self.rows) - 1

    def get_record(self, id):
        return self.rows[id]

    def to_ascii_table(self):
        header: list = self.header.copy()
        header.insert(0, 'ID')
        rows: list = [header,]

        halign = ['l' for _ in header]
        halign[0] = 'r'
        valign = ['m' for _ in header]

        for index, row in enumerate(self.rows):
            r = [index,]
            r.extend(row.to_array())
            rows.append(r)

        table = texttable.Texttable()
        table.set_cols_align(halign)
        table.set_cols_valign(valign)
        table.add_rows(rows)

        return table.draw()

    # def add_to_index(self, index, id, value):
    #     self.indices[index][]

DATABASE = {}

def lex(command: str):
    command = command.replace('\n', ' ').replace('\r', '')
    tokens = []
    pos = 0
    buf = ''
    collect = False

    while pos < len(command):
        if collect:
            if command[pos] == '"':
                t = Token()
                t.kind = 'VALUE'
                t.value = buf
                tokens.append(t)
                buf = ''
                pos += 1
                collect = False
                continue

            buf += command[pos]
            pos += 1
            continue

        if command[pos] == ' ':
            if len(buf) == 0:
                pos += 1
                continue

            t = Token()
            t.kind = 'VALUE'
            t.value = buf
            tokens.append(t)
            buf = ''
            pos += 1
            continue

        if command[pos].isalnum():
            buf += command[pos]
            pos += 1
            continue

        if command[pos] == '"':
            collect = True
            pos += 1
            continue

        break

    if collect:
        raise Exception('Unterminated string')

    if len(buf) != 0:
        t = Token()
        t.kind = 'VALUE'
        t.value = buf
        tokens.append(t)

    eof = Token()
    eof.kind = 'EOF'
    tokens.append(eof)
    return tokens

def parse(tokens: list):
    pos = 0
    r = ParseResult()

    def expect():
        nonlocal pos
        pos += 1
        t = tokens[pos]
        if t.kind != 'VALUE':
            raise Exception('Unexpected token')
        return t

    while pos < len(tokens):
        t: Token = tokens[pos]

        match (t.value):
            case 'from':
                item = expect()
                r.subject = item.value

            case 'ex':
                r.ex.append(expect().value)

            case 'filter':
                c = Comand()
                c.command = t.value

                c.arg = expect().value
                r.commands.append(c)

            case 'select':
                c = Comand()
                c.command = t.value
                c.arg = expect().value
                r.commands.append(c)

            case 'link':
                c = Comand()
                c.command = t.value
                r.commands.append(c)

        pos += 1

        if tokens[pos].kind == 'EOF':
            break

    return r

def run(pr: ParseResult):
    if pr.subject not in DATABASE:
        raise Exception(f'Unknown or unspecified subject {pr.subject}')

    subject = DATABASE[pr.subject]
    final_table = subject

    for command in pr.commands:
        match (command.command):
            case 'select':
                tmp = Table(final_table.header)
                tmp.add_record(final_table.get_record(int(command.arg)))
                final_table = tmp

            # implement other commands

    return final_table.to_ascii_table()


def main(argv):
    if len(argv) < 3:
        print('Insufficient arguments')
        return -1

    subfile = argv[1]
    linkfile = argv[2]

    with open(subfile, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        header.pop(0)

        for row in reader:
            subject = row[0]
            if subject not in DATABASE.keys():
                DATABASE[subject] = Table(header)

            DATABASE[subject].add_record(Record(row[1], row[2]))
            
        # add links via linkfile

    print('argrank testing\n\n')

    while True:
        command = ''
        command = input('> ')
        while command[len(command) - 1] != ';':
            tmp = input('  ')
            command += '\n' + tmp
        command = command.replace(';', '')
        
        print(run(parse(lex(command))))
        print()


if __name__ == '__main__':
    exit(main(sys.argv))

