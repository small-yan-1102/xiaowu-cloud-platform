"""S01-011 深度验证：并发登记是否真的产生双登记（TOCTOU 缺陷复现/确认）"""
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

def reset_jlb(conn_dist):
    conn_dist.cursor().execute("""
        UPDATE video_composition SET related='2', related_at=NULL, change_related_at=NULL, change_related_count=0,
            published_at='2026-03-10 06:40:51', published_date='2026-03-10', scraped_at='2026-03-10 07:30:25'
        WHERE video_id=%s
    """, (BASE_VIDEO_ID,))

def snapshot_jlb(conn_dist):
    cur = conn_dist.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT related, related_at, pipeline_id, composition_id, updated_at, version
        FROM video_composition WHERE video_id=%s
    """, (BASE_VIDEO_ID,))
    return cur.fetchone()

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
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            "http://distribute.test.xiaowutw.com/appApi/videoComposition/bind",
            data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json","accessToken":token}
        ), timeout=30).read())
        return r
    except urllib.error.HTTPError as e:
        return {"status": e.code, "message": e.read()[:300].decode('utf-8','replace')}

# ============ 主流程 ============
conn_dist = pymysql.connect(host='172.16.24.61', port=3306, user='xiaowu_db', password='}C7n%7Wklq6P', database='silverdawn_distribution', charset='utf8mb4', autocommit=True)
token, team_id = jlb_login()

print("=" * 70)
print(f"S01-011 深度验证：并发登记 TOCTOU 缺陷")
print("=" * 70)

# 连跑 3 轮，观察行为是否稳定
TRIALS = 3
stats = []

for trial in range(1, TRIALS + 1):
    print(f"\n{'─' * 50}")
    print(f"【第 {trial} 轮】")
    print(f"{'─' * 50}")

    # 重置
    reset_jlb(conn_dist)
    time.sleep(0.5)
    video = get_candidate(token, team_id)
    if not video:
        print("  ✗ 无候选，退出")
        break

    pre = snapshot_jlb(conn_dist)
    print(f"  重置前: related={pre['related']} related_at={pre['related_at']} pipeline={pre['pipeline_id']}")

    # Barrier 确保两线程"同时"调
    results = [None, None]
    barrier = threading.Barrier(2)
    def worker(idx):
        barrier.wait()
        results[idx] = call_bind(token, video)

    t1 = threading.Thread(target=worker, args=(0,))
    t2 = threading.Thread(target=worker, args=(1,))
    t1.start(); t2.start()
    t1.join(); t2.join()

    print(f"  线程 0: status={results[0].get('status')} msg={str(results[0].get('message'))[:50]}")
    print(f"  线程 1: status={results[1].get('status')} msg={str(results[1].get('message'))[:50]}")

    # 事后快照
    time.sleep(1)
    post = snapshot_jlb(conn_dist)
    print(f"  最终 DB: related={post['related']} related_at={post['related_at']} pipeline={post['pipeline_id']} version={post['version']}")

    success_count = sum(1 for r in results if r.get('status') == 200)
    rejected = [r for r in results if r.get('status') != 200]
    stats.append({
        'trial': trial,
        'success_count': success_count,
        'rejected_msgs': [r.get('message') for r in rejected],
        'final_related': post['related'],
        'final_pipeline': post['pipeline_id'],
    })

reset_jlb(conn_dist)
conn_dist.close()

# ============ 汇总 ============
print("\n" + "=" * 70)
print("汇总（3 轮并发测试）:")
print("=" * 70)
for s in stats:
    icon = "🐛" if s['success_count'] == 2 else ("✅" if s['success_count'] == 1 else "⚠️")
    print(f"  {icon} 第{s['trial']}轮: success={s['success_count']} rejected_msgs={s['rejected_msgs']}")
    print(f"         final related={s['final_related']} pipeline={s['final_pipeline']}")

both_success = sum(1 for s in stats if s['success_count'] == 2)
one_success = sum(1 for s in stats if s['success_count'] == 1)
print(f"\n统计: {both_success}/{TRIALS} 轮两次都成功（TOCTOU 缺陷），{one_success}/{TRIALS} 轮仅一次成功")

if both_success == 0:
    print("\n✅ 所有轮次都仅一个请求成功 → 修复生效")
elif both_success == TRIALS:
    print("\n🐛 所有轮次两个请求都成功 → 缺陷仍存在")
else:
    print(f"\n⚠️ 结果不稳定（{both_success}/{TRIALS} 触发缺陷）→ 缺陷存在但非必现")
