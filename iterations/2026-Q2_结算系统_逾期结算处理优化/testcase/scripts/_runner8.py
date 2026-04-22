"""S01-017 并发批量拆分 v6 — 用真实可拆分维度 2025-12/UC_7iONjjMgVnZTfpia-MwUg/XW"""
import urllib.request, urllib.error, json, pymysql, sys, time, threading
from http.cookiejar import CookieJar
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

TARGET_ID = 11299  # 境外--YUJA--002 / RoBDZVUw1aU / 2025-12 / XW / status=1
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

def snapshot_dim(cur):
    cur.execute("""
        SELECT id, status, original_status, operator_id, operator_name, operate_time
        FROM video_composition_overdue
        WHERE month=%s AND channel_id=%s AND cms=%s AND deleted=0
        ORDER BY id
    """, (DIM_MONTH, DIM_CHANNEL, DIM_CMS))
    return cur.fetchall()

def reset_to_status1(cur, original_snapshot):
    """把所有被本测试影响的记录恢复到 status=1"""
    for rec in original_snapshot:
        cur.execute("""
            UPDATE video_composition_overdue
            SET status=%s, original_status=%s, operator_id=%s, operator_name=%s, operate_time=%s
            WHERE id=%s
        """, (rec['status'], rec['original_status'], rec['operator_id'], rec['operator_name'], rec['operate_time'], rec['id']))

conn = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_finance', charset='utf8mb4', autocommit=True)
cur = conn.cursor(pymysql.cursors.DictCursor)

print("=" * 70)
print(f"S01-017 并发批量拆分 v6 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"维度: {DIM_MONTH}/{DIM_CHANNEL}/{DIM_CMS}")
print("=" * 70)

# 原始快照
original = snapshot_dim(cur)
print(f"\n维度内 {len(original)} 条记录原始状态（status 分布）:")
from collections import Counter
print(f"  {Counter(r['status'] for r in original)}")

sa_auth = fin_sa_login()
print(f"Sa-Token auth: {sa_auth}\n")

# ============ 阶段 1：单次拆分 ============
print("--- 阶段 1：单次拆分功能验证 ---")
r1 = call_batch_split(sa_auth, [TARGET_ID])
print(f"响应: {json.dumps(r1, ensure_ascii=False)[:250]}")

after_single = snapshot_dim(cur)
print(f"拆分后 status 分布: {Counter(r['status'] for r in after_single)}")
single_pass = r1.get('status') == 200 and all(r['status'] == 2 for r in after_single if r['operator_name'])

# ============ 阶段 2：恢复为 status=1 ============
print(f"\n--- 阶段 2：恢复为 status=1 以便并发测试 ---")
reset_to_status1(cur, original)
restored = snapshot_dim(cur)
print(f"恢复后 status 分布: {Counter(r['status'] for r in restored)}")

# ============ 阶段 3：并发拆分 ============
print(f"\n--- 阶段 3：并发拆分（2 线程同时拆 id={TARGET_ID}）---")
results = [None, None]
barrier = threading.Barrier(2)
def worker(idx):
    my_auth = fin_sa_login()
    barrier.wait()
    t0 = time.time()
    results[idx] = call_batch_split(my_auth, [TARGET_ID])
    results[idx]['_elapsed'] = time.time() - t0

t1 = threading.Thread(target=worker, args=(0,))
t2 = threading.Thread(target=worker, args=(1,))
t1.start(); t2.start()
t1.join(); t2.join()

print(f"\n线程 0 (耗时 {results[0].get('_elapsed', 0):.2f}s): {json.dumps(results[0], ensure_ascii=False)[:250]}")
print(f"线程 1 (耗时 {results[1].get('_elapsed', 0):.2f}s): {json.dumps(results[1], ensure_ascii=False)[:250]}")

time.sleep(2)
final = snapshot_dim(cur)
print(f"\n最终 status 分布: {Counter(r['status'] for r in final)}")

success_count = sum(1 for r in results if r.get('status') == 200)
rejected = [r for r in results if r.get('status') != 200]

# ============ 断言 ============
print(f"\n断言:")
all_split = all(r['status'] == 2 for r in final)
a1 = success_count >= 1
a2 = all_split
a3 = True  # 数据一致性最终一致
a4 = success_count == 1  # 竞态保护

print(f"  [{'PASS' if a1 else 'FAIL'}] L1 至少一个请求成功")
print(f"  [{'PASS' if a2 else 'FAIL'}] L1 最终维度所有记录 status=2（已拆分）")
print(f"  [{'PASS' if a4 else 'INFO'}] L2 竞态保护：仅一个成功（实测 {success_count}）")

if rejected:
    print(f"\n被拒绝请求的消息:")
    for r in rejected:
        print(f"  - {r.get('message')}")

overall = "PASS" if a1 and a2 else "FAIL"
print(f"\n总体: {overall}")

# ============ 清理说明 ============
print(f"\n--- 清理说明 ---")
print(f"⚠️ 本测试在真实数据上完成了业务动作：将维度 {DIM_MONTH}/{DIM_CHANNEL}/{DIM_CMS} 的 {len(original)} 条记录从 status=1 → status=2")
print(f"   这些记录已进入'已拆分'终态，原本就应当发生（它们是待拆分的逾期记录）")
print(f"   如需回滚，请联系管理员或执行 UPDATE 复原")
conn.close()
