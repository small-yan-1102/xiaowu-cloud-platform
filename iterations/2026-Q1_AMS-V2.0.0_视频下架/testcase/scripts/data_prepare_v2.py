"""通过 SSO 回调获取 AMS session + DB数据准备"""
import pymysql
import requests
import json

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

def try_sso_callback():
    """尝试 SSO 回调流程获取 AMS session"""
    session = requests.Session()
    
    # Step 1: SSO 登录
    r1 = session.post(
        'http://172.16.24.200:8011/sso/doLogin?name=15057199668&pwd=1111',
        headers={'Accept': 'application/json', 'Content-Length': '0'}
    )
    data = r1.json()['data']
    sso_token = data['token']
    jwt_token = data['accessToken']
    print(f'SSO token: {sso_token}')
    print(f'JWT token: {jwt_token[:50]}...')
    
    # Step 2: 尝试 AMS 登录回调
    login_urls = [
        f'http://172.16.24.200:8024/login?accessToken={jwt_token}&back=http://172.16.24.200:8024',
        f'http://172.16.24.200:8024/login?token={sso_token}',
        f'http://172.16.24.200:8024/api/login?accessToken={jwt_token}',
    ]
    
    for url in login_urls:
        print(f'\nTrying: {url[:80]}...')
        r = session.get(url, allow_redirects=False, timeout=10)
        print(f'  Status: {r.status_code}')
        print(f'  Headers: {dict(r.headers)}'.replace(', ', ',\n    ')[:500])
        if r.status_code in [301, 302]:
            print(f'  Redirect: {r.headers.get("Location", "none")}')
        print(f'  Cookies: {dict(session.cookies)}')
    
    # Step 3: 用 session 调 API（如果有 cookie）
    if session.cookies:
        print('\n=== 有 cookies，尝试 API 调用 ===')
        r3 = session.get('http://172.16.24.200:8024/api/video-takedown/task/list',
                        headers={'Accept': 'application/json'}, timeout=10)
        print(f'Status: {r3.status_code}')
        try:
            print(f'Response: {json.dumps(r3.json(), ensure_ascii=False)[:300]}')
        except:
            print(f'Response: {r3.text[:300]}')
    
    return sso_token, jwt_token

def prepare_data_via_db():
    """通过 DB 直接准备测试数据"""
    conn = pymysql.connect(**DB, database='silverdawn_ams')
    c = conn.cursor(pymysql.cursors.DictCursor)
    
    # 查看当前 PENDING_REVIEW 任务
    c.execute("SELECT id, code, status, process_method, deadline_date "
              "FROM video_takedown_task WHERE status='PENDING_REVIEW' ORDER BY code")
    pending = c.fetchall()
    print(f'\n=== DB 数据准备 ===')
    print(f'当前 PENDING_REVIEW 任务: {len(pending)} 条')
    for t in pending:
        print(f"  {t['code']} (id={t['id']}): deadline={t['deadline_date']}")
    
    if len(pending) >= 4:
        # 审批前3条 → PENDING_PROCESS (不同 deadline 用于排序测试)
        approve_tasks = pending[:3]
        reject_task = pending[3]
        
        print(f'\n--- 审批 3 条任务 → PENDING_PROCESS ---')
        for i, t in enumerate(approve_tasks):
            # 修改 deadline 使其不同，用于排序验证
            deadlines = ['2026-04-05', '2026-04-03', '2026-04-07']
            priorities = [1, 2, 1]  # 不同优先级用于 VT-033
            
            c.execute(
                "UPDATE video_takedown_task SET "
                "status='PENDING_PROCESS', "
                "deadline_date=%s, "
                "auditor_id='17242367637015560', "
                "audit_opinion='AI测试数据准备-自动审批通过', "
                "audit_time=NOW() "
                "WHERE id=%s AND status='PENDING_REVIEW'",
                (deadlines[i], t['id'])
            )
            print(f"  {t['code']} → PENDING_PROCESS (deadline={deadlines[i]})")
        
        # 拒绝1条 → REVIEW_REJECTED
        print(f'\n--- 拒绝 1 条任务 → REVIEW_REJECTED ---')
        c.execute(
            "UPDATE video_takedown_task SET "
            "status='REVIEW_REJECTED', "
            "auditor_id='17242367637015560', "
            "audit_opinion='AI测试数据准备-审核拒绝测试', "
            "audit_time=NOW() "
            "WHERE id=%s AND status='PENDING_REVIEW'",
            (reject_task['id'],)
        )
        print(f"  {reject_task['code']} → REVIEW_REJECTED")
        
        conn.commit()
        print('\n--- DB 更新已提交 ---')
    
    # 验证更新结果
    c.execute("SELECT code, status, deadline_date, audit_opinion "
              "FROM video_takedown_task ORDER BY code")
    print('\n=== 更新后状态 ===')
    for t in c.fetchall():
        print(f"  {t['code']:15s} | {t['status']:20s} | deadline={t['deadline_date']} | {(t['audit_opinion'] or '')[:30]}")
    
    # 各状态汇总
    c.execute("SELECT status, COUNT(*) as cnt FROM video_takedown_task GROUP BY status ORDER BY cnt DESC")
    print('\n=== 状态汇总 ===')
    for t in c.fetchall():
        print(f"  {t['status']:20s} | {t['cnt']}")
    
    conn.close()

def main():
    print('=== Part 1: SSO 回调测试 ===')
    try_sso_callback()
    
    print('\n' + '='*60)
    print('=== Part 2: DB 数据准备 ===')
    prepare_data_via_db()
    
    print('\n=== All Done ===')

if __name__ == '__main__':
    main()
