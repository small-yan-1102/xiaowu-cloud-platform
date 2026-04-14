"""验证VT-033数据 - 输出到文件"""
import pymysql

pw = '}C7n%7Wklq6P'
conn = pymysql.connect(
    host='172.16.24.61', port=3306,
    user='xiaowu_db', password=pw,
    database='silverdawn_ams', charset='utf8mb4'
)
c = conn.cursor()

out = []

# 查看当前状态
c.execute("""
    SELECT code, takedown_reason, deadline_date
    FROM video_takedown_task
    WHERE status='PENDING_PROCESS'
    ORDER BY code
""")
rows = c.fetchall()
out.append("CURRENT PENDING_PROCESS:")
for r in rows:
    out.append(f"  {r[0]} reason={r[1]} deadline={r[2]}")

# 检查是否需要更新
need_update = False
for r in rows:
    if str(r[2]) != '2026-04-05':
        need_update = True
        break

if need_update:
    out.append("\nUpdating data for VT-033...")
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
        out.append(f"  {code}: rows_affected={c.rowcount}")
    conn.commit()
    out.append("Committed.")

    c.execute("""
        SELECT code, takedown_reason, deadline_date
        FROM video_takedown_task
        WHERE status='PENDING_PROCESS'
        ORDER BY code
    """)
    rows = c.fetchall()
    out.append("\nAFTER UPDATE:")
    for r in rows:
        out.append(f"  {r[0]} reason={r[1]} deadline={r[2]}")
else:
    out.append("\nData already set for VT-033, no update needed.")

conn.close()
out.append("DONE")

with open("vt033_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
