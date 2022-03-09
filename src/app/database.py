import os
import json
from sqlite3 import DatabaseError
import psycopg

class BulkLoad:
    def __init__(self, table_name, cur, conn):
        self.__table_name = table_name
        self.__cur = cur
        self.__conn = conn
        pass

    def insert_image(self, name, path: str, encoding1: str, encoding2: str, metadata: str):

        query = f'''
        insert into {self.__table_name} (name, path, encoding1, encoding2, metadata) 
        values ('{name}', '{path}', cube(array{encoding1}), cube(array{encoding2}), '{metadata}');
        '''

        try:
            self.__cur.execute(query)
        except:
            self.__conn.rollback()
            raise DatabaseError(f'Insert Failed')

    def rollback(self):
        self.__conn.rollback()

    def commit(self):
        self.__conn.commit()
        self.__cur.close()

class Database:
    root_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../..'))

    def __init__(self):
        pass

    def read_config(self):
        config_file = open(Database.root_dir + '/db.config')
        config = json.load(config_file)

        self.__user = config['user']
        self.__password = config['password']
        self.__db_name = config['db_name']

        config_file.close()

    def connect(self):
        try:
            self.__conn = psycopg.connect(
            f'dbname={self.__db_name} user={self.__user} password={self.__password}')
        except:
            raise DatabaseError(f'Could not connect to {self.__db_name}')

    def create_table(self, table_name: str):
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
            self.__conn.commit()
            cur.close()
        except:
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
            self.__conn.commit()
            cur.close()
        except:
            self.__conn.rollback()
            raise DatabaseError(f'Insert Failed')

    def bulk_insert(self):
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

        val = None

        try:
            cur.execute(query)
            val = cur.fetchall()
            cur.close()
            self.__conn.commit()
        except:
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

        val = None

        try:
            cur.execute(query)
            val = cur.fetchone()
            self.__conn.commit()
            cur.close()
        except:
            self.__conn.rollback()
            raise DatabaseError(f'Fetch Failed')

        return val

    def __del__(self):
        self.__conn.close()