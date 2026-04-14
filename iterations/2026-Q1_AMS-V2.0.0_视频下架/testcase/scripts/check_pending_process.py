"""查看 PENDING_PROCESS 任务详细字段"""
import pymysql

conn = pymysql.connect(
    host='172.16.24.61', port=3306,
    user='xiaowu_db', password='}C7n%7Wklq6P',
    database='silverdawn_ams', charset='utf8mb4', connect_timeout=10
)
c = conn.cursor(pymysql.cursors.DictCursor)

# 查看 task 表完整列名
c.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS "
          "WHERE TABLE_SCHEMA='silverdawn_ams' AND TABLE_NAME='video_takedown_task' "
          "ORDER BY ORDINAL_POSITION")
cols = [r['COLUMN_NAME'] for r in c.fetchall()]
print('task columns:', cols)

# 查看 PENDING_PROCESS 任务的全部字段
c.execute("SELECT * FROM video_takedown_task WHERE status='PENDING_PROCESS' ORDER BY code")
for t in c.fetchall():
    print()
    for k, v in t.items():
        if v is not None:
            print(f'  {k}: {v}')

# 查看 composition 表关联
c.execute(
    "SELECT tc.task_id, tc.composition_id, tc.composition_name, tc.video_count, "
    "tc.completed_count, tc.failed_count "
    "FROM video_takedown_task_composition tc "
    "JOIN video_takedown_task t ON tc.task_id = t.id "
    "WHERE t.status = 'PENDING_PROCESS'"
)
comps = c.fetchall()
print(f'\nPENDING_PROCESS compositions: {len(comps)}')
for comp in comps:
    print(f"  task_id={comp['task_id']}, comp={comp['composition_name']}, "
          f"videos={comp['video_count']}")

conn.close()
