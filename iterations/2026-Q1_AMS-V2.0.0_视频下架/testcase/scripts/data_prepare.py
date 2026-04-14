"""准备测试数据: 审批/拒绝 PENDING_REVIEW 任务 + 诊断 BY_VIDEO_ID"""
import pymysql
import requests
import json
import time

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

AMS_BASE = 'http://172.16.24.200:8024'
SSO_LOGIN = 'http://172.16.24.200:8011/sso/doLogin'

def get_token():
    """获取 SSO token"""
    r = requests.post(f'{SSO_LOGIN}?name=15057199668&pwd=1111',
                      headers={'Accept': 'application/json', 'Content-Length': '0'})
    data = r.json()
    if data.get('code') == 200:
        token = data['data']['accessToken']
        print(f'Token obtained: {token[:30]}...')
        return token
    else:
        print(f'Login failed: {data}')
        return None

def api_call(method, path, token, body=None):
    """调用 AMS API"""
    url = f'{AMS_BASE}{path}'
    headers = {
        'accessToken': token,
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
    }
    print(f'\n>>> {method} {url}')
    if body:
        print(f'    Body: {json.dumps(body, ensure_ascii=False)[:200]}')
    try:
        if method == 'POST':
            r = requests.post(url, headers=headers, json=body, timeout=15)
        elif method == 'GET':
            r = requests.get(url, headers=headers, timeout=15)
        elif method == 'PUT':
            r = requests.put(url, headers=headers, json=body, timeout=15)
        print(f'    Status: {r.status_code}')
        # 尝试解析 JSON
        try:
            resp = r.json()
            print(f'    Response: {json.dumps(resp, ensure_ascii=False)[:300]}')
            return resp
        except:
            print(f'    Response (text): {r.text[:300]}')
            return r.text
    except Exception as e:
        print(f'    ERROR: {e}')
        return None

def main():
    # Step 1: 获取 token
    print('=== Step 1: 获取 Token ===')
    token = get_token()
    if not token:
        return

    # Step 2: 查询 PENDING_REVIEW 任务的 ID
    print('\n=== Step 2: 查询 PENDING_REVIEW 任务 ===')
    conn = pymysql.connect(**DB, database='silverdawn_ams')
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute("SELECT id, code, process_method, takedown_reason, deadline_date "
              "FROM video_takedown_task WHERE status='PENDING_REVIEW' ORDER BY code")
    pending_tasks = c.fetchall()
    for t in pending_tasks:
        print(f"  {t['code']} (id={t['id']}): {t['process_method']} | {t['takedown_reason']} | deadline={t['deadline_date']}")

    # Step 3: 诊断 BY_VIDEO_ID CREATING 任务
    print('\n=== Step 3: 诊断 BY_VIDEO_ID 任务 ===')
    c.execute("SELECT id, code, status, create_fail_reason, created_at, updated_at "
              "FROM video_takedown_task WHERE create_type='BY_VIDEO_ID'")
    vid_tasks = c.fetchall()
    for t in vid_tasks:
        print(f"  {t['code']}: status={t['status']} | fail={t['create_fail_reason']} | "
              f"created={t['created_at']} | updated={t['updated_at']}")
    conn.close()

    # Step 4: 尝试不同的 API 路径查找正确的审批接口
    print('\n=== Step 4: 探测 API 路径 ===')
    
    # 尝试常见的 API 路径模式
    test_paths = [
        '/api/video-takedown/task/list',
        '/video-takedown/task/list', 
        '/ams/video-takedown/task/list',
        '/api/ams/video-takedown/task/list',
    ]
    for path in test_paths:
        resp = api_call('GET', path, token)
        if resp and isinstance(resp, dict) and resp.get('code') in [200, 0]:
            print(f'    *** FOUND WORKING PATH: {path} ***')
            break

    # Step 5: 尝试审批接口
    if pending_tasks:
        task_id = pending_tasks[0]['id']
        task_code = pending_tasks[0]['code']
        print(f'\n=== Step 5: 尝试审批 {task_code} (id={task_id}) ===')
        
        audit_paths = [
            f'/api/video-takedown/task/{task_id}/audit',
            f'/video-takedown/task/{task_id}/audit',
            f'/api/video-takedown/task/audit',
            f'/ams/api/video-takedown/task/{task_id}/audit',
        ]
        
        audit_body = {
            'auditStatus': 'APPROVED',
            'auditOpinion': 'AI测试数据准备-审批通过'
        }
        
        for path in audit_paths:
            resp = api_call('POST', path, token, audit_body)
            if resp and isinstance(resp, dict) and resp.get('code') in [200, 0]:
                print(f'    *** AUDIT SUCCESS via {path} ***')
                break

    # Step 6: 尝试 create-by-video-id 看当前报错
    print('\n=== Step 6: 测试 create-by-video-id API ===')
    create_paths = [
        '/api/video-takedown/task/create-by-video-id',
        '/video-takedown/task/create-by-video-id',
    ]
    create_body = {
        'videoIds': ['test_diagnosis_001'],
        'processMethod': 'VIDEO_DELETE',
        'takedownReason': 'TEMP_COPYRIGHT_DISPUTE',
        'remark': 'API诊断'
    }
    for path in create_paths:
        resp = api_call('POST', path, token, create_body)
        if resp and isinstance(resp, dict):
            print(f'    Response code: {resp.get("code")}')

    print('\n=== Done ===')

if __name__ == '__main__':
    main()
