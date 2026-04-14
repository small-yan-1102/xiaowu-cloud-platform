"""最小化测试 - 数据库直连"""
import sys
sys.path.insert(0, r'E:\Orange\python-new\lib\site-packages')

# 方法1: pymysql 直连
try:
    import pymysql
    conn = pymysql.connect(
        host='172.16.24.61',
        port=3306,
        user='xiaowu_db',
        password='}C7n%7Wklq6P',
        database='silverdawn_ams',
        charset='utf8mb4',
        connect_timeout=10
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print(f"pymysql OK: {cur.fetchone()}")
    conn.close()
except Exception as e:
    print(f"pymysql FAIL: {e}")

# 方法2: mysql-connector-python 直连
try:
    import mysql.connector
    conn2 = mysql.connector.connect(
        host='172.16.24.61',
        port=3306,
        user='xiaowu_db',
        password='}C7n%7Wklq6P',
        database='silverdawn_ams',
        charset='utf8mb4',
        connection_timeout=10,
        auth_plugin='mysql_native_password'
    )
    cur2 = conn2.cursor()
    cur2.execute("SELECT 1")
    print(f"mysql-connector OK: {cur2.fetchone()}")
    conn2.close()
except Exception as e:
    print(f"mysql-connector FAIL: {e}")

# 方法3: mysql-connector 不指定 auth_plugin
try:
    import mysql.connector
    conn3 = mysql.connector.connect(
        host='172.16.24.61',
        port=3306,
        user='xiaowu_db',
        password='}C7n%7Wklq6P',
        database='silverdawn_ams',
        connection_timeout=10
    )
    cur3 = conn3.cursor()
    cur3.execute("SELECT 1")
    print(f"mysql-connector (auto) OK: {cur3.fetchone()}")
    conn3.close()
except Exception as e:
    print(f"mysql-connector (auto) FAIL: {e}")
