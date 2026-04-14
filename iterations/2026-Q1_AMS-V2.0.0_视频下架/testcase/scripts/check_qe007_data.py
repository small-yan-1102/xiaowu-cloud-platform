"""检查QE-007所需的待审核数据是否仍存在"""
import pymysql

conn = pymysql.connect(
    host='172.16.24.61',
    port=3306,
    user='xiaowu_db',
    password='}C7n%7Wklq6P',
    database='silverdawn_ams',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 检查待审核的视频私享任务
cursor.execute("""
    SELECT id, code, status, process_method, takedown_reason 
    FROM video_takedown_task 
    WHERE status = 'PENDING_REVIEW'
""")
rows = cursor.fetchall()
print('=== 当前待审核任务单 ===')
if rows:
    for r in rows:
        print(f'  ID={r[0]}, code={r[1]}, status={r[2]}, method={r[3]}, reason={r[4]}')
else:
    print('  无待审核任务单！')

# 也检查V2604010001的当前状态
cursor.execute("""
    SELECT id, code, status, process_method 
    FROM video_takedown_task 
    WHERE code = 'V2604010001'
""")
r = cursor.fetchone()
if r:
    print(f'\nV2604010001 当前状态: ID={r[0]}, status={r[2]}, method={r[3]}')
else:
    print('\nV2604010001 不存在!')

conn.close()
