"""为 VT-034 准备数据：同截止日期 + 同下架原因 + 不同审批通过时间"""
import pymysql

pw = '}C7n%7Wklq6P'
conn = pymysql.connect(
    host='172.16.24.61', port=3306,
    user='xiaowu_db', password=pw,
    database='silverdawn_ams', charset='utf8mb4'
)
c = conn.cursor()

out = []

# VT-034: 2条PENDING_PROCESS，同截止日期、同下架原因、不同audit_time
# V2603300004: audit_time 早 → 排在前面
# V2603300003: audit_time 晚 → 排在后面
# V2603300006: 保持不同原因作为参照（或也改为同原因）
# 为简化，只用2条即可满足用例要求

updates = [
    ('V2603300004', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE', '2026-04-01 08:00:00'),  # 早
    ('V2603300003', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE', '2026-04-01 10:00:00'),  # 晚
    ('V2603300006', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE', '2026-04-01 12:00:00'),  # 最晚
]

for code, dl, reason, at in updates:
    c.execute(
        "UPDATE video_takedown_task SET deadline_date=%s, takedown_reason=%s, audit_time=%s "
        "WHERE code=%s AND status='PENDING_PROCESS'",
        (dl, reason, at, code)
    )
    out.append(f"  {code}: rows={c.rowcount}, deadline={dl}, reason={reason}, audit_time={at}")

conn.commit()
out.append("Committed.")

# 验证
c.execute("""
    SELECT code, takedown_reason, deadline_date, audit_time
    FROM video_takedown_task
    WHERE status='PENDING_PROCESS'
    ORDER BY audit_time
""")
out.append("\nAFTER UPDATE (ordered by audit_time):")
for r in c.fetchall():
    out.append(f"  {r[0]} reason={r[1]} deadline={r[2]} audit_time={r[3]}")

conn.close()
out.append("DONE")

import os
result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vt034_result.txt")
with open(result_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
