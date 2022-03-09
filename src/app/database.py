import os
import json
from sqlite3 import DatabaseError
import psycopg

class BulkLoad:
    def __init__(self, table_name, cur, conn):
        # initialzing bulkload object
        self.__table_name = table_name
        self.__cur = cur
        self.__conn = conn
        pass

    def insert_image(self, name, path: str, encoding1: str, encoding2: str, metadata: str):
        '''
        to store images in bulk into database
        commit is made only when explicitly
        called on this object
        '''

        query = f'''
        insert into {self.__table_name} (name, path, encoding1, encoding2, metadata) 
        values ('{name}', '{path}', cube(array{encoding1}), cube(array{encoding2}), '{metadata}');
        '''

        try:
            self.__cur.execute(query)
        except:
            # rollback if query fails or an exception occurs
            self.__conn.rollback()
            raise DatabaseError(f'Insert Failed')

    def rollback(self):
        # to rollback changes
        self.__conn.rollback()

    def commit(self):
        # to commit changes made using insert_image method
        self.__conn.commit()
        self.__cur.close()

class Database:
    # root directory of the project
    root_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../..'))

    def __init__(self):
        pass

    def read_config(self):
        # read database credentials and name from configuration file
        # configuration file is read as json

        config_file = open(Database.root_dir + '/db.config')
        config = json.load(config_file)

        self.__user = config['user']
        self.__password = config['password']
        self.__db_name = config['db_name']

        # closing the configuration file
        config_file.close()

    def connect(self):
        '''
        make a connection with the database
        else raise exception
        '''
        try:
            self.__conn = psycopg.connect(
            f'dbname={self.__db_name} user={self.__user} password={self.__password}')
        except:
            raise DatabaseError(f'Could not connect to {self.__db_name}')

    def create_table(self, table_name: str):
        '''
        create table of specified name
        if an attempt to create another table
        is made, that table is made and switched
        to

        always use this methods inside try except block
        as exception will be raised if query fails

        so, this method can be used to both switch as well as
        create table
        '''

        self.__table_name = table_name
        cur = self.__conn.cursor()

        query = f'''
        create table {table_name} (
            id serial primary key, 
            name varchar(100), 
            path varchar(200),
            encoding1 cube, 
            encoding2 cube, 
            metadata varchar(2000),
            upload_time timestamp default current_timestamp);
        '''

        try:
            cur.execute(query)
            # commit on query success
            self.__conn.commit()
            cur.close()
        except:
            # rollback of query failure
            self.__conn.rollback()
            raise DatabaseError(
                f'Relation {table_name} could not be constructed')

    def insert_image(self, name, path: str, encoding1: str, encoding2: str, metadata: str):

        cur = self.__conn.cursor()

        query = f'''
        insert into {self.__table_name} (name, path, encoding1, encoding2, metadata) 
        values ('{name}', '{path}', cube(array{encoding1}), cube(array{encoding2}), '{metadata}');
        '''

        try:
            cur.execute(query)
            # commit on query success
            self.__conn.commit()
            cur.close()
        except:
            # rollback on query failure
            self.__conn.rollback()
            raise DatabaseError(f'Insert Failed')

    def bulk_insert(self):
        '''
        returns an object which can be used to
        load bulk data into the database
        '''
        cur = self.__conn.cursor()
        return BulkLoad(self.__table_name, cur, self.__conn)

    def identify(self, encoding1: str, encoding2: str, threshold: float, k: int):
        cur = self.__conn.cursor()

        query = f'''
        select dis, id, name from
        (select d1.id as id, d1.name as name, sqrt(d1.ed1*d1.ed1 + d2.ed2*d2.ed2) as dis
        from
        (select id, name, encoding1 <-> cube(array{encoding1}) as ed1 from {self.__table_name}) as d1,
        (select id, encoding2 <-> cube(array{encoding2}) as ed2 from {self.__table_name}) as d2
        where d1.id = d2.id) as d
        where dis<{threshold}
        order by dis desc limit {k};
        '''

        # initialize value to none
        val = None

        try:
            cur.execute(query)
            # on query success, fetch all relevant records
            val = cur.fetchall()
            # commit on query success
            self.__conn.commit()
            cur.close()
        except:
            # rollback on query failure
            self.__conn.rollback()
            raise DatabaseError(f'Identification Failed')
        
        return val

    def get_info(self, id: int):
        cur = self.__conn.cursor()

        query = f'''
        select name, path, metadata, upload_time
        from {self.__table_name}
        where id = {id}
        '''

        # initialize val to none
        val = None

        try:
            cur.execute(query)
            # fetch record on query success
            val = cur.fetchone()
            # commit on query success
            self.__conn.commit()
            cur.close()
        except:
            # rollback on query failure
            self.__conn.rollback()
            raise DatabaseError(f'Fetch Failed')

        return val

    def __del__(self):
        # close connection on object deletion
        self.__conn.close()