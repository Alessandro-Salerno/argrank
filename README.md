# argrank
**BETTER DOCUMENTATION IS COMING**


argrank is a program developed to help italian students with their end-of-school exam.

The exam requires students to speak in front of a commission of six professors about all subjects, from history, to computer science, economics, mathemtics, computer netowrking, etc.

The goal of argrank is to help students prepare for this exam by exploring possible links between subjects that can be used to build a more coherent speach. For example, one could ask argrank to build a full roadmap of subjects and topics starting from the [Cuban Missile Crisis](https://en.wikipedia.org/wiki/Cuban_Missile_Crisis).

## argrank query language
argrank uses its own query languages and supports the SQL concept of closure.
argrank query language is comprised of pre-processed statements and executable commands

| COMMAND | TYPE | DESCRIPTION |
| - | - | - |
| `from` | Preprocessed | Specifies the subject of the query (e.g., history) |
| `ex` | Preprocessed | Excludes results relating to a given subject |
| `filter` | Executable | Filters results by macro-topic using fuzzy search |
| `select` | Executable | Selects a single row from a table using the IDX field |
| `link` | Executable | Scrapes the database to find possible links with other subjects. ONLY WORKS ON TABLES WITH ONE ROW |
| `routes` | Executable | Shows all routes for a given table |

The main difference between preprocessed and executable commands is that the former ones can be placed out of order, while the latter ones are executed in order and, as such, need to placed correctly.

For example, these are both perfecly correct AQL queries to find the first row about the cold war and link it with all subjects aside from computer networking
```
from history
filter "cold war"
select 0
link
ex networking
```

And...
```
filter "cold war"
select 0
link
from history
ex networking
```

## How to install argrank
* Windows:
```
pip install git+https://github.com/Alessandro-Salerno/argrank
```
* macOS/Linux:
```
pip3 install git+https://github.com/Alessandro-Salerno/argrank
```

## How to use argrank
* Create a CSV file to hold all subject/topic data
```csv
"SUBJECT","MACRO TOPIC","TOPIC"
"History","Great Depression","Black Tuesday"
"Maths","Integrals","Defined Integrals"
"Networking","Lab","CISCO Packet Tracer"
```
* Create a second CSV file to hold links between topics. Links are expressed using line numbers of the first file and have effect for both topics (i.e., there's no need to say `2,3` and `3,2`)
```csv
"FROM TOPIC","TO TOPPIC"
2,3
2,4
3,4
```
* Run argrank with one of the follogin commands:
To open argrank in the CLI:
```
<your python> -m argrank --cli <first file>.csv <second file>.csv
```

To launch a WebSocket server:
```
<your python> -m argrank --server <first file>.csv <second file>.csv
```

## Usecase example (Italian)
```
argrank cli
follow the instructions at https://github.com/Alessandro-Salerno/argrank

> from storia
  filter "grande depressione"
  select 0
  link;
+-----+----+---------------------------+---------------------------+
| IDX | ID |           FROM            |            TO             |
+=====+====+===========================+===========================+
|   0 |  0 | crollo di wall street     | domanda ed offerta        |
+-----+----+---------------------------+---------------------------+
|   1 |  1 | crollo di wall street     | la prima api della storia |
+-----+----+---------------------------+---------------------------+
|   2 |  2 | la prima api della storia | le api in generale        |
+-----+----+---------------------------+---------------------------+

> from storia
  select 0
  routes;
+-----+----+-----------------------+---------+----------+
| IDX | ID |         TOPIC         | SUBJECT | NEXT HOP |
+=====+====+=======================+=========+==========+
|   0 |  0 | crollo di wall street | gpoi    | 3        |
+-----+----+-----------------------+---------+----------+
|   1 |  1 | crollo di wall street | tpsi    | 5        |
+-----+----+-----------------------+---------+----------+

> exit;
Good bye
```
