"""S01-017 并发批量拆分 v7 — 完整清理子集数据 + 重跑"""
import urllib.request, urllib.error, json, pymysql, sys, time, threading
from http.cookiejar import CookieJar
from datetime import datetime
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

TARGET_ID = 11299
DIM_MONTH = '2025-12'
DIM_CHANNEL = 'UC_7iONjjMgVnZTfpia-MwUg'
DIM_CMS = 'XW'

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
        ), timeout=60)
        return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8','replace')
        try: return json.loads(body)
        except: return {"status": e.code, "message": body}

conn = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_finance', charset='utf8mb4', autocommit=True)
cur = conn.cursor(pymysql.cursors.DictCursor)

print("=" * 70)
print(f"S01-017 并发批量拆分 v7 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ============ 1. 清理之前 runner8 阶段1 生成的子集 ============
print("\n--- 清理上次测试生成的子集（避免'子集已存在'拦截） ---")
cur.execute("""
    SELECT id, subset_name, settlement_no
    FROM yt_reversal_report
    WHERE channel_id=%s AND month=%s AND cms=%s
      AND settlement_no IS NULL
      AND created_at > DATE_SUB(NOW(), INTERVAL 60 MINUTE)
""", (DIM_CHANNEL, DIM_MONTH, DIM_CMS))
to_delete = cur.fetchall()
print(f"待删除子集: {len(to_delete)} 条")
for r in to_delete:
    print(f"  id={r['id']} subset={r['subset_name']}")
    cur.execute("DELETE FROM yt_reversal_report WHERE id=%s", (r['id'],))

# 确保所有 13 条 overdue 记录都是 status=1
cur.execute("""
    UPDATE video_composition_overdue
    SET status=1, original_status=NULL, operator_id=NULL, operator_name=NULL, operate_time=NULL
    WHERE month=%s AND channel_id=%s AND cms=%s AND deleted=0 AND status=2
""", (DIM_MONTH, DIM_CHANNEL, DIM_CMS))
cur.execute("""
    SELECT status, COUNT(*) as c FROM video_composition_overdue
    WHERE month=%s AND channel_id=%s AND cms=%s AND deleted=0 GROUP BY status
""", (DIM_MONTH, DIM_CHANNEL, DIM_CMS))
distr = {r['status']: r['c'] for r in cur.fetchall()}
print(f"清理后维度内 status 分布: {distr}")

# ============ 2. 并发拆分（2 线程同 id） ============
sa_auth = fin_sa_login()
print(f"\n--- 并发拆分（2 线程同时拆 id={TARGET_ID}）---")
results = [None, None]
barrier = threading.Barrier(2)
def worker(idx):
    my_auth = fin_sa_login()
    barrier.wait()
    t0 = time.time()
    r = call_batch_split(my_auth, [TARGET_ID])
    r['_elapsed'] = time.time() - t0
    results[idx] = r

t1 = threading.Thread(target=worker, args=(0,))
t2 = threading.Thread(target=worker, args=(1,))
t1.start(); t2.start(); t1.join(); t2.join()

print(f"\n线程 0 (耗时 {results[0].get('_elapsed', 0):.2f}s): {json.dumps(results[0], ensure_ascii=False)[:300]}")
print(f"线程 1 (耗时 {results[1].get('_elapsed', 0):.2f}s): {json.dumps(results[1], ensure_ascii=False)[:300]}")

time.sleep(2)
cur.execute("""
    SELECT status, COUNT(*) as c FROM video_composition_overdue
    WHERE month=%s AND channel_id=%s AND cms=%s AND deleted=0 GROUP BY status
""", (DIM_MONTH, DIM_CHANNEL, DIM_CMS))
final = {r['status']: r['c'] for r in cur.fetchall()}
print(f"\n最终 status 分布: {final}")

# 查新生成的子集数
cur.execute("""
    SELECT COUNT(*) as c FROM yt_reversal_report
    WHERE channel_id=%s AND month=%s AND cms=%s
      AND settlement_no IS NULL
      AND created_at > DATE_SUB(NOW(), INTERVAL 3 MINUTE)
""", (DIM_CHANNEL, DIM_MONTH, DIM_CMS))
new_subsets = cur.fetchone()['c']
print(f"本次执行新生成的子集数: {new_subsets}")

# ============ 3. 断言 ============
success_count = sum(1 for r in results if r.get('status') == 200)
rejected = [r for r in results if r.get('status') != 200]
all_split = final.get(2, 0) > 0 and final.get(1, 0) == 0

print(f"\n断言:")
a1 = success_count >= 1
a2 = all_split
a3 = new_subsets <= 1  # 竞态保护：不应生成重复 subset
a4 = success_count == 1

print(f"  [{'PASS' if a1 else 'FAIL'}] L1 至少一个请求成功 (success={success_count})")
print(f"  [{'PASS' if a2 else 'FAIL'}] L1 最终维度所有记录 status=2")
print(f"  [{'PASS' if a3 else 'FAIL'}] L1 竞态保护：无重复子集生成 (新增 {new_subsets} 个)")
print(f"  [{'PASS' if a4 else 'INFO'}] L2 理想竞态：仅一个 API 成功")

if rejected:
    print(f"\n被拒绝消息: {[r.get('message') for r in rejected]}")

overall = "PASS" if a1 and a2 and a3 else "FAIL"
print(f"\n总体: {overall}")
conn.close()
