import pymysql.cursors
from discord.ext import commands


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def update_request(self, database: str, table: str, columns: tuple, new_values: tuple, elements: tuple,
                             data: tuple):
        connection = pymysql.connect(
            host=self.bot.config["Database"]["host"],
            user=self.bot.config["Database"]["user"],
            password=self.bot.config["Database"]["password"],
            db=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        args = ""
        for arg in elements:
            args += '`' + arg + '`=%s, '
        args = args[:-2]

        str_columns = ""
        for column in columns:
            str_columns += '`' + column + '`=%s, '
        str_columns = str_columns[:-2]

        result = True
        try:
            with connection.cursor() as cursor:
                sql = "UPDATE `{}` SET {} WHERE {};".format(table, str_columns, args)
                cursor.execute(sql, new_values + data)
            connection.commit()
        except Exception as e:
            result = str(e)

        connection.close()
        return result

    def insert_request(self, database: str, table: str, elements: tuple, data: tuple):
        connection = pymysql.connect(
            host=self.bot.config["Database"]["host"],
            user=self.bot.config["Database"]["user"],
            password=self.bot.config["Database"]["password"],
            db=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        args = ""
        for arg in elements:
            args += '`' + arg + '`, '
        args = args[:-2]

        result = True
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO `{}` ({}) VALUES ({});".format(table, args, (len(data) - 1) * "%s, " + "%s")
                cursor.execute(sql, data)
            connection.commit()
        except Exception as e:
            result = str(e)

        connection.close()
        return result

    def delete_request(self, database: str, table: str, elements: tuple, data: tuple):
        connection = pymysql.connect(
            host=self.bot.config["Database"]["host"],
            user=self.bot.config["Database"]["user"],
            password=self.bot.config["Database"]["password"],
            db=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        args = ""
        for arg in elements:
            args += '`' + arg + '`=%s, '
        args = args[:-2]

        result = True
        try:
            with connection.cursor() as cursor:
                sql = "DELETE FROM `{}` WHERE {};".format(table, args)
                cursor.execute(sql, data)
            connection.commit()
        except Exception as e:
            result = str(e)

        connection.close()
        return result

    def select_request(self, database: str, table: str, column: str, elements: tuple, data: tuple):
        connection = pymysql.connect(
            host=self.bot.config["Database"]["host"],
            user=self.bot.config["Database"]["user"],
            password=self.bot.config["Database"]["password"],
            db=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        args = ""
        for arg in elements:
            args += '`' + arg + '`=%s, '
        args = args[:-2]

        result = None
        try:
            with connection.cursor() as cursor:
                sql = "SELECT {} FROM `{}` WHERE {};".format(column, table, args) if args != "" else "" \
                                                                                                     "SELECT {} FROM `{}`".format(
                    column, table)
                cursor.execute(sql, data)
                result = cursor.fetchall()

                if len(result) == 1:
                    result = result[0]
                if len(result) == 0:
                    if type(result) == tuple or type(result) == list:
                        result = None

        except Exception as e:
            result = str(e)

        connection.close()
        return result


def setup(bot):
    bot.add_cog(Database(bot))
