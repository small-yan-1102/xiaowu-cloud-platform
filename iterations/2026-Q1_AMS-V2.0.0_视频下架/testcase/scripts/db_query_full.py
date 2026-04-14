"""查询视频下架迭代的完整数据状态"""
import pymysql

DB_CONFIG = {
    'host': '172.16.24.61',
    'port': 3306,
    'user': 'xiaowu_db',
    'password': '}C7n%7Wklq6P',
    'charset': 'utf8mb4',
    'connect_timeout': 10,
}

def query(cur, sql, label=None):
    """执行查询并打印结果"""
    if label:
        print(f'\n=== {label} ===')
    cur.execute(sql)
    rows = cur.fetchall()
    desc = [d[0] for d in cur.description] if cur.description else []
    if rows:
        print('\t'.join(desc))
        for row in rows:
            print('\t'.join(str(v) if v is not None else 'NULL' for v in row))
    else:
        print('(empty)')
    return rows

def main():
    conn = pymysql.connect(**DB_CONFIG, database='silverdawn_ams')
    cur = conn.cursor()

    query(cur,
        "SELECT status, process_method, task_source, COUNT(*) as cnt "
        "FROM video_takedown_task "
        "GROUP BY status, process_method, task_source ORDER BY status",
        '1. 任务单状态分布')

    query(cur,
        "SELECT task_no, status, process_method, takedown_reason, "
        "task_source, video_count, IFNULL(team_id,'NULL') as tid, created_at "
        "FROM video_takedown_task ORDER BY created_at DESC LIMIT 25",
        '2. 任务单清单')

    query(cur,
        "SELECT status, COUNT(*) as cnt FROM video_takedown_task "
        "GROUP BY status ORDER BY cnt DESC",
        '3. 各状态数量')

    query(cur,
        "SELECT task_no, status, process_method, deadline_date, priority "
        "FROM video_takedown_task "
        "WHERE status IN ('PENDING_PROCESS','PROCESSING')",
        '4. 待处理/处理中')

    query(cur,
        "SELECT task_no, status, process_method, review_opinion "
        "FROM video_takedown_task WHERE status='REVIEW_REJECTED'",
        '5. 审核拒绝')

    query(cur,
        "SELECT task_no, status, process_method, takedown_reason, video_count "
        "FROM video_takedown_task WHERE status='PENDING_REVIEW'",
        '6. 待审核')

    query(cur,
        "SELECT task_no, team_id, team_name, process_method "
        "FROM video_takedown_task "
        "WHERE status='COMPLETED' AND team_id IS NOT NULL AND team_id!=''",
        '7. 已完成+有team_id')

    query(cur,
        "SELECT task_no, process_method, LEFT(fail_reason, 120) as reason "
        "FROM video_takedown_task WHERE status='CREATE_FAILED'",
        '8. 创建失败')

    query(cur,
        "SELECT COUNT(*) as total, "
        "SUM(CASE WHEN need_takedown=1 THEN 1 ELSE 0 END) as with_takedown, "
        "SUM(CASE WHEN need_takedown IS NULL OR need_takedown=0 THEN 1 ELSE 0 END) as no_takedown "
        "FROM composition_terminate",
        '9. 解约单统计')

    query(cur,
        "SELECT apc.composition_id, apc.sign_channel_name, apc.register_channel_id "
        "FROM ams_publish_channel apc "
        "WHERE apc.register_channel_id IN ('UClDJc5bJntyxdJoHB94GVgg','UCA17JOb1Bo5YQdggQwJN20Q') "
        "LIMIT 15",
        '10. 测试频道作品')

    query(cur,
        "SELECT vtd.status, COUNT(*) as cnt "
        "FROM video_takedown_task_detail vtd "
        "GROUP BY vtd.status ORDER BY cnt DESC",
        '11. 视频明细状态分布')

    conn.close()

    conn2 = pymysql.connect(**DB_CONFIG, database='dispatcher')
    cur2 = conn2.cursor()
    query(cur2, "SELECT COUNT(*) as total FROM video_takedown_queue", '12. Dispatcher队列')
    conn2.close()

    print('\n=== Done ===')

if __name__ == '__main__':
    main()
