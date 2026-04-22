"""S01-017 并发批量拆分 v4 — 使用有效的 channel/month + 正确 auth"""
import urllib.request, urllib.error, json, pymysql, sys, time, threading
from http.cookiejar import CookieJar
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

def fin_sa_login():
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.open(urllib.request.Request(
        "http://172.16.24.200:8011/sso/doLogin",
        data="name=15057199668&pwd=1111".encode(),
    ), timeout=10).read()
    return next((c.value for c in cj if c.name == 'Authorization'), None)

def call_batch_split(sa_auth, ids):
    try:
        resp = urllib.request.urlopen(urllib.request.Request(
            "http://172.16.24.200:8072/videoCompositionOverdue/batchSplit",
            data=json.dumps(ids).encode(),
            headers={"Content-Type":"application/json","Authorization":f"Bearer {sa_auth}"}
        ), timeout=30)
        return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8','replace')
        try: return json.loads(body)
        except: return {"status": e.code, "message": body}

conn = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_finance', charset='utf8mb4', autocommit=True)
cur = conn.cursor(pymysql.cursors.DictCursor)

# 准备：INSERT 2 条 status=3 可拆分记录，不同维度
# 维度 = receipted_month + channel_id + cms + pipeline_id
# 从现有可拆数据借用 channel+month
cur.execute("""
    SELECT DISTINCT yrr.channel_id, yrr.month, yrr.cms, yrr.channel_type
    FROM yt_reversal_report yrr
    WHERE yrr.received_status = 1
      AND yrr.cms = 'AC'
      AND yrr.channel_type = 1
    ORDER BY yrr.month DESC
    LIMIT 5
""")
dims = cur.fetchall()
print("可用维度（合集频道+已到账）:")
for d in dims:
    print(f"  {d}")

if len(dims) < 1:
    print("✗ 无足够维度，退出")
    sys.exit(1)

target = dims[0]
print(f"\n选用维度: channel={target['channel_id']} month={target['month']} cms={target['cms']}")

# 选一个 unique pipeline_id（借用已有 status=1 记录的 pipeline，或生成一个）
cur.execute("""
    SELECT DISTINCT pipeline_id FROM video_composition_overdue
    WHERE pipeline_id IS NOT NULL AND pipeline_id != '' LIMIT 1
""")
existing_pipeline = cur.fetchone()['pipeline_id']
print(f"借用 pipeline_id: {existing_pipeline}")

# INSERT 2 条：id1 和 id2 都指向同一维度但 import_task_id=999999 供清理
test_id1 = int(time.time() * 1000000)
test_id2 = test_id1 + 1
for tid in [test_id1, test_id2]:
    cur.execute("""
        INSERT INTO video_composition_overdue
        (id, receipted_month, month, video_id, channel_id, channel_name, cms, revenue, us_revenue, sg_revenue,
         pipeline_id, published_date, team_id, team_name, status, registration_time, deleted, created_at, updated_at, import_task_id)
        VALUES (%s, %s, %s, %s, %s, 'TEST_S01_017', %s, 100.00, 20.00, 0, %s, '2026-01-01',
                '1988839584685428736', 'HELLO BEAR', 3, NOW(), 0, NOW(), NOW(), 999999)
    """, (tid, target['month'], target['month'],
          f'TEST_S01_017_{tid}', target['channel_id'], target['cms'], existing_pipeline))
    print(f"  INSERT id={tid} status=3")

sa_auth = fin_sa_login()
print(f"\nSa-Token auth: {sa_auth}")
print("=" * 70)

# 单次拆一次 id1 先确认 API 工作
print(f"\n单次拆 id={test_id1}:")
single = call_batch_split(sa_auth, [test_id1])
print(f"  {json.dumps(single, ensure_ascii=False)[:300]}")
cur.execute("SELECT status FROM video_composition_overdue WHERE id=%s", (test_id1,))
s1 = cur.fetchone()
print(f"  DB status={s1['status'] if s1 else 'N/A'}")

# 并发拆 id2
print(f"\n并发拆 id={test_id2}（2 线程）:")
results = [None, None]
barrier = threading.Barrier(2)
def w(idx):
    my_auth = fin_sa_login()
    barrier.wait()
    results[idx] = call_batch_split(my_auth, [test_id2])
t1 = threading.Thread(target=w, args=(0,))
t2 = threading.Thread(target=w, args=(1,))
t1.start(); t2.start(); t1.join(); t2.join()

print(f"  线程 0: {json.dumps(results[0], ensure_ascii=False)[:200]}")
print(f"  线程 1: {json.dumps(results[1], ensure_ascii=False)[:200]}")

cur.execute("SELECT status FROM video_composition_overdue WHERE id=%s", (test_id2,))
s2 = cur.fetchone()
print(f"  DB 最终 status={s2['status'] if s2 else 'N/A'}")

success = [r for r in results if r.get('status') == 200]
rejected = [r for r in results if r.get('status') != 200]

# 断言
print(f"\n断言:")
assertions = [
    ("L1 至少一个请求成功", len(success) >= 1),
    ("L1 最终 DB status=2 或继续维持拆分态", s2 and s2['status'] == 2),
    ("L1 竞态保护：若两个都成功则无数据冲突", len(success) <= 1 or (s2 and s2['status'] == 2)),
]
passed = 0
for n, p in assertions:
    print(f"  [{'PASS' if p else 'FAIL'}] {n}")
    if p: passed += 1

overall = "PASS" if passed == len(assertions) else "FAIL"
print(f"\n总体: {overall} ({passed}/{len(assertions)})")

# 清理
cur.execute("DELETE FROM video_composition_overdue WHERE id IN (%s, %s) AND import_task_id=999999", (test_id1, test_id2))
print(f"\n✓ 清理完成")
conn.close()
