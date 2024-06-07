import texttable
import asyncio
from websockets.server import serve
import csv
import sys
import regex


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

    def __str__(self) -> str:
        return f'{self.subject}({self.id})'


class Record:
    def __init__(self, macro=None, arg=None, links=[], subject=None):
        self.id = None
        self.subject = subject
        self.macro = macro
        self.arg = arg
        self.links = []

    def to_array(self):
        return [self.id, self.macro, self.arg]


class LinkedRecord:
    def __init__(self, subject, start_topic, end_topic) -> None:
        self.id = None
        self.subject = subject
        self.start_topic = start_topic
        self.end_topic = end_topic

    def to_array(self):
        return [self.id, self.start_topic, self.end_topic]


class RouteRecord:
    def __init__(self, topic, subject, next_hop) -> None:
        self.id = None
        self.topic = topic
        self.subject = subject
        self.next_hop = next_hop

    def to_array(self):
        return [self.id, self.topic, self.subject, self.next_hop]


class Table:
    def __init__(self, header):
        self.header = header
        self.insert_index = 0
        self.rows = []

    def add_record(self, record):
        self.rows.append(record)
        if record.id == None:
            record.id = self.insert_index
            self.insert_index += 1
        return record.id

    def get_record(self, id):
        return self.rows[id]

    def fuzzy_search(self, col, item):
        result = []
        for row in self.rows:
            r = regex.findall('(%s){e<=3}' % row.to_array()[col], item, overlapped=True)
            if len(r) > 0:
                result.append(row)
        return result

    def to_ascii_table(self):
        if len(self.rows) == 0:
            return 'Empty set'

        header: list = self.header.copy()
        header.insert(0, 'ID')
        header.insert(0, 'IDX')
        rows: list = [header,]

        halign = ['l' for _ in header]
        halign[0] = 'r'
        halign[1] = 'r'
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


class RootTable(Table):
    def get_record(self, id):
        return self.rows[id - 2]


DATABASE = {}
LOOKUP = {}
ROOT_TABLE: RootTable = None


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

            case 'filter' | 'select':
                c = Comand()
                c.command = t.value
                c.arg = expect().value
                r.commands.append(c)

            case 'link' | 'routes' | 'exit':
                c = Comand()
                c.command = t.value
                r.commands.append(c)

        pos += 1

        if pos > len(tokens) or tokens[pos].kind == 'EOF':
            break

    return r


def link(excludes, topic, base_topic, prev_hop=None, explored=None):
    table = Table(['FROM', 'TO'])

    if explored == None:
        explored = []

    if prev_hop == None:
        prev_hop = base_topic

    if topic == None:
        return table

    def subjects(t):
        s = []
        for row in t.rows:
            if row.subject not in s:
                s.append(row.subject)
        return s

    def count_subjects(t):
        return len(subjects(t))

    aux_tables = []

    for l in topic.links:
        if l.subject not in excludes and l.id not in explored and l.id != base_topic.id:
            hop = ROOT_TABLE.get_record(l.id)
            explored.append(l.id)
            r = link(excludes, hop, base_topic, topic, explored)
            if topic == base_topic:
                explored.clear()
            t = Table(table.header)
            t.add_record(LinkedRecord(hop.subject, topic.arg, hop.arg))

            for row in r.rows:
                t.add_record(LinkedRecord(row.subject, row.start_topic, row.end_topic))

            if count_subjects(t) > count_subjects(table):
                aux_tables.append(table)
                table = t
            elif topic == base_topic:
                aux_tables.append(t)

    if topic == base_topic and count_subjects(table) < len(DATABASE.keys()):
        s = subjects(table)
        aux_tables = sorted(aux_tables, key=lambda t: len(t.rows), reverse=True)
        for aux in aux_tables:
            for index, row in enumerate(aux.rows):
                if row.subject not in s or row.subject == base_topic.subject or (index > 0 and aux.rows[index - 1].subject == row.subject):
                    row.id = None
                    table.add_record(row)
                    s.append(row.subject)

    return table


def run(pr: ParseResult):
    if pr.subject and pr.subject not in DATABASE:
        raise Exception(f'Unknown or unspecified subject {pr.subject}')

    final_table = ROOT_TABLE
    if pr.subject:
        final_table = DATABASE[pr.subject]

    for command in pr.commands:
        match (command.command):
            case 'select':
                tmp = Table(final_table.header)
                tmp.add_record(final_table.get_record(int(command.arg)))
                final_table = tmp

            case 'filter':
                tmp = Table(final_table.header)
                for row in final_table.fuzzy_search(1, command.arg):
                    tmp.add_record(row)
                final_table = tmp

            case 'link':
                if len(final_table.rows) != 1:
                    raise Exception('Invalid input table')

                final_table = link(pr.ex, final_table.rows[0], final_table.rows[0])

            case 'routes':
                tmp = Table(['TOPIC', 'SUBJECT', 'NEXT HOP'])
                for r in final_table.rows:
                    for l in r.links:
                        tmp.add_record(RouteRecord(r.arg, l.subject, l.id))
                final_table = tmp

            case 'exit':
                return 'Good bye'


    return final_table.to_ascii_table()


def main(argv):
    if len(argv) < 4:
        print('Insufficient arguments')
        return -1

    subfile = argv[2]
    linkfile = argv[3]

    with open(subfile, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        header.pop(0)
        global ROOT_TABLE
        ROOT_TABLE = RootTable(header)

        for index, row in enumerate(reader):
            subject = row[0]
            if subject not in DATABASE.keys():
                t = Table(header)
                DATABASE[subject] = t

            r = Record(row[1], row[2], subject=subject)
            r.id = index + 2
            DATABASE[subject].add_record(r)
            ROOT_TABLE.add_record(r)

    if 'misc' in DATABASE.keys():
        DATABASE.pop('misc')

    with open(linkfile, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

        for row in reader:
            start_topic = int(row[0])
            end_topic = int(row[1])

            s = ROOT_TABLE.get_record(start_topic)
            e = ROOT_TABLE.get_record(end_topic)

            l = Link(e.subject, end_topic)
            s.links.append(l)
            
            l = Link(s.subject, start_topic)
            e.links.append(l)

    match (argv[1]):
        case '--server':
            print('argrank websocket server')
            print('listening on port 8765')

            async def echo(websocket):
                async for message in websocket:
                    try:
                        r = run(parse(lex(str(message))))
                        await websocket.send(r)
                    except Exception as e:
                        await websocket.send(f'ERROR: {e}')

            async def serve_main():
                async with serve(echo, "localhost", 8765):
                    await asyncio.Future()

            asyncio.run(serve_main())

        case '--cli':
            print('argrank cli')
            print('follow the instructions at https://github.com/Alessandro-Salerno/argrank')
            print()

            while True:
                command = ''
                command = input('> ')
                while command[len(command) - 1] != ';':
                    tmp = input('  ')
                    command += '\n' + tmp
                command = command.replace(';', '')
                
                try:
                    r = run(parse(lex(command)))
                    print(r)
                    if r == 'Good bye':
                        return 0
                except KeyboardInterrupt as ki:
                    raise ki
                except Exception as e:
                    print(f'ERROR: {e}')
                finally:
                    print()

        case _:
            print('ERROR: Use --server or --cli')
            return -1


if __name__ == '__main__':
    exit(main(sys.argv))

