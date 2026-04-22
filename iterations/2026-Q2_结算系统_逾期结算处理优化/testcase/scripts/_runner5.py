"""S01-017 并发批量拆分 v3 — 使用 Authorization: Bearer <uuid> 正确认证"""
import urllib.request, urllib.error, json, pymysql, sys, time, threading
from http.cookiejar import CookieJar
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')

BASE_VIDEO_ID = '_ibqnYAR77c'
ORIGINAL_PUBLISHED = '2026-03-10 06:40:51'
ORIGINAL_SCRAPED = '2026-03-10 07:30:25'
FIN_BASE = "http://172.16.24.200:8072"

def jlb_login():
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        "http://distribute.test.xiaowutw.com/appApi/user/emailAndPwdLogin",
        data=json.dumps({"email":"Yancz-cool@outlook.com","password":"TxdvZ06y"}).encode(),
        headers={"Content-Type":"application/json"}
    ), timeout=10).read())
    return r['data']['accessToken'], r['data']['teamId']

def fin_sa_login():
    """返回 Sa-Token 所需的 Authorization UUID"""
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.open(urllib.request.Request(
        "http://172.16.24.200:8011/sso/doLogin",
        data="name=15057199668&pwd=1111".encode(),
    ), timeout=10).read()
    return next((c.value for c in cj if c.name == 'Authorization'), None)

def get_candidate(token, team_id):
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        "http://distribute.test.xiaowutw.com/appApi/videoComposition/pageList",
        data=json.dumps({"teamId":team_id,"related":"2","language":"zh","videoId":BASE_VIDEO_ID,"pageNum":1,"pageSize":5}).encode(),
        headers={"Content-Type":"application/json","accessToken":token}
    ), timeout=10).read())
    return r['data']['records'][0] if r['data'].get('records') else None

def reset_jlb(conn_dist):
    conn_dist.cursor().execute("""
        UPDATE video_composition SET related='2', related_at=NULL, change_related_at=NULL, change_related_count=0,
            published_at=%s, published_date=%s, scraped_at=%s WHERE video_id=%s
    """, (ORIGINAL_PUBLISHED, ORIGINAL_PUBLISHED[:10], ORIGINAL_SCRAPED, BASE_VIDEO_ID))

def set_jlb_dates(conn_dist, published_at, scraped_at=None):
    cur = conn_dist.cursor()
    sc = scraped_at or published_at
    cur.execute("UPDATE video_composition SET published_at=%s, published_date=%s, scraped_at=%s WHERE video_id=%s",
                (published_at, published_at[:10], sc, BASE_VIDEO_ID))

def call_bind(token, video):
    body = {"id":video['id'],"videoId":video['videoId'],"compositionId":video['compositionId'],"amsCompositionId":video['amsCompositionId'],"compositionName":video['compositionName'],"compositionServicePackageId":video['compositionServicePackageId'],"servicePackageCode":video['servicePackageCode'],"servicePackageName":video['servicePackageName'],"channelId":video['channelId'],"changeRelated":"2"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        "http://distribute.test.xiaowutw.com/appApi/videoComposition/bind",
        data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json","accessToken":token}
    ), timeout=15).read())

def call_batch_split(sa_auth, ids):
    try:
        resp = urllib.request.urlopen(urllib.request.Request(
            f"{FIN_BASE}/videoCompositionOverdue/batchSplit",
            data=json.dumps(ids).encode(),
            headers={"Content-Type":"application/json","Authorization":f"Bearer {sa_auth}"}
        ), timeout=30)
        return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8','replace')
        try: return json.loads(body)
        except: return {"status": e.code, "message": body}

# ============ 主流程 ============
conn_fin = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_finance', charset='utf8mb4', autocommit=True)
conn_dist = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_distribution', charset='utf8mb4', autocommit=True)

jlb_token, team_id = jlb_login()
sa_auth = fin_sa_login()
print(f"jlb_token len={len(jlb_token)}, sa_auth={sa_auth}")

print("=" * 70)
print(f"S01-017 并发批量拆分 v3 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# 找一个"可拆分"的冲销表已到账的 receipted_month 对应 channel
# 策略：挑 yt_reversal_report 中 received_status != 0 的记录，取其 channel + month
cur = conn_fin.cursor(pymysql.cursors.DictCursor)
cur.execute("""
    SELECT channel_id, month, received_status, cms
    FROM yt_reversal_report
    WHERE received_status IS NOT NULL AND received_status != 0
      AND deleted=0
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  可拆: channel={r['channel_id']} month={r['month']} received_status={r['received_status']}")

# 用 _ibqnYAR77c 构造一个 2026-03 month 的记录（假设 2026-03 冲销表已到）
# 先看 2026-03 在冲销表状态
cur.execute("SELECT channel_id, month, received_status FROM yt_reversal_report WHERE month='2026-03' AND channel_id='UC4iyNkGAdPcW96CyFTxQmGQ' LIMIT 5")
for r in cur.fetchall():
    print(f"  _ibqnYAR77c 所在频道 2026-03 冲销表: received_status={r['received_status']}")

# 准备两条相同维度记录（同 receipted_month+channel+cms+pipeline）做并发拆分
reset_jlb(conn_dist)
set_jlb_dates(conn_dist, "2026-03-15 10:00:00")
time.sleep(0.5)
video = get_candidate(jlb_token, team_id)

# 插入 2 条同维度记录
test_id1 = int(time.time() * 1000000)
test_id2 = test_id1 + 1
for tid in [test_id1, test_id2]:
    conn_fin.cursor().execute("""
        INSERT INTO video_composition_overdue
        (id, receipted_month, month, video_id, channel_id, channel_name, cms, revenue, us_revenue, sg_revenue,
         pipeline_id, published_date, team_id, team_name, status, deleted, created_at, updated_at, import_task_id)
        VALUES (%s, '2026-04', '2026-03', %s, %s, %s, 'AC', 10.00, 2.00, 0, NULL, '2026-03-15', %s, 'HELLO BEAR', 0, 0, NOW(), NOW(), 999999)
    """, (tid, video['videoId'], video['channelId'], video['channelName'], team_id))
print(f"\n插入两条 DB 记录 id={test_id1}, {test_id2}")

bind_r = call_bind(jlb_token, video)
print(f"bind: {bind_r.get('status')}")
time.sleep(6)

cur.execute("SELECT id, status, pipeline_id FROM video_composition_overdue WHERE id IN (%s,%s)" , (test_id1, test_id2))
recs = cur.fetchall()
print(f"MQ 同步后:")
for r in recs:
    print(f"  id={r['id']} status={r['status']} pipeline={r['pipeline_id']}")

# 单次拆分测试（先确认不会遇到其他错误）
print(f"\n--- 单次拆 id={test_id1} 确认流程 ---")
single_resp = call_batch_split(sa_auth, [test_id1])
print(f"  {json.dumps(single_resp, ensure_ascii=False)[:300]}")

# 如果单次拆分成功，查 DB
cur.execute("SELECT status FROM video_composition_overdue WHERE id=%s", (test_id1,))
single_final = cur.fetchone()
print(f"  id={test_id1} DB status={single_final['status'] if single_final else 'N/A'}")

# 如果单次成功（冲销表等业务条件 OK），尝试并发
can_concurrent = single_resp.get('status') == 200 or '冲销表' not in str(single_resp.get('message',''))
if can_concurrent and single_resp.get('status') == 200:
    print(f"\n--- 并发测试：对 id={test_id2} 并发拆 2 次 ---")
    results = [None, None]
    barrier = threading.Barrier(2)
    def w(idx):
        my_auth = fin_sa_login()
        barrier.wait()
        results[idx] = call_batch_split(my_auth, [test_id2])
    t1 = threading.Thread(target=w, args=(0,)); t2 = threading.Thread(target=w, args=(1,))
    t1.start(); t2.start(); t1.join(); t2.join()
    print(f"  线程 0: {json.dumps(results[0], ensure_ascii=False)[:200]}")
    print(f"  线程 1: {json.dumps(results[1], ensure_ascii=False)[:200]}")

    success = [r for r in results if r.get('status') == 200]
    cur.execute("SELECT status FROM video_composition_overdue WHERE id=%s", (test_id2,))
    final = cur.fetchone()
    print(f"  最终 DB status={final['status'] if final else 'N/A'}")

    print(f"\n断言:")
    print(f"  [{'PASS' if len(success) >= 1 else 'FAIL'}] 至少一个成功")
    print(f"  [{'PASS' if final and final['status'] == 2 else 'FAIL'}] 最终 status=2")
    print(f"  [{'PASS' if len(success) == 1 else 'INFO'}] 竞态保护：仅一个返回200（实测 {len(success)} 个）")
else:
    print(f"\n❌ 单次拆分已失败，无法进行并发测试")
    print(f"   失败原因: {single_resp.get('message')}")
    print(f"   这说明 _ibqnYAR77c 所在月份的冲销表尚未到账，需换其他可拆分的测试数据")

# 清理
conn_fin.cursor().execute("DELETE FROM video_composition_overdue WHERE id IN (%s, %s) AND import_task_id=999999", (test_id1, test_id2))
reset_jlb(conn_dist)
conn_fin.close(); conn_dist.close()
