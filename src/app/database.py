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
        create table faces (
            id serial primary key, 
            name varchar(100), 
            encoding1 cube, 
            encoding2 cube, 
            metadata varchar(2000));
        '''

        try:
            cur.execute(query)
            self.__conn.commit()
        except:
            raise DatabaseError(
                f'Relation {table_name} could not be constructed')

    def insert_image(self, name, encoding1: str, encoding2: str, metadata: str, commit: bool = True):

        cur = self.__conn.cursor()

        query = f'''
        insert into {self.__table_name} (name, encoding1, encoding2, metadata) 
        values ('{name}', cube(array{encoding1}), cube(array{encoding2}), '{metadata}');
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
        select * from
        (select d1.id, d1.name, sqrt(d1.ed1*d1.ed1 + d2.ed2*d2.ed2) as dis, d1.metadata
        from
        (select id, name, encoding1 <-> cube(array{encoding1}) as ed1, metadata from {self.__table_name}) as d1,
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

    def commit(self):
        self.__conn.commit()
