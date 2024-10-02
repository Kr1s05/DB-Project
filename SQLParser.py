import re

SELECT, FROM, WHERE, DROP, DELETE, UPDATE, CREATE, SHRINK, SET, IDENTIFIER, NUMBER, COMMA, OPERATOR, LOGICAL, \
    DATABASE, TABLE, IN, LIST, EOF, STRING, LIKE, INSERT, VALUES, INTO = (
        "SELECT", "FROM", "WHERE", "DROP", "DELETE", "UPDATE", "CREATE", "SHRINK", "SET", "IDENTIFIER", "NUMBER",
        "COMMA", "OPERATOR", "LOGICAL", "DATABASE", "TABLE", "IN", "LIST", "EOF", "STRING", "LIKE", "INSERT", "VALUES",
        "INTO"
    )


class Token:
    def __init__(self, token_type, token_value):
        self.type = token_type
        self.value = token_value

    def __str__(self):
        return f"Token({self.type}, {self.value})"


class Lexer:
    def __init__(self, text):
        self.text = text
        self.position = 0
        self.current_char = self.text[self.position]
        self.lastIdentifier = None

    def error(self):
        raise Exception("Invalid character")

    def advance(self):
        self.position += 1
        if self.position > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.position]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
            if self.current_char == ".":
                result += self.current_char
                self.advance()
        return result

    def identifier(self):
        result = ""
        while self.current_char is not None:
            if not self.current_char.isalnum() and self.current_char != "_":
                break
            result += self.current_char
            self.advance()
        return result

    def operator(self):
        operators = (">", "<", "=", "!")
        result = ""
        while self.current_char in operators:
            result += self.current_char
            self.advance()
        return result

    def list(self):
        result = ""
        open_brackets = 1
        while self.current_char is not None:
            if self.current_char == " ":
                self.advance()
                if self.current_char == ",":
                    result += ","
                    self.advance()
                    if self.current_char == " ":
                        self.advance()
                        continue
                elif self.current_char == " ":
                    self.advance()
                    continue
                else:
                    result += " "
            result += self.current_char
            self.advance()
            if self.current_char == "(":
                open_brackets += 1
            if self.current_char == ")":
                open_brackets -= 1
            if open_brackets == 0:
                result += ")"
                self.advance()
                return result
        self.error()

    def string(self):
        result = "'"
        self.advance()
        while self.current_char.isalnum() or self.current_char == " ":
            result += self.current_char
            self.advance()
        if self.current_char == "'":
            result += "'"
            self.advance()
            return result
        self.error()

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(NUMBER, self.integer())

            if self.current_char == ",":
                self.advance()
                return Token(COMMA, ",")

            if self.current_char == ";":
                return Token(EOF, ";")

            if self.current_char in (">", "<", "=", "!"):
                return Token(OPERATOR, self.operator())

            if self.current_char == "(":
                return Token(LIST, self.list())

            if self.current_char == "'":
                return Token(STRING, self.string())

            if self.current_char == "*":
                self.advance()
                return self.get_next_token()

            if self.current_char.isalpha():
                identifier = self.identifier()
                if identifier.upper() == "SELECT":
                    return Token("SELECT", identifier)
                elif identifier.upper() == "FROM":
                    return Token("FROM", identifier)
                elif identifier.upper() == "WHERE":
                    return Token("WHERE", identifier)
                elif identifier.upper() == "DROP":
                    return Token("DROP", identifier)
                elif identifier.upper() == "DELETE":
                    return Token("DELETE", identifier)
                elif identifier.upper() == "UPDATE":
                    return Token("UPDATE", identifier)
                elif identifier.upper() == "CREATE":
                    return Token("CREATE", identifier)
                elif identifier.upper() == "SHRINK":
                    return Token(SHRINK, identifier)
                elif identifier.upper() == "IN":
                    return Token(OPERATOR, identifier)
                elif identifier.upper() in ("OR", "AND"):
                    return Token(LOGICAL, identifier)
                elif identifier.upper() == "DATABASE":
                    return Token(DATABASE, identifier)
                elif identifier.upper() == "TABLE":
                    return Token(TABLE, identifier)
                elif identifier.upper() == "LIKE":
                    return Token(OPERATOR, identifier)
                elif identifier.upper() == "SET":
                    return Token(SET, identifier)
                elif identifier.upper() == "INSERT":
                    return Token(INSERT, identifier)
                elif identifier.upper() == "INTO":
                    return Token(INTO, identifier)
                elif identifier.upper() == "VALUES":
                    return Token(VALUES, identifier)
                else:
                    self.lastIdentifier = IDENTIFIER
                    return Token(IDENTIFIER, identifier)

            print(self.current_char)
            self.error()


class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception("Invalid syntax")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def select_statement(self):
        self.eat(SELECT)
        columns = []
        while self.current_token.type == IDENTIFIER:
            columns.append(self.current_token.value)
            self.eat(IDENTIFIER)
            if self.current_token.type == COMMA:
                self.eat(COMMA)
        self.eat(FROM)
        table = self.current_token.value
        self.eat(IDENTIFIER)
        if self.current_token.type == WHERE:
            self.eat(WHERE)
            condition = self.condition()
        else:
            condition = None
        return {"type": "select", "columns": columns, "table": table, "condition": condition}

    def condition(self):
        result = ""
        columns = []
        while self.current_token.type == IDENTIFIER:
            columns.append(self.current_token.value)
            result += self.current_token.value + " "
            self.eat(IDENTIFIER)
            if self.current_token.type == OPERATOR:
                result += self.current_token.value + " "
                if self.current_token.value.upper() == "LIKE":
                    self.eat(OPERATOR)
                    result += self.current_token.value + " "
                    self.eat(STRING)
                elif self.current_token.value.upper() == "IN":
                    self.eat(OPERATOR)
                    result += self.current_token.value + " "
                    self.eat(LIST)
                else:
                    self.eat(OPERATOR)
                    result += self.current_token.value + " "
                    self.eat(NUMBER)
            if self.current_token.type == LOGICAL:
                result += self.current_token.value + " "
                self.eat(LOGICAL)
        return result, columns

    def create_statement(self):
        self.eat(CREATE)
        if self.current_token.type == TABLE:
            self.eat(TABLE)
            name = self.current_token.value
            self.eat(IDENTIFIER)
            list_c: str = self.current_token.value
            self.eat(LIST)
            list_c = list_c.replace("(", "").replace(")", "")
            entries = list_c.split(",")
            result = "{"
            for e in entries:
                entry = e.split(" ")
                result += "'" + entry[0] + "':"
                if entry[1] == "int":
                    result += "('int', 4),"
                elif entry[1] == "double":
                    result += "('float', 8),"
                else:
                    length = re.search("^varchar(\d+)$", entry[1])
                    if length:
                        length = length.group(1)
                    else:
                        self.error()
                    result += "('str'," + length + "),"
            result += "}"
            return {"type": "create table", "config": eval(result), "table": name}
        elif self.current_token.type == DATABASE:
            self.eat(DATABASE)
            name = self.current_token
            self.eat(IDENTIFIER)
            return {"type": "create db", "db": name}
        else:
            self.error()

    def drop_statement(self):
        self.eat(DROP)
        if self.current_token.type == TABLE:
            self.eat(TABLE)
            name = self.current_token.value
            self.eat(IDENTIFIER)
            return {"type": "drop table", "table": name}
        elif self.current_token.type == DATABASE:
            self.eat(DATABASE)
            name = self.current_token.value
            self.eat(IDENTIFIER)
            return {"type": "drop db", "db": name}
        self.error()

    def delete_statement(self):
        self.eat(DELETE)
        self.eat(FROM)
        name = self.current_token.value
        self.eat(IDENTIFIER)
        if self.current_token.type == WHERE:
            self.eat(WHERE)
            condition = self.condition()
        else:
            condition = None
        return {"type": "delete", "table": name, "condition": condition}

    def update_statement(self):
        self.eat(UPDATE)
        name = self.current_token.value
        self.eat(IDENTIFIER)
        self.eat(SET)
        result = "{"
        while self.current_token.type == IDENTIFIER:
            col = self.current_token.value
            self.eat(IDENTIFIER)
            if self.current_token.value != "=":
                self.error()
            self.eat(OPERATOR)
            value = self.current_token.value
            if self.current_token.type == NUMBER:
                self.eat(NUMBER)
            else:
                self.eat(STRING)
            result += "'" + col + "':" + value
            if self.current_token.type == COMMA:
                result += ","
                self.eat(COMMA)
        result += "}"
        self.eat(WHERE)
        condition = self.condition()
        return {"type": "update", "table": name, "update_dict": eval(result), "condition": condition}

    def shrink_statement(self):
        self.eat(SHRINK)
        name = self.current_token.value
        self.eat(IDENTIFIER)
        return {"type": "shrink", "table": name}

    def insert_statement(self):
        self.eat(INSERT)
        self.eat(INTO)
        name = self.current_token.value
        self.eat(IDENTIFIER)
        self.eat(LIST)
        self.eat(VALUES)
        row = eval(self.current_token.value)
        self.eat(LIST)
        return {"type": "insert", "table": name, "row": row}

    def parse(self):
        if self.current_token.type == SELECT:
            return self.select_statement()
        elif self.current_token.type == CREATE:
            return self.create_statement()
        elif self.current_token.type == DROP:
            return self.drop_statement()
        elif self.current_token.type == DELETE:
            return self.delete_statement()
        elif self.current_token.type == UPDATE:
            return self.update_statement()
        elif self.current_token.type == SHRINK:
            return self.shrink_statement()
        elif self.current_token.type == INSERT:
            return self.insert_statement()
        else:
            self.error()
