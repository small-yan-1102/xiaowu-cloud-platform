"""检查已完成任务单的作品和视频明细数据"""
import pymysql, os

pw = '}C7n%7Wklq6P'
conn = pymysql.connect(
    host='172.16.24.61', port=3306,
    user='xiaowu_db', password=pw,
    database='silverdawn_ams', charset='utf8mb4'
)
c = conn.cursor()

out = []

# 查询已完成任务的作品数和视频明细
c.execute("""
    SELECT t.code, t.status,
           COUNT(DISTINCT td.composition_id) as comp_count,
           COUNT(td.id) as detail_count
    FROM video_takedown_task t
    LEFT JOIN video_takedown_task_detail td ON t.id = td.task_id
    WHERE t.status = 'COMPLETED'
    GROUP BY t.code, t.status
    ORDER BY comp_count DESC
""")
rows = c.fetchall()
out.append("=== COMPLETED tasks with composition/detail counts ===")
for r in rows:
    out.append(f"  {r[0]} | compositions={r[2]} | details={r[3]}")

# 找到有最多作品的任务，查看其视频明细
if rows:
    best = rows[0]
    out.append(f"\nBest candidate: {best[0]} with {best[2]} compositions, {best[3]} details")

    # 获取该任务的 task_id
    c.execute("SELECT id FROM video_takedown_task WHERE code=%s", (best[0],))
    task_id = c.fetchone()[0]

    # 查看视频明细
    c.execute("""
        SELECT td.video_id, td.video_title, td.composition_name, td.cp_name,
               td.pipeline_id, td.video_status, td.status_detail
        FROM video_takedown_task_detail td
        WHERE td.task_id = %s
        LIMIT 10
    """, (task_id,))
    details = c.fetchall()
    cols = [d[0] for d in c.description]
    out.append(f"\nDetails for {best[0]}:")
    for d in details:
        dd = dict(zip(cols, d))
        out.append(f"  video_id={dd['video_id']} | title={dd['video_title']} | "
                   f"comp={dd['composition_name']} | status={dd['video_status']}")

conn.close()
out.append("DONE")

result_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vt025_check.txt")
with open(result_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
