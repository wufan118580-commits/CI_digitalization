"""数据库连接工具"""
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from config import DB_CONFIG


def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG, cursorclass=DictCursor)


@contextmanager
def get_db():
    """数据库上下文管理器"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def execute_query(sql: str, params: tuple = None, fetch_one: bool = False):
    """执行查询"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()


def execute_write(sql: str, params: tuple = None):
    """执行写操作"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
