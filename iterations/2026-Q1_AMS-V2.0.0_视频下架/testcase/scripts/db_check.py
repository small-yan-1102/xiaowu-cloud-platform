"""数据库验证脚本 - 用于测试执行过程中的数据状态检查"""
import paramiko
import pymysql

def run_check():
    """执行数据库状态检查"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('172.16.24.200', port=22, username='test', password='wgu4&Q_2')
    transport = ssh.get_transport()
    channel = transport.open_channel('direct-tcpip', ('172.16.24.61', 3306), ('127.0.0.1', 0))
    conn = pymysql.connect(
        host='127.0.0.1', port=3306, user='xiaowu_db',
        password='}C7n%7Wklq6P', database='silverdawn_ams',
        charset='utf8mb4', defer_connect=True
    )
    conn.connect(channel)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 1. 解约单统计
    cursor.execute('SELECT COUNT(*) as total FROM composition_terminate')
    row = cursor.fetchone()
    print('=== 解约单总数: {} ==='.format(row['total']))

    sql_type = """
    SELECT terminate_type, COUNT(*) as cnt,
           SUM(CASE WHEN need_takedown = 1 THEN 1 ELSE 0 END) as with_takedown,
           SUM(CASE WHEN need_takedown IS NULL OR need_takedown = 0 THEN 1 ELSE 0 END) as without_takedown
    FROM composition_terminate
    GROUP BY terminate_type
    ORDER BY terminate_type
    """
    cursor.execute(sql_type)
    for r in cursor.fetchall():
        tname = {1: '双方协商', 2: '分销商解约', 3: '上游版权解约'}.get(r['terminate_type'], '未知')
        print('  类型{}({}): {}条, 含下架:{}, 无下架:{}'.format(
            r['terminate_type'], tname, r['cnt'], r['with_takedown'], r['without_takedown']))

    # 2. 双方协商且无下架的记录(TER-015 场景B验证数据)
    print()
    print('=== 双方协商且need_takedown为NULL(前5条) ===')
    sql_no_takedown = """
    SELECT code, team_name, need_takedown, takedown_task_code, created_at
    FROM composition_terminate
    WHERE terminate_type = 1 AND (need_takedown IS NULL OR need_takedown = 0)
    ORDER BY created_at DESC LIMIT 5
    """
    cursor.execute(sql_no_takedown)
    for r in cursor.fetchall():
        print('  {} | {} | need_takedown={} | task={} | {}'.format(
            r['code'], r['team_name'], r['need_takedown'], r['takedown_task_code'], r['created_at']))

    # 3. 任务单状态
    print()
    print('=== 任务单状态 ===')
    cursor.execute('SELECT code, status, process_method, takedown_reason, task_source FROM video_takedown_task ORDER BY code')
    for r in cursor.fetchall():
        print('  {} | {} | {} | {} | source={}'.format(
            r['code'], r['status'], r['process_method'], r['takedown_reason'], r['task_source']))

    # 4. 有关联任务单的解约单(TER-016)
    print()
    print('=== 有关联任务单的解约单 ===')
    sql_linked = """
    SELECT code, terminate_type, team_name, takedown_task_code
    FROM composition_terminate
    WHERE takedown_task_code IS NOT NULL AND takedown_task_code != ''
    ORDER BY created_at DESC LIMIT 10
    """
    cursor.execute(sql_linked)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            cursor.execute('SELECT code, status FROM video_takedown_task WHERE code = %s', (r['takedown_task_code'],))
            task = cursor.fetchone()
            exists = 'EXISTS({})'.format(task['status']) if task else 'NOT_EXISTS'
            print('  {} | type={} | {} | task={} | {}'.format(
                r['code'], r['terminate_type'], r['team_name'], r['takedown_task_code'], exists))
    else:
        print('  无')

    # 5. 检查create_source字段
    print()
    print('=== composition_terminate 表字段 ===')
    cursor.execute('SHOW COLUMNS FROM composition_terminate')
    cols = [r['Field'] for r in cursor.fetchall()]
    print('  有create_source字段: {}'.format('create_source' in cols))
    print('  字段列表: {}'.format(', '.join(cols)))

    conn.close()
    ssh.close()
    print()
    print('DB验证完成')

if __name__ == '__main__':
    run_check()
