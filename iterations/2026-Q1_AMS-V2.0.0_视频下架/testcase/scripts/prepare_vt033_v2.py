"""验证VT-033数据是否就绪 + 如未就绪则执行更新"""
import sys
import pymysql

pw = '}C7n%7Wklq6P'
conn = pymysql.connect(
    host='172.16.24.61', port=3306,
    user='xiaowu_db', password=pw,
    database='silverdawn_ams', charset='utf8mb4'
)
c = conn.cursor()

# 先查看当前状态
c.execute("""
    SELECT code, takedown_reason, deadline_date
    FROM video_takedown_task
    WHERE status='PENDING_PROCESS'
    ORDER BY code
""")
rows = c.fetchall()
sys.stderr.write("CURRENT PENDING_PROCESS:\n")
for r in rows:
    sys.stderr.write(f"  {r[0]} reason={r[1]} deadline={r[2]}\n")
sys.stderr.flush()

# 检查是否需要更新
need_update = False
for r in rows:
    if str(r[2]) != '2026-04-05':
        need_update = True
        break

if need_update:
    sys.stderr.write("\nUpdating data for VT-033...\n")
    updates = [
        ('V2603300004', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE'),
        ('V2603300006', '2026-04-05', 'ADJUST_LAUNCH_TIME'),
        ('V2603300003', '2026-04-05', 'DISTRIBUTOR_TERMINATION'),
    ]
    for code, dl, reason in updates:
        c.execute(
            "UPDATE video_takedown_task SET deadline_date=%s, takedown_reason=%s "
            "WHERE code=%s AND status='PENDING_PROCESS'",
            (dl, reason, code)
        )
        sys.stderr.write(f"  {code}: rows_affected={c.rowcount}\n")
    conn.commit()
    sys.stderr.write("Committed.\n")

    # 验证
    c.execute("""
        SELECT code, takedown_reason, deadline_date
        FROM video_takedown_task
        WHERE status='PENDING_PROCESS'
        ORDER BY code
    """)
    rows = c.fetchall()
    sys.stderr.write("\nAFTER UPDATE:\n")
    for r in rows:
        sys.stderr.write(f"  {r[0]} reason={r[1]} deadline={r[2]}\n")
else:
    sys.stderr.write("\nData already set for VT-033, no update needed.\n")

sys.stderr.flush()
conn.close()
sys.stderr.write("DONE\n")
sys.stderr.flush()
