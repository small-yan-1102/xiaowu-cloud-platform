import pymysql
import os

conn = pymysql.connect(
    host='172.16.24.61', port=3306, user='xiaowu_db',
    password='}C7n%7Wklq6P', database='silverdawn_ams',
    charset='utf8mb4'
)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'full_state_result.txt')
lines = []

with conn.cursor() as cur:
    # 查表结构
    cur.execute("SHOW COLUMNS FROM video_takedown_task")
    all_cols = [c[0] for c in cur.fetchall()]
    lines.append(f"COLUMNS: {all_cols}")

    # 找软删除字段
    del_col = None
    for c in all_cols:
        if 'delete' in c.lower():
            del_col = c
            break
    del_cond = f"`{del_col}` = 0" if del_col else "1=1"
    lines.append(f"DEL_COL: {del_col}")

    # 查全部任务
    cur.execute(f"SELECT * FROM video_takedown_task WHERE {del_cond} ORDER BY created_at")
    desc = [d[0] for d in cur.description]
    rows = cur.fetchall()

    lines.append(f"DESC: {desc}")
    lines.append(f"TASK COUNT: {len(rows)}")
    lines.append("")

    for row in rows:
        d = dict(zip(desc, row))
        no_val = d.get('task_number', d.get('number', d.get('id', '?')))
        st = d.get('status', '?')
        pm = d.get('process_method', '?')
        tr = d.get('takedown_reason', '?')
        dd = d.get('deadline_date', d.get('deadline', '?'))
        at = d.get('audit_time', '?')
        lines.append(f"{no_val} | {st} | {pm} | {tr} | dd={dd} | audit={at}")

    # 统计状态分布
    cur.execute(f"""
        SELECT status, process_method, COUNT(*) FROM video_takedown_task
        WHERE {del_cond} GROUP BY status, process_method ORDER BY status
    """)
    lines.append("\nSTATUS DISTRIBUTION:")
    for r in cur.fetchall():
        lines.append(f"  {r[0]} / {r[1]} = {r[2]}")

    # 查 composition 表结构
    cur.execute("SHOW COLUMNS FROM video_takedown_task_composition")
    tc_cols = [c[0] for c in cur.fetchall()]
    lines.append(f"\nTC_COLUMNS: {tc_cols}")

    tc_del_col = None
    for c in tc_cols:
        if 'delete' in c.lower():
            tc_del_col = c
            break
    tc_del_cond = f"tc.`{tc_del_col}` = 0" if tc_del_col else "1=1"

    # 查作品数
    cur.execute(f"""
        SELECT t.id, t.status, COUNT(tc.id) as cc
        FROM video_takedown_task t
        LEFT JOIN video_takedown_task_composition tc ON t.id = tc.task_id AND {tc_del_cond}
        WHERE {del_cond.replace('`', 't.`')} GROUP BY t.id ORDER BY cc DESC
    """)
    lines.append("\nCOMPOSITION COUNTS:")
    for r in cur.fetchall():
        lines.append(f"  id={r[0]} status={r[1]} compositions={r[2]}")

    # 解约单
    cur.execute("SHOW COLUMNS FROM composition_terminate")
    ter_cols = [c[0] for c in cur.fetchall()]
    ter_del_col = None
    for c in ter_cols:
        if 'delete' in c.lower():
            ter_del_col = c
            break
    ter_del_cond = f"`{ter_del_col}` = 0" if ter_del_col else "1=1"
    cur.execute(f"SELECT COUNT(*) FROM composition_terminate WHERE {ter_del_cond}")
    lines.append(f"\nTERMINATION COUNT: {cur.fetchone()[0]}")

conn.close()

with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("DONE")
