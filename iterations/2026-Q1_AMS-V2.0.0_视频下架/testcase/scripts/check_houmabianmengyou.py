# -*- coding: utf-8 -*-
"""查询作品「后妈变盟友」的完整数据链路"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

WORK_NAME = '后妈变盟友'
AMS_COMP_ID = 100965  # 已查到

def connect_db(database='silverdawn_ams'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('172.16.24.200', port=22, username='test', password='wgu4&Q_2')
    transport = ssh.get_transport()
    channel = transport.open_channel('direct-tcpip', ('172.16.24.61', 3306), ('127.0.0.1', 0))
    conn = pymysql.connect(
        host='127.0.0.1', port=3306, user='xiaowu_db',
        password='}C7n%7Wklq6P', database=database,
        charset='utf8mb4', defer_connect=True
    )
    conn.connect(channel)
    return ssh, conn

def dump_rows(rows, label):
    print('-' * 70)
    print('{} (n={})'.format(label, len(rows)))
    if not rows:
        print('  (无)')
        return
    for i, r in enumerate(rows):
        print('  #{}'.format(i + 1))
        for k, v in r.items():
            print('    {}: {}'.format(k, v))

def run():
    # ===== 1) AMS 作品 =====
    print('=' * 80)
    print('【1】silverdawn_ams.ams_composition')
    print('=' * 80)
    ssh, conn = connect_db('silverdawn_ams')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM ams_composition WHERE id=%s", (AMS_COMP_ID,))
    dump_rows(cur.fetchall(), 'ams_composition')
    print()

    # ===== 2) 分销分配 =====
    print('=' * 80)
    print('【2】silverdawn_ams.composition_allocate (分销分配)')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM composition_allocate")
    alloc_cols = [r['Field'] for r in cur.fetchall()]
    print('字段: {}'.format(', '.join(alloc_cols)))
    # 找 composition 引用字段
    for f in ['ams_composition_id', 'composition_id', 'composition_ams_id']:
        if f in alloc_cols:
            cur.execute("SELECT * FROM composition_allocate WHERE {}=%s".format(f), (AMS_COMP_ID,))
            dump_rows(cur.fetchall(), 'composition_allocate (via {})'.format(f))
            break
    print()

    # ===== 3) 任务单关联 =====
    print('=' * 80)
    print('【3】silverdawn_ams.video_takedown_task_composition')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM video_takedown_task_composition")
    vtc_cols = [r['Field'] for r in cur.fetchall()]
    print('字段: {}'.format(', '.join(vtc_cols)))
    task_ids = []
    for f in ['ams_composition_id', 'composition_id']:
        if f in vtc_cols:
            cur.execute("SELECT * FROM video_takedown_task_composition WHERE {}=%s".format(f), (AMS_COMP_ID,))
            rows = cur.fetchall()
            dump_rows(rows, 'video_takedown_task_composition')
            task_ids = list(set(r.get('task_id') for r in rows if r.get('task_id')))
            break
    print('关联 task_id: {}'.format(task_ids))
    print()

    # 任务单
    if task_ids:
        ph = ','.join(['%s'] * len(task_ids))
        cur.execute("SELECT * FROM video_takedown_task WHERE id IN ({})".format(ph), task_ids)
        dump_rows(cur.fetchall(), 'video_takedown_task')
        cur.execute("SELECT * FROM video_takedown_task_video WHERE task_id IN ({})".format(ph), task_ids)
        dump_rows(cur.fetchall(), 'video_takedown_task_video')
    print()

    # ===== 4) 解约单 =====
    print('=' * 80)
    print('【4】silverdawn_ams.composition_terminate')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM composition_terminate")
    ter_cols = [r['Field'] for r in cur.fetchall()]
    print('字段: {}'.format(', '.join(ter_cols)))
    for f in ['ams_composition_id', 'composition_id']:
        if f in ter_cols:
            cur.execute("SELECT * FROM composition_terminate WHERE {}=%s".format(f), (AMS_COMP_ID,))
            dump_rows(cur.fetchall(), 'composition_terminate')
            break
    # 按 detail 表也查查
    cur.execute("SHOW COLUMNS FROM composition_terminate_detail")
    td_cols = [r['Field'] for r in cur.fetchall()]
    print('composition_terminate_detail 字段: {}'.format(', '.join(td_cols)))
    for f in ['ams_composition_id', 'composition_id']:
        if f in td_cols:
            cur.execute("SELECT * FROM composition_terminate_detail WHERE {}=%s".format(f), (AMS_COMP_ID,))
            dump_rows(cur.fetchall(), 'composition_terminate_detail')
            break

    conn.close(); ssh.close()
    print()

    # ===== 5) silverdawn_distribution (剧老板端) =====
    print('=' * 80)
    print('【5】silverdawn_distribution (剧老板分销端)')
    print('=' * 80)
    try:
        ssh2, conn2 = connect_db('silverdawn_distribution')
        c2 = conn2.cursor(pymysql.cursors.DictCursor)
        c2.execute("""
            SELECT TABLE_NAME FROM information_schema.TABLES
            WHERE TABLE_SCHEMA='silverdawn_distribution'
              AND (TABLE_NAME LIKE '%takedown%' OR TABLE_NAME LIKE '%composition%'
                   OR TABLE_NAME LIKE '%channel%')
            ORDER BY TABLE_NAME
        """)
        for r in c2.fetchall():
            print('  - {}'.format(r['TABLE_NAME']))
        conn2.close(); ssh2.close()
    except Exception as e:
        print('失败: {}'.format(e))

if __name__ == '__main__':
    run()
