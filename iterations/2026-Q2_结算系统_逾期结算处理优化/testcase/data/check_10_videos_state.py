# -*- coding: utf-8 -*-
"""查询 10 个视频当前状态，用于写恢复 SQL"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

VIDEOS = [
    'l1G-j-RPN4c', '-xImHQaOuEM', 'teBj-w7rR3s', 'iMMKQEIX1JE',
    'Jw4RABozVg4', 'noIaBMD1Vr8', 'PXj-DCK-4SU', 'h96jGKrMhdw',
    'Af0vNbFqNZU', 'e0DMJ2aRm0g',
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

    # ===== 1) overdue 表当前状态 =====
    print('=' * 80)
    print('【1】video_composition_overdue 当前状态')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM video_composition_overdue")
    cols = [r['Field'] for r in cur.fetchall()]
    print('关键字段: id, video_id, channel_id, receipted_month, status, pipeline_id, original_status, video_tag, published_date, deleted, created_at, updated_at')
    print()

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
        print('  id={} vid={} ch={} month={} status={} orig_status={} pipeline={} tag={} pub={} deleted={} updated={}'.format(
            r['id'], r['video_id'], r['channel_id'], r['receipted_month'],
            r['status'], r['original_status'], r['pipeline_id'],
            r['video_tag'], r['published_date'], r['deleted'], r['updated_at']))
    print()

    # 汇总 status 分布
    from collections import Counter
    status_counter = Counter()
    pipeline_ids = set()
    channels = set()
    for r in rows:
        status_counter[(r['status'], r['deleted'])] += 1
        if r['pipeline_id']:
            pipeline_ids.add(r['pipeline_id'])
        if r['channel_id']:
            channels.add(r['channel_id'])
    print('status 分布: {}'.format(dict(status_counter)))
    print('涉及 pipeline_id: {}'.format(pipeline_ids))
    print('涉及 channel_id: {}'.format(channels))
    print()

    # ===== 2) 冲销表子行（如果已拆分）=====
    if pipeline_ids:
        print('=' * 80)
        print('【2】yt_reversal_report 相关子行')
        print('=' * 80)
        ph_p = ','.join(['%s'] * len(pipeline_ids))
        cur.execute("""
            SELECT id, channel_id, month, channel_type, pipeline_id,
                   channel_split_status, settlement_created_status,
                   unattributed_revenue, created_at, updated_at
            FROM yt_reversal_report
            WHERE pipeline_id IN ({})
            ORDER BY pipeline_id, id
        """.format(ph_p), list(pipeline_ids))
        for r in cur.fetchall():
            print('  id={} ch={} month={} ch_type={} pipeline={} split={} settle={} rev={} created={} updated={}'.format(
                r['id'], r['channel_id'], r['month'], r['channel_type'], r['pipeline_id'],
                r['channel_split_status'], r['settlement_created_status'],
                r['unattributed_revenue'], r['created_at'], r['updated_at']))
        print()

    # ===== 3) 涉及频道的冲销父行（month 2026-01 和 2026-02 等）=====
    if channels:
        print('=' * 80)
        print('【3】涉及频道的冲销父行（所有月份）')
        print('=' * 80)
        ph_c = ','.join(['%s'] * len(channels))
        cur.execute("""
            SELECT id, channel_id, month, channel_type, pipeline_id,
                   channel_split_status, settlement_created_status,
                   unattributed_revenue
            FROM yt_reversal_report
            WHERE channel_id IN ({}) AND pipeline_id IS NULL
            ORDER BY channel_id, month, channel_type
        """.format(ph_c), list(channels))
        for r in cur.fetchall():
            print('  id={} ch={} month={} ch_type={} split={} settle={} rev={}'.format(
                r['id'], r['channel_id'], r['month'], r['channel_type'],
                r['channel_split_status'], r['settlement_created_status'],
                r['unattributed_revenue']))
        print()

    # ===== 4) revenue_source 该视频是否已归属 =====
    print('=' * 80)
    print('【4】yt_month_channel_revenue_source 这 10 个视频的 pipeline_id')
    print('=' * 80)
    cur.execute("""
        SELECT target_video_id, month, target_channel_id, pipeline_id,
               v_revenue_ratio, revenue
        FROM yt_month_channel_revenue_source
        WHERE target_video_id IN ({})
        ORDER BY target_video_id, month
    """.format(ph), VIDEOS)
    for r in cur.fetchall():
        print('  vid={} month={} ch={} pipeline={} ratio={} revenue={}'.format(
            r['target_video_id'], r['month'], r['target_channel_id'],
            r['pipeline_id'], r['v_revenue_ratio'], r['revenue']))

    conn.close(); ssh.close()

if __name__ == '__main__':
    run()
