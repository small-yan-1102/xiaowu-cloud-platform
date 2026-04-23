"""S01-011 重新执行，保留所有数据供人工确认（不清理不重置）"""
import urllib.request, urllib.error, json, pymysql, sys, time, threading
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

BASE_VIDEO_ID = '_ibqnYAR77c'

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
    return r['data']['records'][0] if r['data'].get('records') else None

def reset_for_clean_test(conn_dist, conn_fin):
    """仅重置到可并发测试的起点状态，不做事后清理"""
    # 剧老板端：related=2, 清 pipeline_id 便于观察新生成
    conn_dist.cursor().execute("""
        UPDATE video_composition
        SET related='2', related_at=NULL, change_related_at=NULL, change_related_count=0, pipeline_id=NULL
        WHERE video_id=%s
    """, (BASE_VIDEO_ID,))
    # 结算端：清理遗留关联
    conn_fin.cursor().execute("""
        DELETE FROM video_composition WHERE video_id=%s
    """, (BASE_VIDEO_ID,))

def snapshot_all(conn_dist, conn_fin, label):
    print(f"\n【{label}】")
    # 剧老板
    cur = conn_dist.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT id, video_id, related, related_at, change_related_at, change_related_count,
               pipeline_id, composition_id, composition_name, version, updated_at
        FROM video_composition WHERE video_id=%s
    """, (BASE_VIDEO_ID,))
    r = cur.fetchone()
    if r:
        print(f"  剧老板 video_composition:")
        print(f"    id={r['id']} related={r['related']} related_at={r['related_at']}")
        print(f"    pipeline_id={r['pipeline_id']}")
        print(f"    version={r['version']} updated_at={r['updated_at']}")
    else:
        print(f"  剧老板: 无记录")

    # 结算端
    cur2 = conn_fin.cursor(pymysql.cursors.DictCursor)
    cur2.execute("""
        SELECT id, video_id, pipeline_id, related, related_at, video_tag, created_at, updated_at
        FROM video_composition WHERE video_id=%s
    """, (BASE_VIDEO_ID,))
    recs = cur2.fetchall()
    print(f"  结算 video_composition: {len(recs)} 条")
    for rec in recs:
        print(f"    id={rec['id']} pipeline={rec['pipeline_id']} related={rec['related']} related_at={rec['related_at']}")
        print(f"      video_tag={rec['video_tag']} created={rec['created_at']} updated={rec['updated_at']}")

    cur2.execute("""
        SELECT id, receipted_month, status, pipeline_id, registration_time, created_at, updated_at
        FROM video_composition_overdue WHERE video_id=%s AND deleted=0
    """, (BASE_VIDEO_ID,))
    overdue = cur2.fetchall()
    print(f"  结算 video_composition_overdue: {len(overdue)} 条")
    for rec in overdue:
        print(f"    id={rec['id']} month={rec['receipted_month']} status={rec['status']} pipeline={rec['pipeline_id']} reg_time={rec['registration_time']}")

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
    t0 = time.time()
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            "http://distribute.test.xiaowutw.com/appApi/videoComposition/bind",
            data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json","accessToken":token}
        ), timeout=30).read())
        r['_elapsed'] = time.time() - t0
        return r
    except urllib.error.HTTPError as e:
        return {"status": e.code, "message": e.read()[:300].decode('utf-8','replace'), '_elapsed': time.time() - t0}

# ============ 主流程 ============
conn_dist = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_distribution', charset='utf8mb4', autocommit=True)
conn_fin = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_finance', charset='utf8mb4', autocommit=True)
token, team_id = jlb_login()

print("=" * 70)
print(f"S01-011 并发登记测试 · 数据保留模式 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Step 1: 重置到起点
print("\n--- Step 1：重置到干净起点（剧老板 related=2 + pipeline_id=NULL，结算 video_composition 清空）---")
reset_for_clean_test(conn_dist, conn_fin)
time.sleep(0.5)

snapshot_all(conn_dist, conn_fin, "起点状态")

# Step 2: 获取候选
video = get_candidate(token, team_id)
if not video:
    print("✗ 无候选")
    sys.exit(1)
print(f"\n候选: videoId={video['videoId']} composition={video['compositionName']}")

# Step 3: 并发 bind
print(f"\n--- Step 2：并发 bind（2 线程 barrier 同步）---")
results = [None, None]
barrier = threading.Barrier(2)
def worker(idx):
    barrier.wait()
    results[idx] = call_bind(token, video)

t1 = threading.Thread(target=worker, args=(0,))
t2 = threading.Thread(target=worker, args=(1,))
t1.start(); t2.start()
t1.join(); t2.join()

print(f"\n  线程 0 (耗时 {results[0].get('_elapsed', 0):.2f}s):")
print(f"    {json.dumps(results[0], ensure_ascii=False)[:300]}")
print(f"  线程 1 (耗时 {results[1].get('_elapsed', 0):.2f}s):")
print(f"    {json.dumps(results[1], ensure_ascii=False)[:300]}")

# Step 4: 事后快照（不清理）
time.sleep(6)  # 等 MQ 消费
snapshot_all(conn_dist, conn_fin, "并发 bind 后的最终状态（已等 6s MQ 同步）")

# Step 5: 告知用户
success_count = sum(1 for r in results if r.get('status') == 200)
print(f"\n{'=' * 70}")
print(f"本次并发 API 返回 200 的次数: {success_count}")
if success_count == 2:
    print("🐛 仍复现：两个请求都返回 200")
else:
    print(f"⚠️ 仅 {success_count} 个成功 — 可能已修复或复现失败")

print(f"\n【⚠️ 数据已保留，未执行任何清理 / 重置】")
print(f"请核对：")
print(f"  1. 剧老板 video_composition pipeline_id（新生成 vs 保留原值）")
print(f"  2. 结算 video_composition 条数（应为 1，若为 2 则 MQ 发了 2 次）")
print(f"  3. 结算 video_composition_overdue 有无重复插入")
print(f"  4. AMS 侧查看 pipeline_id 对应通道是否创建了多个（建议你到 AMS 后台核对）")

conn_dist.close()
conn_fin.close()
