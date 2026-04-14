"""
调整 VT-013 测试数据: 截止日期 = TODAY / TOMORROW / DAY_AFTER_TOMORROW
TODAY = 2026-04-01
"""
import pymysql

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'database': 'silverdawn_ams',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

def adjust_for_vt013():
    """将3条PENDING_PROCESS的deadline改为TODAY/TOMORROW/DAY_AFTER"""
    conn = pymysql.connect(**DB)
    c = conn.cursor(pymysql.cursors.DictCursor)
    
    updates = [
        ('V2603300004', '2026-04-01', 'TEMP_COPYRIGHT_DISPUTE'),    # TODAY - 排第一
        ('V2603300003', '2026-04-02', 'TEMP_COPYRIGHT_DISPUTE'),    # TOMORROW
        ('V2603300006', '2026-04-03', 'ADJUST_LAUNCH_TIME'),        # DAY_AFTER
    ]
    
    print('=== VT-013 数据调整: deadline=TODAY/TOMORROW/DAY_AFTER ===')
    for code, deadline, reason in updates:
        c.execute(
            "UPDATE video_takedown_task SET deadline_date=%s, takedown_reason=%s "
            "WHERE code=%s AND status='PENDING_PROCESS'",
            (deadline, reason, code)
        )
        print(f"  {code} -> deadline={deadline}, reason={reason} (rows={c.rowcount})")
    
    conn.commit()
    
    # 验证
    c.execute(
        "SELECT code, status, deadline_date, takedown_reason "
        "FROM video_takedown_task WHERE status='PENDING_PROCESS' ORDER BY deadline_date"
    )
    print('\n=== PENDING_PROCESS 任务(按deadline排序) ===')
    for t in c.fetchall():
        print(f"  {t['code']} | deadline={t['deadline_date']} | reason={t['takedown_reason']}")
    
    # 同时检查 REVIEW_REJECTED
    c.execute(
        "SELECT code, status, audit_opinion "
        "FROM video_takedown_task WHERE status='REVIEW_REJECTED'"
    )
    print('\n=== REVIEW_REJECTED 任务 ===')
    for t in c.fetchall():
        print(f"  {t['code']} | opinion={t['audit_opinion']}")
    
    conn.close()
    print('\n数据调整完成，可以开始执行 VT-013/VT-018/VT-027')

if __name__ == '__main__':
    adjust_for_vt013()
