"""查询表结构 + 数据状态"""
import pymysql

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

def q(cur, sql, label=''):
    if label:
        print(f'\n=== {label} ===')
    cur.execute(sql)
    rows = cur.fetchall()
    if cur.description:
        cols = [d[0] for d in cur.description]
        print('\t'.join(cols))
    for r in rows:
        print('\t'.join(str(v) if v is not None else 'NULL' for v in r))
    if not rows:
        print('(empty)')
    return rows

def main():
    conn = pymysql.connect(**DB, database='silverdawn_ams')
    c = conn.cursor()

    # 表结构
    q(c, "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH "
         "FROM information_schema.COLUMNS "
         "WHERE TABLE_SCHEMA='silverdawn_ams' AND TABLE_NAME='video_takedown_task' "
         "ORDER BY ORDINAL_POSITION", '表结构: video_takedown_task')

    # 任务单清单（用 * 先看所有字段）
    q(c, "SELECT * FROM video_takedown_task ORDER BY id DESC LIMIT 3",
      '任务单样例（前3条）')

    conn.close()
    print('\n=== Done ===')

if __name__ == '__main__':
    main()
