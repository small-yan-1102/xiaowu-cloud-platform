"""为 VT-033 准备数据：同截止日期 + 不同下架原因（优先级）"""
import pymysql

conn = pymysql.connect(
    host='172.16.24.61', port=3306,
    user='xiaowu_db', password='}C7n%7Wklq6P',
    database='silverdawn_ams', charset='utf8mb4'
)
c = conn.cursor()

# VT-033 要求：3条PENDING_PROCESS，截止日期相同，下架原因不同
# 优先级：TEMP_COPYRIGHT_DISPUTE(1) > ADJUST_LAUNCH_TIME(2) > DISTRIBUTOR_TERMINATION(5)
# 预期排序：V2603300004(优先级1) → V2603300006(优先级2) → V2603300003(优先级5)
updates = [
    ('V2603300004', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE'),       # 临时版权纠纷 priority 1
    ('V2603300006', '2026-04-05', 'ADJUST_LAUNCH_TIME'),           # 调整上线时间 priority 2
    ('V2603300003', '2026-04-05', 'DISTRIBUTOR_TERMINATION'),      # 分销商解约 priority 5
]

for code, deadline, reason in updates:
    c.execute(
        "UPDATE video_takedown_task SET deadline_date=%s, takedown_reason=%s "
        "WHERE code=%s AND status='PENDING_PROCESS'",
        (deadline, reason, code)
    )
    print(f"  Updated {code}: deadline={deadline}, reason={reason}, rows={c.rowcount}", flush=True)

conn.commit()

# 验证更新结果
c.execute("""
    SELECT code, status, takedown_reason, deadline_date
    FROM video_takedown_task
    WHERE status='PENDING_PROCESS'
    ORDER BY deadline_date, takedown_reason
""")
print("\n=== PENDING_PROCESS tasks after update ===", flush=True)
for r in c.fetchall():
    print(f"  {r[0]} | {r[1]} | reason={r[2]} | deadline={r[3]}", flush=True)

conn.close()
print("DONE", flush=True)
