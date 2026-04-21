# -*- coding: utf-8 -*-
"""只聚焦海外频道 UC4IGCtXW9sdyZN2235v7r_Q 下 不蓝姬 的 pipeline_id"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko, pymysql

AMS_ID = 100883
CHANNEL = 'UC4IGCtXW9sdyZN2235v7r_Q'
VIDS = ['teBj-w7rR3s', 'dUAZ4_KEM5g']

def connect(database):
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
    ph = ','.join(['%s'] * len(VIDS))

    # ===== 1) distribution.video_composition =====
    print('=' * 80)
    print('【1】silverdawn_distribution.video_composition (海外频道)')
    print('=' * 80)
    ssh, conn = connect('silverdawn_distribution')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT id, video_id, channel_id, ams_composition_id, pipeline_id,
               deleted, updated_at
        FROM video_composition
        WHERE ams_composition_id=%s AND channel_id=%s
    """, (AMS_ID, CHANNEL))
    for r in cur.fetchall():
        pipe = r['pipeline_id']
        tag = '✅ NULL' if pipe is None else '⚠️ {}'.format(pipe)
        print('  id={} vid={} updated={} pipeline={}'.format(
            r['id'], r['video_id'], r['updated_at'], tag))
    conn.close(); ssh.close()
    print()

    # ===== 2) finance.video_composition_overdue =====
    print('=' * 80)
    print('【2】silverdawn_finance.video_composition_overdue (海外频道)')
    print('=' * 80)
    ssh, conn = connect('silverdawn_finance')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT id, video_id, channel_id, receipted_month, status, original_status,
               pipeline_id, deleted
        FROM video_composition_overdue
        WHERE channel_id=%s AND video_id IN ({})
    """.format(ph), [CHANNEL] + VIDS)
    for r in cur.fetchall():
        pipe = r['pipeline_id']
        tag = '✅ NULL' if pipe is None else '⚠️ {}'.format(pipe)
        print('  id={} vid={} month={} status={} orig={} deleted={} pipeline={}'.format(
            r['id'], r['video_id'], r['receipted_month'],
            r['status'], r['original_status'], r['deleted'], tag))
    print()

    # ===== 3) finance.yt_month_channel_revenue_source =====
    print('=' * 80)
    print('【3】silverdawn_finance.yt_month_channel_revenue_source (海外频道)')
    print('=' * 80)
    cur.execute("""
        SELECT target_video_id, month, target_channel_id, pipeline_id, revenue
        FROM yt_month_channel_revenue_source
        WHERE target_channel_id=%s AND target_video_id IN ({})
        ORDER BY target_video_id, month
    """.format(ph), [CHANNEL] + VIDS)
    for r in cur.fetchall():
        pipe = r['pipeline_id']
        tag = '⚠️ {}'.format(pipe)
        if pipe == 'unattributed':
            tag = '🟡 unattributed'
        elif pipe is None:
            tag = '✅ NULL'
        print('  vid={} month={} revenue={} pipeline={}'.format(
            r['target_video_id'], r['month'], r['revenue'], tag))
    conn.close(); ssh.close()

if __name__ == '__main__':
    run()
