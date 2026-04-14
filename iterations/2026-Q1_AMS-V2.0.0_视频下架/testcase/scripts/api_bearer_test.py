"""测试 Bearer 前缀 API 认证 + 诊断 BY_VIDEO_ID"""
import requests
import json
import pymysql

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

def test_bearer_auth():
    """使用 Bearer 前缀测试 AMS API 认证"""
    # SSO 登录获取 token
    r = requests.post(
        'http://172.16.24.200:8011/sso/doLogin?name=15057199668&pwd=1111',
        headers={'Accept': 'application/json', 'Content-Length': '0'}
    )
    data = r.json()['data']
    jwt_token = data['accessToken']
    sso_token = data['token']
    print(f'JWT token: {jwt_token[:60]}...')
    print(f'SSO token: {sso_token}')

    # 尝试不同 Bearer 前缀组合
    test_cases = [
        ('Authorization: Bearer JWT',   {'Authorization': f'Bearer {jwt_token}'}),
        ('accessToken: Bearer JWT',      {'accessToken': f'Bearer {jwt_token}'}),
        ('Authorization: Bearer SSO',    {'Authorization': f'Bearer {sso_token}'}),
        ('accessToken: Bearer SSO',      {'accessToken': f'Bearer {sso_token}'}),
        ('token: Bearer JWT',            {'token': f'Bearer {jwt_token}'}),
        ('Authorization + accessToken',  {'Authorization': f'Bearer {jwt_token}', 'accessToken': jwt_token}),
    ]
    
    api_url = 'http://172.16.24.200:8024/api/video-takedown/task/list'
    
    for desc, headers in test_cases:
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        print(f'\n--- {desc} ---')
        try:
            r = requests.get(api_url, headers=headers, timeout=10)
            print(f'  Status HTTP: {r.status_code}')
            resp = r.json()
            print(f'  Status API: {resp.get("status")}')
            print(f'  Message: {resp.get("message", "")[:100]}')
            if resp.get('status') == 200:
                print(f'  DATA: {json.dumps(resp.get("data"), ensure_ascii=False)[:300]}')
                return headers  # 返回成功的 headers
        except Exception as e:
            print(f'  Error: {e}')
    
    # 也试一下 POST 方式
    print('\n\n=== 尝试 POST 方式 ===')
    for desc, headers in test_cases[:2]:
        headers['Accept'] = 'application/json'
        headers['Content-Type'] = 'application/json'
        print(f'\n--- POST {desc} ---')
        try:
            r = requests.post(api_url, headers=headers, json={}, timeout=10)
            print(f'  Status HTTP: {r.status_code}')
            resp = r.json()
            print(f'  Status API: {resp.get("status")}')
            print(f'  Message: {resp.get("message", "")[:100]}')
            if resp.get('status') == 200:
                print(f'  DATA: {json.dumps(resp.get("data"), ensure_ascii=False)[:300]}')
                return headers
        except Exception as e:
            print(f'  Error: {e}')
    
    return None


def diagnose_by_video_id():
    """诊断 BY_VIDEO_ID 创建的任务"""
    conn = pymysql.connect(**DB, database='silverdawn_ams')
    c = conn.cursor(pymysql.cursors.DictCursor)
    
    print('\n\n' + '='*60)
    print('=== BY_VIDEO_ID 任务诊断 ===')
    
    # V2603310006 - CREATING 卡住
    c.execute("""
        SELECT t.id, t.code, t.status, t.create_type, t.process_method,
               t.task_source, t.team_id, t.deadline_date,
               t.create_fail_reason, t.created_at, t.updated_at
        FROM video_takedown_task t 
        WHERE t.code IN ('V2603310006', 'V2603300002')
    """)
    for t in c.fetchall():
        print(f"\n  Code: {t['code']}")
        print(f"  Status: {t['status']}")
        print(f"  CreateType: {t['create_type']}")
        print(f"  ProcessMethod: {t['process_method']}")
        print(f"  TaskSource: {t['task_source']}")
        print(f"  TeamID: {t['team_id']}")
        print(f"  FailReason: {t['create_fail_reason']}")
        print(f"  Created: {t['created_at']}")
        print(f"  Updated: {t['updated_at']}")
    
    # 查看这两个任务的 detail
    c.execute("""
        SELECT td.id, td.task_id, td.video_id, td.video_title, td.video_status,
               td.composition_name, td.channel_name
        FROM video_takedown_task_detail td
        JOIN video_takedown_task t ON td.task_id = t.id
        WHERE t.code IN ('V2603310006', 'V2603300002')
        LIMIT 20
    """)
    details = c.fetchall()
    print(f'\n=== BY_VIDEO_ID 任务明细: {len(details)} 条 ===')
    for d in details:
        print(f"  task_id={d['task_id']}, video={d['video_title'][:20] if d['video_title'] else 'N/A'}, "
              f"status={d['video_status']}, channel={d['channel_name']}")
    
    # 检查是否有异步任务记录
    print('\n=== 检查可能的异步任务相关表 ===')
    try:
        c.execute("SHOW TABLES LIKE '%async%'")
        tables = c.fetchall()
        print(f"  async 相关表: {tables}")
    except Exception as e:
        print(f"  查询失败: {e}")
    
    try:
        c.execute("SHOW TABLES LIKE '%job%'")
        tables = c.fetchall()
        print(f"  job 相关表: {tables}")
    except Exception as e:
        print(f"  查询失败: {e}")
    
    # 尝试修复 V2603310006: 将 CREATING → CREATE_FAILED 
    # 以便可以重新创建，或直接标记为诊断完成
    print('\n=== BY_VIDEO_ID 修复方案分析 ===')
    print('  V2603310006 (CREATING): 异步验证卡住，pipeline 无法找到匹配的分发记录')
    print('  V2603300002 (CREATE_FAILED): 创建失败，原因未记录')
    print('  方案: 直接通过 DB 构造一条 BY_VIDEO_ID 类型的 PENDING_REVIEW 任务')
    
    # 查看是否有 DISTRIBUTOR 来源的已成功任务可以参考
    c.execute("""
        SELECT t.code, t.status, t.create_type, t.task_source, t.team_id, t.process_method
        FROM video_takedown_task t
        WHERE t.task_source = 'DISTRIBUTOR' AND t.status = 'COMPLETED'
    """)
    ref = c.fetchall()
    print(f'\n=== DISTRIBUTOR 成功参考任务: {len(ref)} 条 ===')
    for r in ref:
        print(f"  {r['code']} | {r['status']} | {r['create_type']} | {r['process_method']}")
    
    conn.close()


if __name__ == '__main__':
    working_headers = test_bearer_auth()
    if working_headers:
        print(f'\n=== API 认证成功! Headers: {working_headers} ===')
    else:
        print('\n=== 所有 Bearer 组合均失败 ===')
    
    diagnose_by_video_id()
