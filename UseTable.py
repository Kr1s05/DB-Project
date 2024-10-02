import re
import os.path
import struct
from ast import literal_eval

infoExtension = ".td"
configExtension = ".tc"
tableExtension = ".tab"


class TableConfig:
    def __init__(self, name):
        self.name = name
        self.tableName = name + tableExtension
        self.configFile = name + configExtension
        self.infoFile = name + infoExtension
        with open(self.configFile, mode='r', encoding='UTF-8') as conf:
            config_lines = conf.readlines()
        self.configuration: dict = literal_eval(config_lines[0])
        self.row_count = int(config_lines[1])
        self.deleted_rows = int(config_lines[2])
        self.row_length = sum(list(self.configuration.values())[i][1] for i in range(0, len(self.configuration)))

    def write_config(self):
        config_string = str(self.configuration).replace('\n', '') + "\n"
        config_string += str(self.row_count) + "\n"
        config_string += str(self.deleted_rows).replace('\n', '') + "\n"
        os.remove(self.configFile)
        with open(self.configFile, mode="w", encoding="UTF-8") as conf:
            conf.write(config_string)


class UseTable:
    table = None  # otvoreniq fail na tablicata
    binFormat = ">"  # nachaloto na format string za struct
    opened = False

    def __init__(self, table_name, path):
        try:
            os.chdir(os.getcwd() + path)
        except FileNotFoundError:
            print("Table does not exist")
            self.valid = False
            return
        self.configObject = TableConfig(table_name)  # zarejda konfiguraciqta na tablicata
        self.generate_format()  # generira formata za struct
        self.open_table()  # otvarq tablicata
        self.valid = True

    def generate_format(self):  # preminava prez configuraciqta i generira pravilniq format
        for i, value in enumerate(self.configObject.configuration.values()):
            value_type = value[0][0:1]
            if value_type == 's':
                self.binFormat += str(value[1]) + value_type
            elif value_type == 'i':
                if i in (0, 1):  # id i info kolonite sa tip unsigned short
                    self.binFormat += "1H"
                else:
                    self.binFormat += "1l"
            elif value_type == 'f':
                self.binFormat += "1d"

    def open_table(self):  # otvarq tablicata
        self.table = open(self.configObject.tableName, mode="rb+")
        self.opened = True

    def close_table(self):  # zatvarq tablicata i zapisva konfig faila
        self.table.close()
        self.opened = False
        self.configObject.write_config()
        os.chdir("../")

    def row_to_bin(self, data):  # prevrushta danni v bin
        return struct.pack(self.binFormat, *data)

    def row_to_data(self, bin_data):  # prevrushta bin danni v list
        return struct.unpack(self.binFormat, bin_data)

    def verify_row_data(self, data: list):  # proverqva dali dannite sa podhodqshti za tablicata
        if not len(data) == len(self.configObject.configuration):  # proverqva broq na poletata
            return False
        for count, value in enumerate(data):  # proverqva vsqko pole po tip i razmer
            cell_type = list(self.configObject.configuration.values())[count][0]
            cell_size = list(self.configObject.configuration.values())[count][1]
            if not str(type(value)).__contains__(cell_type):
                return False
            if cell_type == "str":
                if len(value) > cell_size:
                    return False
                data[count] = bytes(data[count], encoding="ascii")  # prevrushta str v bytes
            else:
                if value > 2147483648 or value < -2147483648:
                    return False
        return True

    def insert(self, data: list):  # suzdava nov red po dadeni danni i go postavq nakraq na tablicata
        data = [1, self.configObject.row_count] + data
        if not self.verify_row_data(data):
            print("invalid data")
            return
        if not self.opened:
            self.open_table()
        self.write_row(data)
        self.configObject.row_count += 1  # zapisva che redovete sa 1 poveche

    def select_where(self, conditions: str = None, columns: list = None):
        if not conditions:
            return "all"
        ids = None
        id_condition = re.search('id (>|<|>=|<=|!=|==|in) (\(*\d+(?:,*\d*)*\)*)', conditions)
        if not self.verify_columns(columns):
            print("Invalid condition columns")
            return
        if id_condition:
            operation = id_condition.group(1)
            operand = id_condition.group(2)
            if operation == "<":
                ids = range(0, int(operand) - 1)
            elif operation == ">":
                ids = range(int(operand), self.configObject.row_count)
            elif operation == "<=":
                ids = range(0, int(operand))
            elif operation == ">=":
                ids = range(int(operand), self.configObject.row_count)
            elif operation == "==":
                ids = int(operand)
            elif operation == "in":
                ids = eval(operand)
            elif operation == "!=":
                ids = operand
        if ids is None:
            ids = range(0, self.configObject.row_count)
        cols = ""
        for col in list(self.configObject.configuration.keys()):
            if col != "info" and col != "id":
                cols = cols + "," + str(col)
        lamb_text = "lambda id" + cols + " : " + conditions
        condition_lambda = eval(lamb_text)
        indexes = []
        if isinstance(ids, range) or isinstance(ids, tuple):
            for i in ids:
                row = self.read_row(i)
                if row and condition_lambda(*row):
                    indexes.append(i)
        elif isinstance(ids, int):
            row = self.read_row(ids)
            if row and condition_lambda(*row):
                indexes.append(ids)
        elif isinstance(ids, str):
            for i in range(0, self.configObject.row_count - 1):
                if i == int(ids):
                    continue
                row = self.read_row(i)
                if row and condition_lambda(*row):
                    indexes.append(i)
        return indexes

    def write_row(self, row, index=None):
        if not index:  # ako nqma zadaden index pishe nakraq na tablicata
            index = self.configObject.row_count
        self.table.seek(index * self.configObject.row_length)
        self.table.write(self.row_to_bin(row))

    def read_row(self, index):
        if index >= self.configObject.row_count:  # proverqva dali indexa go ima v tablicata
            return
        self.table.seek(index * self.configObject.row_length)
        row = list(self.row_to_data(self.table.read(self.configObject.row_length)))  # chete reda
        for i, value in enumerate(list(self.configObject.configuration.values())):  # prevrushta bytes v str
            if value[0] == 'str':
                row[i] = row[i].decode("ascii")
                row[i] = row[i].replace("\x00", "")
        if row[0] == 2:  # proverqva dali reda e markiran kato iztrit
            return
        # del row[1]
        del row[0]  # maha info kolonata
        return row

    def truncate_table(self):  # iztriva vsichko ot tablicata no zapazva strukturata i
        self.table.truncate(0)
        self.configObject.row_count = 0

    def delete_row(self, index):  # markira red kato iztrit
        self.table.seek((index * self.configObject.row_length))
        self.table.write(struct.pack(">1H", 2))
        self.configObject.deleted_rows += 1  # ako triem ot sredata markirame reda za iztrit

    def verify_columns(self, columns):  # proverqva dali kolonite sushtestvuvat v tablicata
        config = list(self.configObject.configuration.keys())
        del config[0]
        if isinstance(columns, list):
            for column in columns:
                if column not in config:
                    return False
        else:
            if columns not in config:
                return False
        return True

    def get_display_names(self):
        result = list(self.configObject.configuration.keys())
        del result[0]
        return result

    def generate_select(self, indexes, columns=None):
        if columns and not self.verify_columns(columns):
            print("invalid columns")
            return

        def trim_row(row):  # funkciq koqto trie kolonite koito ne sa ukazani
            if not row:
                return
            table_columns = self.get_display_names()
            row = dict(zip(table_columns, row))
            if not columns:
                return row
            result = dict.fromkeys(columns)
            for key in list(result.keys()):
                result[key] = row[key]
            return result

        if not indexes:
            print("invalid statement")
            return
        if indexes == "all":  # preminava prez tablicata/indexite i gi vrushta s yield
            indexes = range(0, self.configObject.row_count)
        for i in indexes:
            result = trim_row(self.read_row(i))
            if result:
                yield list(result.values())
            else:
                continue

    def update_row(self, index, update: dict):  # funkciq za promqna na red
        if not self.verify_columns(list(update.keys())):
            print("Invalid update columns")
            return
        if index >= self.configObject.row_count:
            return
        original_row = self.read_row(index)  # izvajda stariq red
        original_row.insert(0, 1)
        for key in list(update.keys()):
            original_row[list(self.configObject.configuration.keys()).index(key)] = update[key]  # promenq reda
        if self.verify_row_data(original_row):
            self.write_row(original_row, index)  # pishe reda v tablicata

    def shrink(self):
        with open(self.configObject.name + ".new", mode="wb+") as newTable:
            i = 0
            for row in self.generate_select("all"):
                if row:
                    del row[0]
                    row = [1, i] + row
                    self.verify_row_data(row)
                    newTable.seek(i * self.configObject.row_length)
                    newTable.write(self.row_to_bin(row))
                    i += 1
            self.configObject.row_count = i
            self.configObject.deleted_rows = 0
            self.close_table()
            os.chdir(self.configObject.name + "/")
            os.rename(self.configObject.tableName, self.configObject.name + ".old")
            os.rename(self.configObject.name + ".new", self.configObject.tableName)
            self.open_table()
