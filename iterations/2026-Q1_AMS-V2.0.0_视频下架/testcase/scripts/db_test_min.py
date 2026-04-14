"""最小化测试 - pymysql直连"""
import pymysql
try:
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
    print("OK:", cur.fetchone())
    conn.close()
except Exception as e:
    print("FAIL:", type(e).__name__, e)
