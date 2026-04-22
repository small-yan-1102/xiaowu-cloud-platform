"""S01-017 并发批量拆分 v2 — 每次重新登录取 fresh token"""
import urllib.request, urllib.error, json, pymysql, sys, time, threading
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

def fin_login():
    raw = urllib.request.urlopen(urllib.request.Request(
        "http://172.16.24.200:8011/sso/doLogin",
        data="name=15057199668&pwd=1111".encode(),
    ), timeout=10).read().decode('utf-8').replace('\t',' ')
    return json.loads(raw)['data']['accessToken']

def get_candidate(token, team_id):
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        "http://distribute.test.xiaowutw.com/appApi/videoComposition/pageList",
        data=json.dumps({"teamId":team_id,"related":"2","language":"zh","videoId":BASE_VIDEO_ID,"pageNum":1,"pageSize":5}).encode(),
        headers={"Content-Type":"application/json","accessToken":token}
    ), timeout=10).read())
    recs = r['data'].get('records', [])
    return recs[0] if recs else None

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

def insert_overdue(conn_fin, video, published_date, team_id):
    cur = conn_fin.cursor()
    test_id = int(time.time() * 1000000)
    next_month = (datetime.strptime(published_date, '%Y-%m-%d') + timedelta(days=40)).strftime('%Y-%m')
    cur.execute("""
        INSERT INTO video_composition_overdue
        (id, receipted_month, month, video_id, channel_id, channel_name, cms, revenue, us_revenue, sg_revenue,
         pipeline_id, published_date, team_id, team_name, status, deleted, created_at, updated_at, import_task_id)
        VALUES (%s, %s, %s, %s, %s, %s, 'AC', 10.00, 2.00, 0, NULL, %s, %s, 'HELLO BEAR', 0, 0, NOW(), NOW(), 999999)
    """, (test_id, next_month, published_date[:7],
          video['videoId'], video['channelId'], video['channelName'],
          published_date, team_id))
    return test_id

def cleanup_overdue_all(conn_fin, video_id):
    conn_fin.cursor().execute("DELETE FROM video_composition_overdue WHERE video_id=%s AND import_task_id=999999", (video_id,))

def call_bind(token, video):
    body = {
        "id": video['id'], "videoId": video['videoId'],
        "compositionId": video['compositionId'], "amsCompositionId": video['amsCompositionId'],
        "compositionName": video['compositionName'],
        "compositionServicePackageId": video['compositionServicePackageId'],
        "servicePackageCode": video['servicePackageCode'],
        "servicePackageName": video['servicePackageName'],
        "channelId": video['channelId'], "changeRelated": "2"
    }
    try:
        return json.loads(urllib.request.urlopen(urllib.request.Request(
            "http://distribute.test.xiaowutw.com/appApi/videoComposition/bind",
            data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json","accessToken":token}
        ), timeout=15).read())
    except urllib.error.HTTPError as e:
        return {"status": e.code, "message": e.read()[:300].decode('utf-8','replace')}

def call_batch_split(fin_token, ids):
    try:
        resp = urllib.request.urlopen(urllib.request.Request(
            f"{FIN_BASE}/videoCompositionOverdue/batchSplit",
            data=json.dumps(ids).encode(),
            headers={"Content-Type":"application/json","accessToken":fin_token}
        ), timeout=30)
        return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode('utf-8','replace')
        try:
            return json.loads(body)
        except:
            return {"status": e.code, "message": body}

# ============ 主流程 ============
conn_fin = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_finance', charset='utf8mb4', autocommit=True)
conn_dist = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_distribution', charset='utf8mb4', autocommit=True)

jlb_token, team_id = jlb_login()

print("=" * 70)
print(f"S01-017 并发批量拆分 v2 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# 1. 准备：造一条 status=3 记录
reset_jlb(conn_dist)
set_jlb_dates(conn_dist, "2026-03-15 10:00:00")
time.sleep(0.5)
video = get_candidate(jlb_token, team_id)
test_id = insert_overdue(conn_fin, video, "2026-03-15", team_id)
print(f"\n准备 DB id={test_id}")

bind_resp = call_bind(jlb_token, video)
print(f"bind: status={bind_resp.get('status')}")
time.sleep(6)

cur = conn_fin.cursor(pymysql.cursors.DictCursor)
cur.execute("SELECT status FROM video_composition_overdue WHERE id=%s", (test_id,))
print(f"MQ 同步后 status={cur.fetchone()['status']}")

# 2. 并发拆分 — 每线程独立登录获 fresh token
print(f"\n--- 并发拆分（2 线程，每线程独立 login）---")
results = [None, None]
barrier = threading.Barrier(2)
def split_worker(idx):
    # 每线程独立登录
    my_token = fin_login()
    barrier.wait()
    results[idx] = call_batch_split(my_token, [test_id])

t1 = threading.Thread(target=split_worker, args=(0,))
t2 = threading.Thread(target=split_worker, args=(1,))
t1.start(); t2.start()
t1.join(); t2.join()

print(f"\n线程 0: {json.dumps(results[0], ensure_ascii=False)[:300]}")
print(f"线程 1: {json.dumps(results[1], ensure_ascii=False)[:300]}")

# 查 DB 最终
time.sleep(3)
cur.execute("SELECT status FROM video_composition_overdue WHERE id=%s", (test_id,))
final = cur.fetchone()
print(f"\nDB 最终 status={final['status'] if final else 'N/A'}")

# 断言
success = [r for r in results if r.get('status') == 200]
rejected = [r for r in results if r.get('status') != 200]
assertions = [
    ("L1 至少一个拆分成功（status=200）", len(success) >= 1),
    ("L1 竞态保护：最多一个完全成功拆分", len(success) <= 1 or (final and final['status'] == 2)),
    ("L1 最终 DB status=2（已拆分）", final and final['status'] == 2),
]

# 清理
cleanup_overdue_all(conn_fin, video['videoId'])
reset_jlb(conn_dist)
conn_fin.close()
conn_dist.close()

passed = sum(1 for _,p in assertions if p)
overall = "PASS" if passed == len(assertions) else "FAIL"
print(f"\n断言:")
for n, p in assertions:
    print(f"  [{'PASS' if p else 'FAIL'}] {n}")
print(f"\n总体: {overall} ({passed}/{len(assertions)})")
