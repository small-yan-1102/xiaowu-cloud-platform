"""QE-007 数据准备脚本: 将 V2604010001 重置为 PENDING_REVIEW 状态"""
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

task_id = 2039170925521399809  # V2604010001

# Step 1: 重置前 - 确认当前状态
print("=== 重置前状态 ===")
cursor.execute("SELECT code, status, process_method, deadline_date, auditor_id, audit_opinion, audit_time FROM video_takedown_task WHERE id = %s", (task_id,))
row = cursor.fetchone()
print(f"  code={row[0]}, status={row[1]}, method={row[2]}, deadline={row[3]}")
print(f"  auditor={row[4]}, opinion={row[5]}, audit_time={row[6]}")

# Step 2: 重置主表 - status→PENDING_REVIEW, 清除审核字段, 延长截止日期
cursor.execute("""
    UPDATE video_takedown_task 
    SET status = 'PENDING_REVIEW',
        auditor_id = NULL,
        audit_opinion = NULL,
        audit_time = NULL,
        deadline_date = '2026-04-07'
    WHERE id = %s
""", (task_id,))
print(f"\n主表已更新: {cursor.rowcount} 行")

# Step 3: 重置明细表 - video_status→PENDING, 清除执行时间
cursor.execute("""
    UPDATE video_takedown_task_detail
    SET video_status = 'PENDING',
        execute_time = NULL,
        complete_time = NULL
    WHERE task_id = %s
""", (task_id,))
print(f"明细表已更新: {cursor.rowcount} 行")

conn.commit()

# Step 4: 验证重置结果
print("\n=== 重置后状态 ===")
cursor.execute("SELECT code, status, process_method, deadline_date, auditor_id, audit_opinion, audit_time FROM video_takedown_task WHERE id = %s", (task_id,))
row = cursor.fetchone()
print(f"  code={row[0]}, status={row[1]}, method={row[2]}, deadline={row[3]}")
print(f"  auditor={row[4]}, opinion={row[5]}, audit_time={row[6]}")

cursor.execute("SELECT video_id, video_status, execute_time, complete_time FROM video_takedown_task_detail WHERE task_id = %s", (task_id,))
for r in cursor.fetchall():
    print(f"  video={r[0]}, status={r[1]}, exec_time={r[2]}, complete_time={r[3]}")

# Step 5: 确认待审核列表中可见
print("\n=== 当前所有 PENDING_REVIEW 记录 ===")
cursor.execute("SELECT code, process_method, deadline_date FROM video_takedown_task WHERE status = 'PENDING_REVIEW'")
for r in cursor.fetchall():
    print(f"  code={r[0]}, method={r[1]}, deadline={r[2]}")

conn.close()
print("\n=== 数据重置完成 ===")
