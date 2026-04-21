# -*- coding: utf-8 -*-
"""查询第二批 10 个视频当前状态"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

VIDEOS = [
    'aP6cbrB-SDk', 'CVKZIfDhidk', 'dUAZ4_KEM5g', 'EJzUQcngUo0',
    'fMrgq0wUFk8', 'GoPWpoZ5uu4', 'iu9VlE7oH9g', 'nhTBDkMwn9s',
    'oCNjwf83Uyo', 'SJK02WQZu6M',
]

def connect(database='silverdawn_finance'):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('172.16.24.200', port=22, username='test', password='wgu4&Q_2')
    tr = ssh.get_transport()
    ch = tr.open_channel('direct-tcpip', ('172.16.24.61', 3306), ('127.0.0.1', 0))
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='xiaowu_db',
                           password='}C7n%7Wklq6P', database=database,
                           charset='utf8mb4', defer_connect=True)
    conn.connect(ch)
    return ssh, conn

def run():
    ssh, conn = connect()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    ph = ','.join(['%s'] * len(VIDEOS))

    # ===== 1) overdue =====
    print('=' * 80)
    print('【1】video_composition_overdue 当前状态')
    print('=' * 80)
    cur.execute("""
        SELECT id, video_id, channel_id, receipted_month, status,
               pipeline_id, original_status, video_tag, published_date,
               team_name, deleted, created_at, updated_at
        FROM video_composition_overdue
        WHERE video_id IN ({})
        ORDER BY video_id, receipted_month, id
    """.format(ph), VIDEOS)
    rows = cur.fetchall()
    print('命中记录数: {}'.format(len(rows)))
    for r in rows:
        print('  id={} vid={} ch={} month={} status={} orig={} pipeline={} pub={} deleted={} updated={}'.format(
            r['id'], r['video_id'], r['channel_id'], r['receipted_month'],
            r['status'], r['original_status'], r['pipeline_id'],
            r['published_date'], r['deleted'], r['updated_at']))

    from collections import Counter
    sc = Counter()
    pipe_ids = set()
    chans = set()
    for r in rows:
        sc[(r['status'], r['original_status'], r['deleted'])] += 1
        if r['pipeline_id']:
            pipe_ids.add(r['pipeline_id'])
        if r['channel_id']:
            chans.add(r['channel_id'])
    print()
    print('(status, orig, deleted) 分布: {}'.format(dict(sc)))
    print('pipeline_id: {}'.format(pipe_ids))
    print('channel: {}'.format(chans))
    print()

    # ===== 2) 拆分产生的冲销子行 =====
    if pipe_ids:
        print('=' * 80)
        print('【2】yt_reversal_report 同 pipeline 子行')
        print('=' * 80)
        ph_p = ','.join(['%s'] * len(pipe_ids))
        cur.execute("""
            SELECT id, channel_id, month, channel_type, pipeline_id,
                   channel_split_status, settlement_created_status,
                   unattributed_revenue, created_at, updated_at
            FROM yt_reversal_report
            WHERE pipeline_id IN ({})
            ORDER BY pipeline_id, id
        """.format(ph_p), list(pipe_ids))
        for r in cur.fetchall():
            print('  id={} ch={} month={} ch_type={} pipeline={} split={} settle={} rev={} created={}'.format(
                r['id'], r['channel_id'], r['month'], r['channel_type'], r['pipeline_id'],
                r['channel_split_status'], r['settlement_created_status'],
                r['unattributed_revenue'], r['created_at']))
    print()

    conn.close(); ssh.close()

if __name__ == '__main__':
    run()
