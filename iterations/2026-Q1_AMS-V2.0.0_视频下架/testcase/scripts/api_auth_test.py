"""修正 token 认证 + 审批/拒绝 API"""
import pymysql
import requests
import json

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

AMS_BASE = 'http://172.16.24.200:8024'

def get_tokens():
    """获取两种 token"""
    r = requests.post('http://172.16.24.200:8011/sso/doLogin?name=15057199668&pwd=1111',
                      headers={'Accept': 'application/json', 'Content-Length': '0'})
    data = r.json()['data']
    jwt_token = data['accessToken']
    sso_token = data['token']
    print(f'JWT accessToken: {jwt_token[:40]}...')
    print(f'SSO token:       {sso_token}')
    return jwt_token, sso_token

def try_api(path, token, header_name='accessToken', method='GET', body=None):
    """尝试 API 调用"""
    url = f'{AMS_BASE}{path}'
    headers = {
        header_name: token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    try:
        if method == 'GET':
            r = requests.get(url, headers=headers, timeout=10)
        else:
            r = requests.post(url, headers=headers, json=body, timeout=10)
        try:
            resp = r.json()
            return resp
        except:
            return {'raw': r.text[:200], 'status_code': r.status_code}
    except Exception as e:
        return {'error': str(e)}

def main():
    jwt_token, sso_token = get_tokens()

    # 测试不同 token + header 组合
    test_path = '/api/video-takedown/task/list'
    combos = [
        ('accessToken', jwt_token, 'JWT + accessToken header'),
        ('accessToken', sso_token, 'SSO + accessToken header'),
        ('Authorization', f'Bearer {jwt_token}', 'JWT + Authorization Bearer'),
        ('token', sso_token, 'SSO + token header'),
        ('token', jwt_token, 'JWT + token header'),
    ]

    print('\n=== 测试 token 认证组合 ===')
    working_combo = None
    for header_name, token_val, desc in combos:
        resp = try_api(test_path, token_val, header_name)
        status = resp.get('status', resp.get('code', 'unknown'))
        msg = resp.get('message', resp.get('msg', ''))[:80]
        print(f'  [{desc}] status={status} msg={msg}')
        if status in [200, 0, '200', '0'] and '401' not in str(status):
            working_combo = (header_name, token_val, desc)
            print(f'  *** WORKING: {desc} ***')

    if not working_combo:
        # 也试试带查询参数
        for header_name, token_val, desc in combos:
            resp = try_api(f'{test_path}?page=1&pageSize=10', token_val, header_name)
            status = resp.get('status', resp.get('code', 'unknown'))
            msg = resp.get('message', resp.get('msg', ''))[:80]
            print(f'  [{desc} +params] status={status} msg={msg}')
            if status in [200, 0] and '401' not in str(status) and 'token' not in str(msg):
                working_combo = (header_name, token_val, desc)
                print(f'  *** WORKING: {desc} ***')
                break

    if working_combo:
        h_name, h_val, h_desc = working_combo
        print(f'\n=== 使用认证方式: {h_desc} ===')

        # 获取任务列表
        resp = try_api('/api/video-takedown/task/list?page=1&pageSize=20',
                      h_val, h_name)
        print(f'\n任务列表: {json.dumps(resp, ensure_ascii=False)[:500]}')

    else:
        print('\n所有认证组合均失败，尝试直接用 POST body 传 token...')
        # 某些系统把 token 放在请求参数或 cookie 中
        r = requests.get(
            f'{AMS_BASE}/api/video-takedown/task/list',
            params={'accessToken': sso_token, 'page': 1, 'pageSize': 5},
            headers={'Accept': 'application/json'},
            timeout=10
        )
        try:
            resp = r.json()
            print(f'Query param approach: {json.dumps(resp, ensure_ascii=False)[:300]}')
        except:
            print(f'Query param approach: {r.status_code} {r.text[:200]}')

        # Cookie approach
        r2 = requests.get(
            f'{AMS_BASE}/api/video-takedown/task/list',
            cookies={'accessToken': sso_token},
            headers={'Accept': 'application/json'},
            timeout=10
        )
        try:
            resp2 = r2.json()
            print(f'Cookie approach: {json.dumps(resp2, ensure_ascii=False)[:300]}')
        except:
            print(f'Cookie approach: {r2.status_code} {r2.text[:200]}')

    print('\n=== Done ===')

if __name__ == '__main__':
    main()
