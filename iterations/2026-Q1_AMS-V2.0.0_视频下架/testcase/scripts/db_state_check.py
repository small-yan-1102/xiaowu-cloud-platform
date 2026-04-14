"""查询当前数据库状态，评估测试数据可用性"""
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

# 1. 任务单状态分布
print("=== 任务单状态分布 ===")
cursor.execute("""
    SELECT status, process_method, COUNT(*) as cnt 
    FROM video_takedown_task 
    GROUP BY status, process_method 
    ORDER BY status, process_method
""")
for r in cursor.fetchall():
    print(f"  {r[0]} / {r[1]}: {r[2]}")

# 2. 每条任务的作品数
print("\n=== 任务单作品数 ===")
cursor.execute("""
    SELECT t.code, t.status, t.process_method, 
           COUNT(DISTINCT c.id) as comp_count
    FROM video_takedown_task t
    LEFT JOIN video_takedown_task_composition c ON c.task_id = t.id
    GROUP BY t.code, t.status, t.process_method
    ORDER BY t.created_at DESC
""")
for r in cursor.fetchall():
    print(f"  {r[0]}: status={r[1]}, method={r[2]}, 作品数={r[3]}")

# 3. 有视频明细的任务单
print("\n=== 任务单视频明细数 ===")
cursor.execute("""
    SELECT t.code, t.status, COUNT(d.id) as detail_count
    FROM video_takedown_task t
    LEFT JOIN video_takedown_task_detail d ON d.task_id = t.id
    GROUP BY t.code, t.status
    ORDER BY t.created_at DESC
""")
for r in cursor.fetchall():
    print(f"  {r[0]}: status={r[1]}, 视频数={r[2]}")

# 4. 视频明细中各状态
print("\n=== 视频明细状态分布 ===")
cursor.execute("""
    SELECT d.video_status, COUNT(*) 
    FROM video_takedown_task_detail d
    GROUP BY d.video_status
""")
for r in cursor.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 5. 解约单数据
print("\n=== 解约单状态 ===")
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN need_takedown = 1 THEN 1 ELSE 0 END) as with_takedown,
           SUM(CASE WHEN need_takedown IS NULL OR need_takedown = 0 THEN 1 ELSE 0 END) as without_takedown
    FROM composition_terminate
""")
r = cursor.fetchone()
print(f"  总数={r[0]}, 含下架={r[1]}, 无下架={r[2]}")

# 6. 检查 PENDING_REVIEW 任务
print("\n=== PENDING_REVIEW 任务 ===")
cursor.execute("SELECT code, process_method, deadline_date FROM video_takedown_task WHERE status = 'PENDING_REVIEW'")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r[0]}: method={r[1]}, deadline={r[2]}")
if not rows:
    print("  无")

# 7. 检查 PENDING_PROCESS 任务
print("\n=== PENDING_PROCESS 任务 ===")
cursor.execute("SELECT code, process_method, deadline_date FROM video_takedown_task WHERE status = 'PENDING_PROCESS'")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r[0]}: method={r[1]}, deadline={r[2]}")
if not rows:
    print("  无")

# 8. 检查 PROCESSING 任务
print("\n=== PROCESSING 任务 ===")
cursor.execute("SELECT code, process_method FROM video_takedown_task WHERE status = 'PROCESSING'")
rows = cursor.fetchall()
for r in rows:
    print(f"  {r[0]}: method={r[1]}")
if not rows:
    print("  无")

# 9. 检查已完成任务中是否有失败视频
print("\n=== 已完成任务的视频状态 ===")
cursor.execute("""
    SELECT t.code, d.video_status, COUNT(d.id)
    FROM video_takedown_task t
    JOIN video_takedown_task_detail d ON d.task_id = t.id
    WHERE t.status = 'COMPLETED'
    GROUP BY t.code, d.video_status
""")
for r in cursor.fetchall():
    print(f"  {r[0]}: video_status={r[1]}, count={r[2]}")

# 10. CREATE_FAILED 任务及其作品数据
print("\n=== CREATE_FAILED 任务 ===")
cursor.execute("""
    SELECT t.code, t.process_method, t.takedown_reason,
           COUNT(DISTINCT c.id) as comp_count
    FROM video_takedown_task t
    LEFT JOIN video_takedown_task_composition c ON c.task_id = t.id
    WHERE t.status = 'CREATE_FAILED'
    GROUP BY t.code, t.process_method, t.takedown_reason
""")
for r in cursor.fetchall():
    print(f"  {r[0]}: method={r[1]}, reason={r[2]}, 作品数={r[3]}")

conn.close()
print("\n=== 完成 ===")
