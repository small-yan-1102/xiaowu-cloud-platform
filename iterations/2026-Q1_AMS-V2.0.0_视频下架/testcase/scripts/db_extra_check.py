"""查找FAILED视频所在任务"""
import pymysql
conn = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db',
    password='}C7n%7Wklq6P', database='silverdawn_ams', charset='utf8mb4')
cursor = conn.cursor()

# 查找FAILED视频
cursor.execute("""
    SELECT t.code, t.status, d.video_id, d.video_status, d.status_detail
    FROM video_takedown_task_detail d
    JOIN video_takedown_task t ON t.id = d.task_id
    WHERE d.video_status = 'FAILED'
""")
for r in cursor.fetchall():
    print(f"FAILED video: task={r[0]}, task_status={r[1]}, video={r[2]}, detail={r[4]}")

# 检查审核拒绝状态任务(如有)
cursor.execute("SELECT code, status FROM video_takedown_task WHERE status IN ('AUDIT_REJECTED','REJECTED')")
for r in cursor.fetchall():
    print(f"Rejected: {r[0]}, status={r[1]}")

# 检查空Tab(哪些状态没有数据)
cursor.execute("SELECT status, COUNT(*) FROM video_takedown_task GROUP BY status")
print("\nStatus counts:")
for r in cursor.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
