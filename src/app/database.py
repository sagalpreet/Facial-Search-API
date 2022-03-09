import os
import json
from sqlite3 import DatabaseError
import psycopg


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
        self.__conn = psycopg.connect(
            f'dbname={self.__db_name} user={self.__user} password={self.__password}')

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
        except:
            raise DatabaseError(
                f'Relation {table_name} could not be constructed')

    def insert_image(self, name, path: str, encoding1: str, encoding2: str, metadata: str, commit: bool = True):

        cur = self.__conn.cursor()

        query = f'''
        insert into {self.__table_name} (name, path, encoding1, encoding2, metadata) 
        values ('{name}', '{path}', cube(array{encoding1}), cube(array{encoding2}), '{metadata}');
        '''

        try:
            cur.execute(query)
            if (commit):
                self.__conn.commit()
        except:
            raise DatabaseError(f'Insert Failed')

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

        try:
            cur.execute(query)
        except:
            raise DatabaseError(f'Identification Failed')
        
        return cur.fetchall()

    def get_info(self, id: int):
        cur = self.__conn.cursor()

        query = f'''
        select name, path, metadata, upload_time
        from {self.__table_name}
        where id = {id}
        '''

        try:
            cur.execute(query)
        except:
            raise DatabaseError(f'Fetch Failed')

        return cur.fetchone()


    def commit(self):
        self.__conn.commit()

    def tear(self):
        self.__conn.close()