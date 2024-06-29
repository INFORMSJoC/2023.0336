from mysql.connector import connect
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import pandas

class MySqlDatabaseException(Exception):
    pass

class MySqlDatabase(object):
    
    def __init__(self, user, user_password, root_password, database_name, host, port):
        """MySqlDatabase constructor __init__

        Arguments:
        user                    username for database
        user_password           user password
        root_password           password for MYSQL server root
        database_name           name of database schema
        host                    MYSQL server host address
        port                    MYSQL server port
        """
        self.user = user
        self.user_password = user_password
        self.root_password = root_password
        self.database_name = database_name
        self.host = host
        self.port = port

    def _get_connect(self, root=False):
        """Connect to MYSQL server as root or to database as user, per input root flag"""
        try:
            if root:
                connection = connect(
                    host=self.host,
                    port=self.port,
                    user="root",
                    password=self.root_password,
                )
            else:
                connection = connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.user_password,
                    database=self.database_name
                )
        except Exception as error:
            raise MySqlDatabaseException("MYSQL connection failed:\n"+str(error)+"\n")
        return connection

    def _get_connect_sql_alchemy(self):
        """Connect to MYSQL server using SQLAlchemy for Pandas to_sql method"""
        try:
            engine = create_engine("mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}".format(
                quote_plus(self.user),
                quote_plus(self.user_password),
                self.host,
                self.port,
                self.database_name,
            ))
            connection = engine.connect()
        except Exception as error:
            raise MySqlDatabaseException("SQLAlchemy connection failed:\n"+str(error)+"\n")
        return connection

    def _execute_sql(self, sql:str, root=False):
        """Execute single SQL command as user or root, per input root flag"""
        try:
            with self._get_connect(root=root) as connection:
                connection.cursor().execute(sql)
                connection.commit()
        except Exception as error:
            raise MySqlDatabaseException("Execute SQL failed:\n"+str(error)+"\n")

    def _execute_sql_commands(self, sql_text, root=False):
        """Execute all commands in sql_text as user or root, per input root flag"""
        # split on all semicolons unless part of filetype definition
        commands = sql_text.split(";")
        for command in commands:
            try:
                if command.strip() != "":
                    self._execute_sql(command, root=root)
            except Exception as error:
                raise MySqlDatabaseException("Command skipped:\n"+str(error)+"\n")

    def execute_sql_file(self, filename, root=False):
        """Execute all commands in .sql file as user or root, per input root flag"""
        try:
            with open(filename, "r") as fid:
                sql_text = fid.read()
        except Exception as error:
            raise IOError("Failed in execute_sql_file to read file "+filename+"\n"+str(error)+"\n")
        return self._execute_sql_commands(sql_text, root=root)  

    def drop_create_user_database(self):
        """Create database and user, assign user privileges"""
        sql_text = "DROP USER IF EXISTS "+self.user+"@'%';" \
                    + "FLUSH PRIVILEGES;" \
                    + "CREATE USER '"+self.user+"'@'%' IDENTIFIED BY '"+self.user_password+"';" \
                    + "DROP SCHEMA IF EXISTS `"+self.database_name+"`;" \
                    + "CREATE SCHEMA IF NOT EXISTS `"+self.database_name+"`" \
                    + "DEFAULT CHARACTER SET UTF8MB4 COLLATE utf8mb4_unicode_ci;" \
                    + "USE "+self.database_name+";" \
                    + "GRANT ALL ON "+self.database_name+".* TO "+self.user+"@'%';"
        return self._execute_sql_commands(sql_text, root=True)

    def make_data(self, filenames, drop_create_db=False):
        """Drop / create user and database
        Execute all commands in list of .sql files as user or root, per input root flag"""
        if drop_create_db:
            try:
                self.drop_create_user_database()
            except Exception as error:
                raise MySqlDatabaseException("Drop/create MYSQL user and database failed:\n"+str(error))
        for filename in filenames:
            try:
                self.execute_sql_file(filename, root=False)
            except Exception as error:
                raise MySqlDatabaseException("Execute "+filename+" file failed:\n"+str(error))

    def query(self, select, values=None, output_format="default", root=False):
        """Execute SQL select query (as root optionally)
        Results are returned in the format specified output_format specified
            default - returns a list of row values returned by query
            dict - returns a python dictionary
            list - returns results in a list of the first item in each row.
            item - returns only the first item retrieved in a tuple format"""
        result = None
        dict_flag = output_format.lower() == "dict"
        try:            
            with self._get_connect(root=root) as connection:
                with connection.cursor(dictionary=dict_flag) as cursor:
                    cursor.execute(select, values)
                    result = cursor.fetchall()
                if output_format.lower() == "list":
                    result = [x[0] for x in result]                        
                elif output_format.lower() == "item":
                    if len(result)==0:
                        return None
                    else:
                        return result[0]
        except Exception as error:
            raise MySqlDatabaseException("Query failed:\n"+str(error)+"\n")
        return result

    def _insert_insert_update(self, table_name:str, data_dict:dict, update:bool):
        """Insert or update row(s) in database table, per input flag update
        data_dict keys are field names in table
        data_dict values are either lists of values or a single value,
        allowing for inserting or updating multiple rows or a single row"""
        if table_name is None or table_name=="":
            raise MySqlDatabaseException("table_name cannot be empty\n")
        data_dict = {k:v if isinstance(v, list) else [v] for (k, v) in data_dict.items()}
        fields = list(data_dict.keys())
        if len(fields) == 0: return
        num_records = len(data_dict[fields[0]])
        for field in fields:
            if len(data_dict[field]) != num_records:
                raise ValueError("All fields in dict should have same length list: ", data_dict)
        sql = "INSERT INTO {0} ({1}) VALUES({2})".format(
            table_name, ",".join(fields),  ",".join(["%s"]*len(fields))
        )
        if update:
            sql += " ON DUPLICATE KEY UPDATE "+",".join([field+"=%s" for field in fields])
        lastrowid = 0
        with self._get_connect() as connection:
            for i in range(0, num_records):
                values = [data_dict[field][i] for field in fields]
                if update: values += values
                lastrowid = 0
                try:
                    cursor = connection.cursor()
                    cursor.execute(sql, values)
                    lastrowid = cursor.lastrowid
                except Exception as error:
                    raise MySqlDatabaseException("Insert / update failed:\n"+str(error)+"\n")
            connection.commit()
        return lastrowid

    def insert_update(self, table_name:str, data_dict:dict):
        """Update row(s) in database table, per input flag update
        data_dict keys are field names in table
        data_dict values are either lists of values or a single value,
        allowing for inserting or updating multiple rows or a single row"""
        return self._insert_insert_update(table_name, data_dict, update=True)

    def insert(self, table_name:str, data_dict:dict):
        """Insert row(s) in database table, per input flag update
        data_dict keys are field names in table
        data_dict values are either lists of values or a single value,
        allowing for inserting or updating multiple rows or a single row"""
        return self._insert_insert_update(table_name, data_dict, update=False)

    def update(self, table_name, data_dict, where_dict):
        """Update row(s) in database table
        data_dict keys are field names in table
        data_dict[key]=value being updated to new value
        where_dict keys are field names in the table
        where_dict[key]=value of the field in the where condition"""
        set_fields = list(data_dict.keys())
        where_fields = list(where_dict.keys())
        sql = """UPDATE {0}
                SET {1}
                WHERE {2}""".format(
            table_name, 
            ",".join([field+"=%s" for field in set_fields]),
            " AND ".join([field+"=%s" for field in where_fields])
        )
        values = [data_dict[field] for field in set_fields]
        values += [where_dict[field] for field in where_fields]
        with self._get_connect() as connection:
            try:
                cursor = connection.cursor()
                cursor.execute(sql, values)
            except Exception as error:
                raise MySqlDatabaseException("Update failed:\n"+str(error)+"\n")
            connection.commit()

    def delete(self, table_name, where_dict):
        """Delete rows from table specified with conditions specified,
        where_dict keys are field names in the table
        where_dict[key]=value of the field in the where condition"""
        sql = "DELETE FROM "+table_name+" WHERE " \
                + " AND ".join([field+"=%s" for field in where_dict])
        success = False
        with self._get_connect() as connection:
            try:                
                cursor = connection.cursor()
                cursor.execute(sql, list(where_dict.values()))                
                success = cursor.lastrowid == 0
                connection.commit()                
            except Exception as error:
                raise MySqlDatabaseException("delete_from_table error:\n"+str(error)+"\n")            
        return success

    def exists(self):
        """Returns boolean indicating if database exists"""
        try:
            database_exists = self.query(
                """SELECT SCHEMA_NAME
                    FROM INFORMATION_SCHEMA.SCHEMATA
                    WHERE SCHEMA_NAME = %s""",
                values = [self.database_name], output_format="item", root=True,
            ) is not None
        except Exception as error:
            raise MySqlDatabaseException("exists() method failed\n"+str(error))
        return database_exists

    def num_tables(self):
        """Returns integer number of tables in database"""
        try:
            num = self.query(
                """SELECT COUNT(*)
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = %s""",
                values = [self.database_name], output_format="item", root=True,
            )[0]
        except Exception as error:
            raise MySqlDatabaseException("num_tables() method failed\n"+str(error))
        return num

    def add_dataframe(self, dataframe, table_name):
        """Execute SQL insert using Pandas"""
        try:            
            with self._get_connect_sql_alchemy() as connection:
                dataframe.to_sql(
                    table_name, connection, schema=None, if_exists='append', 
                    index=False, chunksize=10000, dtype=None, method='multi')
        except Exception as error:
            raise MySqlDatabaseException("Pandas to_sql failed:\n"+str(error)+"\n")

    def read_dataframe(self, query):
        """Execute SQL read using Pandas"""
        try:            
            with self._get_connect_sql_alchemy() as connection:
                data = pandas.read_sql(query, connection)
        except Exception as error:
            raise MySqlDatabaseException("Pandas read_sql failed:\n"+str(error)+"\n")
        return data
