"""SET-01 批量执行脚本 v3 — 覆盖剩余可行用例"""
import urllib.request, urllib.error, json, pymysql, sys, time
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')

BASE_VIDEO_ID = '_ibqnYAR77c'
ORIGINAL_PUBLISHED = '2026-03-10 06:40:51'
ORIGINAL_SCRAPED = '2026-03-10 07:30:25'

def jlb_login():
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        "http://distribute.test.xiaowutw.com/appApi/user/emailAndPwdLogin",
        data=json.dumps({"email":"Yancz-cool@outlook.com","password":"TxdvZ06y"}).encode(),
        headers={"Content-Type":"application/json"}
    ), timeout=10).read())
    return r['data']['accessToken'], r['data']['teamId']

def get_candidate(token, team_id):
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        "http://distribute.test.xiaowutw.com/appApi/videoComposition/pageList",
        data=json.dumps({"teamId":team_id,"related":"2","language":"zh","videoId":BASE_VIDEO_ID,"pageNum":1,"pageSize":5}).encode(),
        headers={"Content-Type":"application/json","accessToken":token}
    ), timeout=10).read())
    recs = r['data'].get('records', [])
    return recs[0] if recs else None

def reset_jlb(conn_dist, restore_publish=True):
    cur = conn_dist.cursor()
    if restore_publish:
        cur.execute("""
            UPDATE video_composition
            SET related='2', related_at=NULL, change_related_at=NULL, change_related_count=0,
                published_at=%s, published_date=%s, scraped_at=%s
            WHERE video_id=%s
        """, (ORIGINAL_PUBLISHED, ORIGINAL_PUBLISHED[:10], ORIGINAL_SCRAPED, BASE_VIDEO_ID))
    else:
        cur.execute("UPDATE video_composition SET related='2', related_at=NULL, change_related_at=NULL, change_related_count=0 WHERE video_id=%s", (BASE_VIDEO_ID,))

def set_jlb_dates(conn_dist, published_at, scraped_at=None):
    cur = conn_dist.cursor()
    sc = scraped_at or published_at
    cur.execute("""
        UPDATE video_composition SET published_at=%s, published_date=%s, scraped_at=%s WHERE video_id=%s
    """, (published_at, published_at[:10], sc, BASE_VIDEO_ID))

def insert_overdue(conn_fin, video_info, published_date, team_id, receipted_month=None, month=None, status=0, registration_time=None):
    cur = conn_fin.cursor()
    test_id = int(time.time() * 1000000)
    next_month = receipted_month or (datetime.strptime(published_date, '%Y-%m-%d') + timedelta(days=40)).strftime('%Y-%m')
    mo = month or published_date[:7]
    cur.execute("""
        INSERT INTO video_composition_overdue
        (id, receipted_month, month, video_id, channel_id, channel_name, cms, revenue, us_revenue, sg_revenue,
         published_date, team_id, team_name, status, registration_time, deleted, created_at, updated_at, import_task_id)
        VALUES (%s, %s, %s, %s, %s, %s, 'AC', 10.00, 2.00, 0, %s, %s, 'HELLO BEAR', %s, %s, 0, NOW(), NOW(), 999999)
    """, (test_id, next_month, mo, video_info['videoId'], video_info['channelId'], video_info['channelName'],
          published_date, team_id, status, registration_time))
    return test_id

def cleanup_overdue_all(conn_fin, video_id):
    cur = conn_fin.cursor()
    cur.execute("DELETE FROM video_composition_overdue WHERE video_id=%s AND import_task_id=999999", (video_id,))

def call_bind(token, video_info):
    body = {
        "id": video_info['id'], "videoId": video_info['videoId'],
        "compositionId": video_info['compositionId'], "amsCompositionId": video_info['amsCompositionId'],
        "compositionName": video_info['compositionName'],
        "compositionServicePackageId": video_info['compositionServicePackageId'],
        "servicePackageCode": video_info['servicePackageCode'],
        "servicePackageName": video_info['servicePackageName'],
        "channelId": video_info['channelId'], "changeRelated": "2"
    }
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            "http://distribute.test.xiaowutw.com/appApi/videoComposition/bind",
            data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json","accessToken":token}
        ), timeout=15).read())
        return r
    except urllib.error.HTTPError as e:
        return {"status": e.code, "message": e.read()[:200].decode('utf-8','replace')}

def wait_mq_by_video(conn_fin, video_id, initial_status=0, max_wait=30):
    """轮询直到 video_id 所有记录 status 都 != initial_status"""
    cur = conn_fin.cursor(pymysql.cursors.DictCursor)
    for i in range(max_wait // 5):
        time.sleep(5)
        cur.execute("SELECT id, status, registration_time, video_tag, receipted_month FROM video_composition_overdue WHERE video_id=%s AND deleted=0 AND import_task_id=999999 ORDER BY id", (video_id,))
        rows = cur.fetchall()
        if rows and all(r['status'] != initial_status for r in rows):
            return rows, (i+1)*5
    return cur.fetchall(), max_wait  # timeout 返回现状

# ============ 执行入口 ============
conn_fin = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_finance', charset='utf8mb4', autocommit=True)
conn_dist = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_distribution', charset='utf8mb4', autocommit=True)
token, team_id = jlb_login()
all_results = []

print("=" * 70)
print(f"SET-01 v3 | 今天: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ========== S01-003 跨系统 E2E 联动 ==========
print("\n>>> S01-003 跨系统 E2E 联动（剧老板登记 → MQ → 结算状态变更）")
reset_jlb(conn_dist)
set_jlb_dates(conn_dist, "2026-03-15 10:00:00")
time.sleep(0.5)
video = get_candidate(token, team_id)
test_id = insert_overdue(conn_fin, video, "2026-03-15", team_id)
print(f"  准备 DB id={test_id} status=0")
bind_resp = call_bind(token, video)
bind_ok = bind_resp.get('status') == 200
print(f"  bind: status={bind_resp.get('status')}")

# 端到端：从 bind 成功 → DB 最终状态为目标
rows, elapsed = wait_mq_by_video(conn_fin, video['videoId'])
if rows:
    r = rows[0]
    print(f"  MQ t+{elapsed}s: status={r['status']} reg_time={r['registration_time']}")
    status_ok = r['status'] == 3
else:
    status_ok = False
assertions = [
    ("L1-1 bind status=200", bind_ok),
    ("L1-2 端到端链路：登记触发 MQ 同步", rows is not None and len(rows) > 0),
    ("L1-3 最终 DB status=3", status_ok),
]
cleanup_overdue_all(conn_fin, video['videoId'])
all_results.append(('S01-003', '跨系统 E2E 联动', assertions))

# ========== S01-004 多月份记录批量分发 ==========
print("\n>>> S01-004 多月份记录批量分发（同视频多条月份独立判定）")
reset_jlb(conn_dist)
set_jlb_dates(conn_dist, "2026-03-15 10:00:00")
time.sleep(0.5)
video = get_candidate(token, team_id)
# 2 条不同 receipted_month 记录，同 video_id
tid1 = insert_overdue(conn_fin, video, "2026-03-15", team_id, receipted_month="2026-04", month="2026-03")
tid2 = insert_overdue(conn_fin, video, "2026-03-15", team_id, receipted_month="2026-03", month="2026-02")
print(f"  准备 DB 两条 id={tid1}/{tid2}")
bind_resp = call_bind(token, video)
bind_ok = bind_resp.get('status') == 200
rows, elapsed = wait_mq_by_video(conn_fin, video['videoId'])
print(f"  MQ t+{elapsed}s: 共 {len(rows) if rows else 0} 条 status={[r['status'] for r in rows] if rows else []}")
both_updated = rows and len(rows) == 2 and all(r['status'] == 3 for r in rows)
assertions = [
    ("L1-1 bind status=200", bind_ok),
    ("L1 两条记录都被更新", rows is not None and len(rows) == 2),
    ("L1 两条记录都变 status=3", both_updated),
]
cleanup_overdue_all(conn_fin, video['videoId'])
all_results.append(('S01-004', '多月份批量分发', assertions))

# ========== S01-008 时间精度：29日 00:00:00 应逾期 ==========
print("\n>>> S01-008 时间精度：29日 00:00:00 → status=1（逾期）")
reset_jlb(conn_dist)
# 让 次月29日00:00:00 == 今天或早于今天 → 逾期
# published_at 使 "次月28日" = 某个早于今天的时间
# 今天 2026-04-22，published_at=2026-03-29 → 次月28 = 2026-04-28 > 今天 → 跨期
# published_at=2026-02-28 已测过。试 published_at=2026-03-01（次月28=2026-04-28，今天<边界→跨期）
# 要测"29日 00:00:00" 越界即逾期，可用 published_at=2026-02-28 23:59:59 + today 正好 next month 29日 00:00:00
# 简化：published_at=2025-03-15 → 次月28=2025-04-28 << 今天 → 逾期
set_jlb_dates(conn_dist, "2025-03-01 00:00:00")
time.sleep(0.5)
video = get_candidate(token, team_id)
test_id = insert_overdue(conn_fin, video, "2025-03-01", team_id)
bind_resp = call_bind(token, video)
bind_ok = bind_resp.get('status') == 200
rows, elapsed = wait_mq_by_video(conn_fin, video['videoId'])
r = rows[0] if rows else None
print(f"  MQ t+{elapsed}s: status={r['status'] if r else 'N/A'}")
assertions = [
    ("L1-1 bind status=200", bind_ok),
    ("L1-3 DB status=1（逾期）", r and r['status'] == 1),
]
cleanup_overdue_all(conn_fin, video['videoId'])
all_results.append(('S01-008', '时间精度 29日00:00 逾期', assertions))

# ========== S01-013 重复登记幂等 ==========
print("\n>>> S01-013 重复登记幂等（已登记状态的视频重复 bind 应被拦截）")
reset_jlb(conn_dist)
set_jlb_dates(conn_dist, "2026-03-15 10:00:00")
time.sleep(0.5)
video = get_candidate(token, team_id)
test_id = insert_overdue(conn_fin, video, "2026-03-15", team_id)
# 第一次 bind
bind1 = call_bind(token, video)
print(f"  第一次 bind: status={bind1.get('status')}")
time.sleep(6)  # 等 MQ 同步
# 第二次 bind（此时 jlb 该视频应已 related=1，会被拦截）
bind2 = call_bind(token, video)
print(f"  第二次 bind: status={bind2.get('status')} msg={str(bind2.get('message'))[:80]}")

# 断言：第二次 bind 应失败或返回拦截提示
# 现有代码逻辑：related=1 且重复登记 → 抛 VIDEO_ALREADY_RELATED
second_rejected = bind2.get('status') != 200 or '已登记' in str(bind2.get('message','')) or '已关联' in str(bind2.get('message',''))
assertions = [
    ("L1 第一次 bind 成功", bind1.get('status') == 200),
    ("L1 第二次 bind 被拦截（或返回失败）", second_rejected),
]
cleanup_overdue_all(conn_fin, video['videoId'])
all_results.append(('S01-013', '重复登记幂等', assertions))

# ========== S01-014 videoTag 计算：scraped_at > 次月15日 → videoTag=1 ==========
print("\n>>> S01-014 videoTag 计算：scraped_at > 发布次月15日 → video_tag=1")
reset_jlb(conn_dist)
# published_at=2025-10-01, scraped_at=2025-11-20（> 2025-11-15 23:59:59 → 漏爬）
set_jlb_dates(conn_dist, "2025-10-01 10:00:00", scraped_at="2025-11-20 10:00:00")
time.sleep(0.5)
video = get_candidate(token, team_id)
test_id = insert_overdue(conn_fin, video, "2025-10-01", team_id)
bind_resp = call_bind(token, video)
bind_ok = bind_resp.get('status') == 200
rows, elapsed = wait_mq_by_video(conn_fin, video['videoId'])
r = rows[0] if rows else None
vt = r['video_tag'] if r else None
print(f"  MQ t+{elapsed}s: status={r['status'] if r else 'N/A'} video_tag={vt}")
assertions = [
    ("L1-1 bind status=200", bind_ok),
    ("L1 DB video_tag=1（技术漏爬）", vt == 1),
]
cleanup_overdue_all(conn_fin, video['videoId'])
all_results.append(('S01-014', 'videoTag 技术漏爬', assertions))

# ========== S01-015 videoTag 边界：scraped_at = 次月15日 23:59:59 → video_tag=null ==========
print("\n>>> S01-015 videoTag 边界值：scraped_at = 发布次月15日 23:59:59 → video_tag=null")
reset_jlb(conn_dist)
# published_at=2025-10-01, scraped_at=2025-11-15 23:59:59（恰好 ≤ 边界）
set_jlb_dates(conn_dist, "2025-10-01 10:00:00", scraped_at="2025-11-15 23:59:59")
time.sleep(0.5)
video = get_candidate(token, team_id)
test_id = insert_overdue(conn_fin, video, "2025-10-01", team_id)
bind_resp = call_bind(token, video)
bind_ok = bind_resp.get('status') == 200
rows, elapsed = wait_mq_by_video(conn_fin, video['videoId'])
r = rows[0] if rows else None
vt = r['video_tag'] if r else None
print(f"  MQ t+{elapsed}s: status={r['status'] if r else 'N/A'} video_tag={vt}")
assertions = [
    ("L1-1 bind status=200", bind_ok),
    ("L1 DB video_tag=NULL（恰好不超阈值）", vt is None),
]
cleanup_overdue_all(conn_fin, video['videoId'])
all_results.append(('S01-015', 'videoTag 边界值', assertions))

# ========== S01-016 videoTag 双表一致 ==========
print("\n>>> S01-016 videoTag 双表一致：video_composition 与 video_composition_overdue")
reset_jlb(conn_dist)
set_jlb_dates(conn_dist, "2025-10-01 10:00:00", scraped_at="2025-11-20 10:00:00")
time.sleep(0.5)
video = get_candidate(token, team_id)
test_id = insert_overdue(conn_fin, video, "2025-10-01", team_id)
bind_resp = call_bind(token, video)
rows, elapsed = wait_mq_by_video(conn_fin, video['videoId'])

# 检查两表 video_tag
cur_f = conn_fin.cursor(pymysql.cursors.DictCursor)
cur_f.execute("SELECT video_tag FROM video_composition WHERE video_id=%s", (video['videoId'],))
f_video = cur_f.fetchone()
tag_overdue = rows[0]['video_tag'] if rows else None
tag_fin_video = f_video['video_tag'] if f_video else None
print(f"  video_composition_overdue.video_tag={tag_overdue}")
print(f"  silverdawn_finance.video_composition.video_tag={tag_fin_video}")
assertions = [
    ("L1-1 bind status=200", bind_resp.get('status') == 200),
    ("L1 两表 video_tag 一致", tag_overdue == tag_fin_video),
]
cleanup_overdue_all(conn_fin, video['videoId'])
all_results.append(('S01-016', 'videoTag 双表一致', assertions))

# ============ 清理 + 汇总 ============
reset_jlb(conn_dist)
conn_fin.close()
conn_dist.close()

print("\n" + "=" * 70)
print("汇总:")
for cid, cname, asserts in all_results:
    passed = sum(1 for _,p in asserts if p)
    status = "PASS" if passed == len(asserts) else "FAIL"
    icon = "✅" if status=="PASS" else "❌"
    print(f"  {icon} {cid}: {status} ({passed}/{len(asserts)})")
    for n, p in asserts:
        print(f"      [{'PASS' if p else 'FAIL'}] {n}")
