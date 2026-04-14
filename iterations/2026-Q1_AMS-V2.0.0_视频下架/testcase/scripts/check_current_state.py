"""检查当前数据库中所有视频下架任务单状态"""
import sys
import pymysql

try:
    conn = pymysql.connect(
        host='172.16.24.61', port=3306,
        user='xiaowu_db', password='}C7n%7Wklq6P',
        database='silverdawn_ams', charset='utf8mb4'
    )
    c = conn.cursor()

    c.execute("""
        SELECT code, status, takedown_reason, process_method, deadline_date,
               audit_opinion, audit_time, created_at, updated_at
        FROM video_takedown_task
        ORDER BY code
    """)
    rows = c.fetchall()
    cols = [d[0] for d in c.description]
    print("=== ALL TASKS ===", flush=True)
    for r in rows:
        d = dict(zip(cols, r))
        print(f"  {d['code']} | {d['status']} | reason={d['takedown_reason']} | method={d['process_method']} | deadline={d['deadline_date']} | audit_time={d['audit_time']}", flush=True)

    c.execute("""
        SELECT status, COUNT(*) as cnt
        FROM video_takedown_task
        GROUP BY status ORDER BY cnt DESC
    """)
    print("\n=== STATUS SUMMARY ===", flush=True)
    for r in c.fetchall():
        print(f"  {r[0]}: {r[1]}", flush=True)

    conn.close()
    print("DONE", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    sys.exit(1)
