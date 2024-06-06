# argrank
**BETTER DOCUMENTATION IS COMING**


argrank is a program developed to help italian students with their end-of-school exam.

The exam requires students to speak in front of a commission of six professors about all subjects, from history, to computer science, economics, mathemtics, computer netowrking, etc.

The goal of argrank is to help students prepare for this exam by exploring possible links between subjects that can be used to build a more coherent speach. For example, one could ask argrank to build a full roadmap of subjects and topics starting from the [Cuban Missile Crisis]().

## argrank query language
argrank uses its own query languages and supports the SQL concept of closure.
argrank query language is comprised of pre-processed statements and executable commands

| COMMAND | TYPE | DESCRIPTION |
| - | - | - |
| `from` | Preprocessed | Specifies the subject of the query (e.g., history) |
| `ex` | Preprocessed | Excludes results relating to a subject |
| `filter` | Executable | Filters results by macro-topic or topic |
| `select` | Executable | Selects a single row from a table |
| `link` | Executable | Scrapes the database to find possible links with other subjects. ONLY WORKS ON TABLES WITH ONE ROW |

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

