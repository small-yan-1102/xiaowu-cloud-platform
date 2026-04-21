# -*- coding: utf-8 -*-
"""SMOKE-001 导入失败排查：3 个 videoId 可用性 + 占比校验"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

VIDEOS = ['pHmZ-SP1DHA', 'xWuqfuYh3RQ', 'zZcAgM-V0cg']
CHANNEL = 'UC_7iONjjMgVnZTfpia-MwUg'
MONTH = '2026-01'

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

def dump(rows, label):
    print('-' * 70)
    print('{} (n={})'.format(label, len(rows)))
    for r in rows:
        for k, v in r.items():
            print('  {}: {}'.format(k, v))
        print()

def run():
    ssh, conn = connect()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    ph = ','.join(['%s'] * len(VIDEOS))

    # 1) 收益表存在性 + 占比字段
    print('=' * 80)
    print('【1】yt_month_channel_revenue_source - 3 个 videoId 在 2026-01 的记录')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM yt_month_channel_revenue_source")
    cols = [r['Field'] for r in cur.fetchall()]
    print('字段: {}'.format(', '.join(cols)))
    print()

    cur.execute("""
        SELECT * FROM yt_month_channel_revenue_source
        WHERE target_video_id IN ({}) AND month=%s
    """.format(ph), VIDEOS + [MONTH])
    rev_rows = cur.fetchall()
    dump(rev_rows, 'revenue_source by videoId + month=2026-01')

    # 2) 查看所有月份下这 3 个 videoId 的收益记录
    print('=' * 80)
    print('【2】所有月份下这 3 个 videoId 的收益记录')
    print('=' * 80)
    cur.execute("""
        SELECT month, target_video_id, target_channel_id, revenue, pipeline_id,
               v_revenue_ratio
        FROM yt_month_channel_revenue_source
        WHERE target_video_id IN ({})
        ORDER BY target_video_id, month
    """.format(ph), VIDEOS)
    rows = cur.fetchall()
    print('共 {} 条'.format(len(rows)))
    for r in rows:
        print('  {}'.format(r))
    print()

    # 3) 冲销表
    print('=' * 80)
    print('【3】yt_reversal_report - 冲销父行')
    print('=' * 80)
    cur.execute("""
        SELECT id, channel_id, month, received_status, channel_split_status,
               settlement_created_status, unattributed_revenue, channel_type
        FROM yt_reversal_report
        WHERE channel_id = %s AND month = %s
    """, (CHANNEL, MONTH))
    dump(cur.fetchall(), 'yt_reversal_report')

    # 4) 频道分成配置（占比校验源头）
    print('=' * 80)
    print('【4】频道分成配置表（占比校验源头）')
    print('=' * 80)
    # 先列出可能的表
    cur.execute("""
        SELECT TABLE_NAME FROM information_schema.TABLES
        WHERE TABLE_SCHEMA='silverdawn_finance'
          AND (TABLE_NAME LIKE '%split%' OR TABLE_NAME LIKE '%ratio%'
               OR TABLE_NAME LIKE '%channel_team%' OR TABLE_NAME LIKE '%allocate%'
               OR TABLE_NAME LIKE '%share%')
        ORDER BY TABLE_NAME
    """)
    print('候选分成表:')
    split_tables = []
    for r in cur.fetchall():
        print('  - {}'.format(r['TABLE_NAME']))
        split_tables.append(r['TABLE_NAME'])
    print()

    # 针对每个可能表，看是否含 channel_id 字段并查询
    for t in split_tables:
        try:
            cur.execute("SHOW COLUMNS FROM `{}`".format(t))
            tcols = [r['Field'] for r in cur.fetchall()]
            if 'channel_id' in tcols:
                cur.execute("SELECT * FROM `{}` WHERE channel_id=%s LIMIT 20".format(t), (CHANNEL,))
                rr = cur.fetchall()
                if rr:
                    dump(rr, '{} (by channel_id)'.format(t))
        except Exception as e:
            print('{} 失败: {}'.format(t, e))
    print()

    # 5) 查视频-作品关联（SMOKE-001 明确说"导入无归属视频"—也许现在反而是有归属了）
    print('=' * 80)
    print('【5】video_composition 归属情况 (distribution 库)')
    print('=' * 80)
    conn.close(); ssh.close()
    ssh2, conn2 = connect('silverdawn_distribution')
    cur = conn2.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT video_id, channel_id, team_id, composition_id, ams_composition_id,
               composition_name, related, deleted
        FROM video_composition
        WHERE video_id IN ({})
    """.format(ph), VIDEOS)
    dump(cur.fetchall(), 'video_composition')
    conn2.close(); ssh2.close()

    # 6) 频道归属
    print('=' * 80)
    print('【6】频道归属（target_channel）')
    print('=' * 80)
    ssh3, conn3 = connect('silverdawn_distribution')
    c = conn3.cursor(pymysql.cursors.DictCursor)
    c.execute("SELECT * FROM target_channel WHERE channel_id=%s", (CHANNEL,))
    dump(c.fetchall(), 'target_channel')
    conn3.close(); ssh3.close()

if __name__ == '__main__':
    run()
