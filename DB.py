import ast
import os
import shutil

from SQLParser import Lexer, Parser
from UseTable import UseTable


def drop_database(path):
    try:
        shutil.rmtree(path)
    except:
        print("Database does not exist")


def drop_table(path, table):
    try:
        shutil.rmtree(path + table)
    except:
        print("Table does not exist")


def create_db(name):
    os.mkdir(name)
    os.chdir(name)
    if not os.path.exists(name + ".dc"):
        with open(name + ".dc", mode="w") as conf:
            config_string = name + "\n []"
            conf.write(config_string)
        with open(name + ".tb", mode="x"):
            pass


class DBobj(object):
    def __init__(self, name):
        os.chdir(name + "/")
        with open(name + ".dc", mode="r+") as conf:
            lines = conf.readlines()
            self.name = lines[0]
            self.tables = ast.literal_eval(lines[1])

    def create_table(self, name, configuration: dict):  # suzdava failovete za nova tablica
        if not os.path.exists(name):
            configuration_required_columns = {'id': ('int', 2), 'info': ('int', 2)}
            with open(name + ".tc", mode="w") as conf:
                config_string = str(configuration_required_columns.update(configuration)).replace('\n', '') + "\n"
                config_string += "0\n"
                config_string += "[]\n"
                conf.write(config_string)
            with open(name + ".tb", mode="x"):
                pass
        else:
            print("Table already exists")

    def execute_query(self, query):
        lex = Lexer(query)
        parser = Parser(lex)
        statement = parser.parse()
        if statement["type"].lower() == "select":
            table = UseTable(statement["table"], "/" + statement["table"])
            if not table.valid:
                return
            if statement["condition"]:
                indexes = table.select_where(statement["condition"][0], statement["condition"][1])
            else:
                indexes = "all"
            if not statement['columns']:
                print(table.get_display_names())
            else:
                print(statement['columns'])
            for row in table.generate_select(indexes, statement["columns"]):
                if row:
                    print(row)
            table.close_table()
        elif statement["type"].lower() == "insert":
            table = UseTable(statement["table"], "/" + statement["table"])
            if not table.valid:
                return
            table.insert(list(statement["row"]))
            table.close_table()
        elif statement["type"].lower() == "delete":
            table = UseTable(statement["table"], "/" + statement["table"])
            if not table.valid:
                return
            if statement["condition"]:
                indexes = table.select_where(*statement["condition"])
                for i in indexes:
                    table.delete_row(i)
            else:
                table.truncate_table()
            table.close_table()
        elif statement["type"].lower() == "update":
            table = UseTable(statement["table"], "/" + statement["table"])
            if not table.valid:
                return
            indexes = table.select_where(*statement["condition"])
            for i in indexes:
                table.update_row(i, statement["update_dict"])
            table.close_table()
        elif statement["type"].lower() == "create table":
            self.create_table(statement['table'], statement['config'])
        elif statement["type"].lower() == "create db":
            create_db(statement['db'])
        elif statement["type"].lower() == "drop db":
            drop_database("../" + statement['db'])
        elif statement["type"].lower() == "drop table":
            drop_table("./", statement["table"])
        elif statement["type"].lower() == "shrink":
            table = UseTable(statement["table"], "/" + statement["table"])
            if not table.valid:
                return
            table.shrink()
            table.close_table()


# opening the desired database
x = DBobj("DB1")
# queries
x.execute_query("SELECT * from table1;")

# x.execute_query("INSERT INTO table1 (column1, column2, column3) VALUES (5555,'tsdf',7.622);")

# x.execute_query("DELETE FROM table1;")

# x.execute_query("UPDATE table1 SET column1 = 3 WHERE id == 4;")
#
# x.execute_query("SHRINK table1;")
#
# x.execute_query("DROP database DB2;")
