"""SET-01 批量执行脚本 v2 — 修复逾期用例数据准备"""
import urllib.request, urllib.error, json, pymysql, sys, time
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')

BASE_VIDEO_ID = '_ibqnYAR77c'
ORIGINAL_PUBLISHED = '2026-03-10 06:40:51'  # 原始 published_at
ORIGINAL_SCRAPED = '2026-03-10 07:30:25'    # 原始 scraped_at

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
    """完整重置：related=2 + 恢复 published_at/scraped_at 原值"""
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
    """临时改 剧老板 published_at/scraped_at（测试数据准备）"""
    cur = conn_dist.cursor()
    sc = scraped_at or published_at  # 默认 scraped_at = published_at（当天抓取）
    cur.execute("""
        UPDATE video_composition
        SET published_at=%s, published_date=%s, scraped_at=%s
        WHERE video_id=%s
    """, (published_at, published_at[:10], sc, BASE_VIDEO_ID))

def insert_overdue(conn_fin, video_info, published_date, team_id):
    cur = conn_fin.cursor()
    test_id = int(time.time() * 1000000)
    next_month = (datetime.strptime(published_date, '%Y-%m-%d') + timedelta(days=40)).strftime('%Y-%m')
    cur.execute("""
        INSERT INTO video_composition_overdue
        (id, receipted_month, month, video_id, channel_id, channel_name, cms, revenue, us_revenue, sg_revenue,
         published_date, team_id, team_name, status, deleted, created_at, updated_at, import_task_id)
        VALUES (%s, %s, %s, %s, %s, %s, 'AC', 10.00, 2.00, 0, %s, %s, 'HELLO BEAR', 0, 0, NOW(), NOW(), 999999)
    """, (test_id, next_month, published_date[:7],
          video_info['videoId'], video_info['channelId'], video_info['channelName'],
          published_date, team_id))
    return test_id

def cleanup_overdue(conn_fin, test_id):
    cur = conn_fin.cursor()
    cur.execute("DELETE FROM video_composition_overdue WHERE id=%s AND import_task_id=999999", (test_id,))

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

def wait_mq(conn_fin, test_id, max_wait=30):
    cur = conn_fin.cursor(pymysql.cursors.DictCursor)
    for i in range(max_wait // 5):
        time.sleep(5)
        cur.execute("SELECT status, registration_time, video_tag FROM video_composition_overdue WHERE id=%s", (test_id,))
        r = cur.fetchone()
        if r and r['status'] != 0:
            return r, (i+1) * 5
    return None, max_wait

# ============ 用例定义 ============
# 关键发现：结算端判定的 publishedAt 来自 剧老板 MQ 消息，所以测试数据要改 video_composition.published_at
# 今天: 2026-04-22
cases = [
    {"id": "S01-002", "name": "逾期登记分发",
     "jlb_published_at": "2025-10-01 10:00:00",
     "overdue_published_date": "2025-10-01",
     "expect_status": 1,
     "note": "published_at=2025-10-01 → 次月28=2025-11-28 << 今天 → 逾期"},
    {"id": "S01-005", "name": "边界值：恰好满足跨期正常",
     "jlb_published_at": "2026-03-15 10:00:00",
     "overdue_published_date": "2026-03-15",
     "expect_status": 3,
     "note": "published_at=2026-03-15 → 次月28=2026-04-28 > 今天 → 跨期正常"},
    {"id": "S01-006", "name": "边界值：刚过跨期正常阈值",
     "jlb_published_at": "2026-02-28 10:00:00",
     "overdue_published_date": "2026-02-28",
     "expect_status": 1,
     "note": "published_at=2026-02-28 → 次月28=2026-03-28 < 今天 → 逾期"},
    {"id": "S01-007", "name": "时间精度：次月28日 23:59:59（最后一秒）",
     "jlb_published_at": "2026-03-28 23:59:59",  # 让次月28=2026-04-28，今天<边界
     "overdue_published_date": "2026-03-28",
     "expect_status": 3,
     "note": "published_at 使次月28 23:59:59 = 2026-04-28 23:59:59 > 今天 → 跨期正常"},
    {"id": "S01-009", "name": "无匹配记录：结算系统无该视频 → 登记正常完成",
     "jlb_published_at": "2026-03-15 10:00:00",
     "skip_db_insert": True, "expect_no_db_change": True},
]

# ============ 执行 ============
conn_fin = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_finance', charset='utf8mb4', autocommit=True)
conn_dist = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_distribution', charset='utf8mb4', autocommit=True)

# 先读当前原值保存
cur = conn_dist.cursor(pymysql.cursors.DictCursor)
cur.execute("SELECT published_at, published_date, scraped_at FROM video_composition WHERE video_id=%s", (BASE_VIDEO_ID,))
orig = cur.fetchone()
print(f"原始值: published_at={orig['published_at']} scraped_at={orig['scraped_at']}")

token, team_id = jlb_login()
print("=" * 70)
print(f"SET-01 批量执行 v2 | 今天: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

results = []
for case in cases:
    print(f"\n>>> {case['id']} {case['name']}")
    if case.get('note'): print(f"  [{case['note']}]")

    # 1. 重置剧老板（恢复原值）
    reset_jlb(conn_dist, restore_publish=True)
    # 2. 设置本用例的 published_at
    if case.get('jlb_published_at'):
        set_jlb_dates(conn_dist, case['jlb_published_at'])
        print(f"  设置 jlb.published_at={case['jlb_published_at']}")
    time.sleep(0.5)

    # 3. 重新获取候选
    video = get_candidate(token, team_id)
    if not video:
        print(f"  FAIL: 无候选")
        results.append((case['id'], case['name'], 'FAIL', [('获取候选', False)]))
        continue

    # 4. DB 准备
    test_id = None
    if not case.get('skip_db_insert'):
        test_id = insert_overdue(conn_fin, video, case['overdue_published_date'], team_id)
        print(f"  DB INSERT id={test_id} published_date={case['overdue_published_date']}")
    else:
        print(f"  跳过 DB INSERT")

    # 5. bind
    bind_resp = call_bind(token, video)
    bind_ok = bind_resp.get('status') == 200
    print(f"  bind: status={bind_resp.get('status')} msg={str(bind_resp.get('message'))[:60]}")

    assertions = [("L1-1 bind status=200", bind_ok)]

    if case.get('expect_status'):
        rec, elapsed = wait_mq(conn_fin, test_id)
        if rec:
            print(f"  MQ t+{elapsed}s: status={rec['status']} reg_time={rec['registration_time']}")
            assertions.append((f"L1-3 DB status={case['expect_status']}", rec['status'] == case['expect_status']))
            reg_ok = rec['registration_time'] and abs((datetime.now() - rec['registration_time']).total_seconds()) < 300
            assertions.append(("L1-3b registration_time ±5min", reg_ok))
        else:
            print(f"  MQ 超时")
            assertions.append((f"L1-3 DB status={case['expect_status']}", False))
            assertions.append(("L1-3b registration_time ±5min", False))
    elif case.get('expect_no_db_change'):
        cur_f = conn_fin.cursor(pymysql.cursors.DictCursor)
        cur_f.execute("SELECT COUNT(*) as c FROM video_composition_overdue WHERE video_id=%s AND deleted=0", (video['videoId'],))
        db_cnt = cur_f.fetchone()['c']
        print(f"  DB 记录数: {db_cnt}")
        assertions.append(("L1 DB 无新增记录", db_cnt == 0))
        time.sleep(6)
        cur_f.execute("SELECT COUNT(*) as c FROM video_composition_overdue WHERE video_id=%s AND deleted=0", (video['videoId'],))
        db_cnt2 = cur_f.fetchone()['c']
        assertions.append(("L1 等6s后 DB 仍无新增", db_cnt2 == 0))

    if test_id:
        cleanup_overdue(conn_fin, test_id)

    passed = sum(1 for _,p in assertions if p)
    overall = "PASS" if passed == len(assertions) else "FAIL"
    print(f"  => {overall} ({passed}/{len(assertions)})")
    for n, p in assertions:
        print(f"    [{'PASS' if p else 'FAIL'}] {n}")
    results.append((case['id'], case['name'], overall, assertions))

# 最后恢复原值
reset_jlb(conn_dist, restore_publish=True)
print(f"\n✓ 恢复剧老板 video_composition 原值 (published_at={orig['published_at']})")

conn_fin.close()
conn_dist.close()

print("\n" + "=" * 70)
print("汇总:")
for r in results:
    icon = "✅" if r[2]=="PASS" else "❌"
    print(f"  {icon} {r[0]} {r[1]}: {r[2]}")
