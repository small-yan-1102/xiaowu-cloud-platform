"""最终数据库状态检查 - 确认可执行用例的前置数据"""
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

    # 1. 任务单按状态分组
    print('=== 任务单按状态分组 ===')
    cursor.execute("""
        SELECT status, process_method, COUNT(*) as cnt
        FROM video_takedown_task
        GROUP BY status, process_method
        ORDER BY status, process_method
    """)
    for r in cursor.fetchall():
        method = {1: 'VIDEO_DELETE', 2: 'VIDEO_PRIVACY'}.get(r['process_method'], str(r['process_method']))
        print('  status={} | method={} | count={}'.format(r['status'], method, r['cnt']))

    # 2. 待审核任务单(QE-006)
    print()
    print('=== 待审核任务单 (QE-006) ===')
    cursor.execute("""
        SELECT code, status, process_method, takedown_reason, task_source
        FROM video_takedown_task
        WHERE status = 'PENDING_REVIEW'
        ORDER BY code
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            method = {1: 'VIDEO_DELETE', 2: 'VIDEO_PRIVACY'}.get(r['process_method'], str(r['process_method']))
            print('  {} | {} | {} | {} | source={}'.format(
                r['code'], r['status'], method, r['takedown_reason'], r['task_source']))
    else:
        print('  无待审核任务单')

    # 3. 处理中任务单(SP-008 场景A)
    print()
    print('=== 处理中任务单 (SP-008) ===')
    cursor.execute("""
        SELECT code, status, process_method, takedown_reason
        FROM video_takedown_task
        WHERE status = 'PROCESSING'
        ORDER BY code
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            method = {1: 'VIDEO_DELETE', 2: 'VIDEO_PRIVACY'}.get(r['process_method'], str(r['process_method']))
            print('  {} | {} | {} | {}'.format(r['code'], r['status'], method, r['takedown_reason']))
    else:
        print('  无处理中任务单')

    # 4. 已完成任务单(SP-008 场景B)
    print()
    print('=== 已完成任务单 (SP-008) ===')
    cursor.execute("""
        SELECT code, status, process_method, takedown_reason
        FROM video_takedown_task
        WHERE status = 'COMPLETED'
        ORDER BY code
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            method = {1: 'VIDEO_DELETE', 2: 'VIDEO_PRIVACY'}.get(r['process_method'], str(r['process_method']))
            print('  {} | {} | {} | {}'.format(r['code'], r['status'], method, r['takedown_reason']))
    else:
        print('  无已完成任务单')

    # 5. 已完成任务中有失败视频的(SP-009)
    print()
    print('=== 已完成任务中视频状态 ===')
    cursor.execute("""
        SELECT t.code, t.status as task_status, 
               d.takedown_status, COUNT(*) as cnt
        FROM video_takedown_task t
        JOIN video_takedown_task_detail d ON t.id = d.task_id
        WHERE t.status = 'COMPLETED'
        GROUP BY t.code, t.status, d.takedown_status
        ORDER BY t.code, d.takedown_status
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print('  {} | task={} | video_status={} | count={}'.format(
                r['code'], r['task_status'], r['takedown_status'], r['cnt']))
    else:
        print('  无数据')

    # 6. 全部失败任务(SP-009)
    print()
    print('=== 全部失败的任务单 (SP-009) ===')
    cursor.execute("""
        SELECT t.code, t.status,
               SUM(CASE WHEN d.takedown_status = 'FAILED' THEN 1 ELSE 0 END) as failed_cnt,
               COUNT(*) as total_cnt
        FROM video_takedown_task t
        JOIN video_takedown_task_detail d ON t.id = d.task_id
        WHERE t.status = 'COMPLETED'
        GROUP BY t.code, t.status
        HAVING failed_cnt = total_cnt
        ORDER BY t.code
    """)
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print('  {} | {} | all_failed({}/{})'.format(
                r['code'], r['status'], r['failed_cnt'], r['total_cnt']))
    else:
        print('  无全部失败任务')

    conn.close()
    ssh.close()
    print()
    print('DB check done')

if __name__ == '__main__':
    run_check()
