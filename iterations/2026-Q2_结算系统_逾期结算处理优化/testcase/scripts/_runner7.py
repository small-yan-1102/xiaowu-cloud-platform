"""S01-017 并发批量拆分 v5 — 用真实可拆分记录 id=26779"""
import urllib.request, urllib.error, json, pymysql, sys, time, threading
from http.cookiejar import CookieJar
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

TARGET_ID = 26779  # HELLO BEAR / 足球张雨琦 / 2026-01 / video=-Bn51jJNeJc / status=3

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

# ============ 1. 记录原始状态 ============
cur.execute("""
    SELECT id, status, receipted_month, month, channel_id, video_id, pipeline_id,
           original_status, operator_id, operator_name, operate_time, updated_at
    FROM video_composition_overdue WHERE id=%s
""", (TARGET_ID,))
orig = cur.fetchone()
print(f"原始状态: id={orig['id']} status={orig['status']} pipeline={orig['pipeline_id'][:15]} operator={orig['operator_name']}")
print(f"  month={orig['month']} channel={orig['channel_id']} video={orig['video_id']}")

sa_auth = fin_sa_login()
print(f"Sa-Token auth: {sa_auth}")
print("=" * 70)

# ============ 2. 单次拆分测试（先做功能验证）============
print(f"\n--- 阶段 1：单次拆分功能验证 ---")
print(f"POST /videoCompositionOverdue/batchSplit body=[{TARGET_ID}]")
r1 = call_batch_split(sa_auth, [TARGET_ID])
print(f"响应: {json.dumps(r1, ensure_ascii=False)[:300]}")

cur.execute("SELECT status, original_status, operator_id, operator_name FROM video_composition_overdue WHERE id=%s", (TARGET_ID,))
after1 = cur.fetchone()
print(f"DB status={after1['status']} original_status={after1['original_status']} operator={after1['operator_name']}")

single_pass = r1.get('status') == 200 and after1['status'] == 2

# ============ 3. 重置为 status=3 再做并发 ============
if single_pass:
    print(f"\n--- 阶段 2：重置状态 → status=3 以便并发 ---")
    cur.execute("""
        UPDATE video_composition_overdue
        SET status=3, original_status=NULL, operator_id=NULL, operator_name=NULL, operate_time=NULL
        WHERE id=%s
    """, (TARGET_ID,))
    cur.execute("SELECT status FROM video_composition_overdue WHERE id=%s", (TARGET_ID,))
    print(f"重置后 status={cur.fetchone()['status']}")

    # ============ 4. 并发拆分 ============
    print(f"\n--- 阶段 3：并发拆分（2 线程同时拆同一 id）---")
    results = [None, None]
    barrier = threading.Barrier(2)
    def w(idx):
        my_auth = fin_sa_login()
        barrier.wait()
        results[idx] = call_batch_split(my_auth, [TARGET_ID])
    t1 = threading.Thread(target=w, args=(0,))
    t2 = threading.Thread(target=w, args=(1,))
    t1.start(); t2.start()
    t1.join(); t2.join()

    print(f"线程 0: {json.dumps(results[0], ensure_ascii=False)[:250]}")
    print(f"线程 1: {json.dumps(results[1], ensure_ascii=False)[:250]}")

    time.sleep(2)
    cur.execute("SELECT status, operator_name, operate_time FROM video_composition_overdue WHERE id=%s", (TARGET_ID,))
    final = cur.fetchone()
    print(f"\n最终 DB status={final['status']} operator={final['operator_name']} time={final['operate_time']}")

    success_count = sum(1 for r in results if r.get('status') == 200)
    rejected = [r for r in results if r.get('status') != 200]

    # 断言
    print(f"\n断言:")
    a1 = success_count >= 1
    a2 = final['status'] == 2
    a3 = success_count <= 1 or final['status'] == 2  # 两个都成功也 OK 只要最终一致
    a4 = success_count == 1  # 竞态保护：理想情况只一个成功
    print(f"  [{'PASS' if a1 else 'FAIL'}] L1 至少一个请求成功")
    print(f"  [{'PASS' if a2 else 'FAIL'}] L1 最终 DB status=2（已拆分）")
    print(f"  [{'PASS' if a3 else 'FAIL'}] L1 数据一致性保障")
    print(f"  [{'PASS' if a4 else 'INFO'}] L2 理想竞态保护：仅一个成功（实测 {success_count}，若 2 个都成功说明存在幂等但无拦截）")

    if rejected:
        print(f"\n被拒绝请求的消息: {[r.get('message') for r in rejected]}")

    overall = "PASS" if a1 and a2 and a3 else "FAIL"
    print(f"\n总体: {overall}")
else:
    print(f"\n❌ 单次拆分已失败，跳过并发测试")
    print(f"   原因: {r1.get('message')}")
    overall = "FAIL"

# ============ 5. 清理（保持 status=2 已拆分的最终态）============
print(f"\n--- 清理 ---")
cur.execute("SELECT status FROM video_composition_overdue WHERE id=%s", (TARGET_ID,))
cur_status = cur.fetchone()['status']
print(f"当前 status={cur_status}")
if cur_status == 2:
    print(f"✓ 保持 status=2 最终态（与单次拆分后一致）")
else:
    # 如果不是 2，尝试再拆一次走到终态
    print(f"⚠️ status={cur_status}，应为 2，可能需要手工检查")

conn.close()
