"""查表结构 + 补充查询"""
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
    if cur.description and rows:
        cols = [d[0] for d in cur.description]
        print('\t'.join(cols))
        for r in rows:
            vals = []
            for v in r:
                s = str(v) if v is not None else 'NULL'
                if len(s) > 80:
                    s = s[:77] + '...'
                vals.append(s)
            print('\t'.join(vals))
    elif not rows:
        print('(empty)')
    return rows

def main():
    conn = pymysql.connect(**DB, database='silverdawn_ams')
    c = conn.cursor()

    # video_takedown_task_detail 表结构
    q(c, "SELECT COLUMN_NAME, DATA_TYPE "
         "FROM information_schema.COLUMNS "
         "WHERE TABLE_SCHEMA='silverdawn_ams' AND TABLE_NAME='video_takedown_task_detail' "
         "ORDER BY ORDINAL_POSITION",
      'video_takedown_task_detail 结构')

    # video_takedown_task_composition 表结构
    q(c, "SELECT COLUMN_NAME, DATA_TYPE "
         "FROM information_schema.COLUMNS "
         "WHERE TABLE_SCHEMA='silverdawn_ams' AND TABLE_NAME='video_takedown_task_composition' "
         "ORDER BY ORDINAL_POSITION",
      'video_takedown_task_composition 结构')

    # composition_terminate 表结构
    q(c, "SELECT COLUMN_NAME, DATA_TYPE "
         "FROM information_schema.COLUMNS "
         "WHERE TABLE_SCHEMA='silverdawn_ams' AND TABLE_NAME='composition_terminate' "
         "ORDER BY ORDINAL_POSITION",
      'composition_terminate 结构')

    # 任务-作品关联
    q(c, "SELECT vt.code, vtc.composition_id, vtc.cp_name, vtc.video_count "
         "FROM video_takedown_task_composition vtc "
         "JOIN video_takedown_task vt ON vtc.task_id = vt.id "
         "ORDER BY vt.code",
      '任务-作品关联')

    # 解约单最近10条
    q(c, "SELECT * FROM composition_terminate ORDER BY id DESC LIMIT 5",
      '解约单样例')

    # BY_VIDEO_ID 那条 CREATING 的详细信息
    q(c, "SELECT * FROM video_takedown_task WHERE code='V2603310006'",
      'V2603310006 (CREATING BY_VIDEO_ID) 详情')

    # BY_VIDEO_ID CREATE_FAILED 的
    q(c, "SELECT code, create_fail_reason FROM video_takedown_task WHERE code='V2603300002'",
      'V2603300002 (CREATE_FAILED BY_VIDEO_ID) 失败原因')

    conn.close()

    # dispatcher 库
    conn2 = pymysql.connect(**DB, database='dispatcher')
    c2 = conn2.cursor()
    q(c2, "SELECT COLUMN_NAME, DATA_TYPE "
          "FROM information_schema.COLUMNS "
          "WHERE TABLE_SCHEMA='dispatcher' AND TABLE_NAME='video_takedown_queue' "
          "ORDER BY ORDINAL_POSITION",
      'video_takedown_queue 结构')
    q(c2, "SELECT COUNT(*) as total FROM video_takedown_queue", 'Dispatcher队列总数')
    conn2.close()

    print('\n=== Done ===')

if __name__ == '__main__':
    main()
