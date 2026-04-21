# -*- coding: utf-8 -*-
"""深挖占比校验失败原因"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

VIDEOS_V1 = ['pHmZ-SP1DHA', 'xWuqfuYh3RQ', 'zZcAgM-V0cg']
VIDEOS_V2 = ['xamAKzz2WPg', 'GclPPYfhmHE', 'g7pWlMyl-gg']
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

    # 1) 冲销表完整字段 + 所有状态
    print('=' * 80)
    print('【1】yt_reversal_report 完整字段结构')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM yt_reversal_report")
    for r in cur.fetchall():
        print('  {} {} NULL={} DEFAULT={}'.format(r['Field'], r['Type'], r['Null'], r['Default']))
    print()

    # 2) 查 v2 的 3 个 videoId 是否在收益表、归属情况
    ph = ','.join(['%s'] * 3)
    print('=' * 80)
    print('【2】v2 文件的 videoId 在收益表情况')
    print('=' * 80)
    cur.execute("""
        SELECT target_video_id, target_channel_id, month, revenue, pipeline_id, v_revenue_ratio
        FROM yt_month_channel_revenue_source
        WHERE target_video_id IN ({})
        ORDER BY target_video_id, month
    """.format(ph), VIDEOS_V2)
    rows = cur.fetchall()
    for r in rows:
        print('  {}'.format(r))
    print('v2 共 {} 条'.format(len(rows)))
    print()

    # 3) 该频道 2026-01 已被拆分的视频 (有具体 pipeline_id 的)
    print('=' * 80)
    print('【3】频道 UC_7iONjjMgVnZTfpia-MwUg 2026-01 非 unattributed 的视频（已归属 pipeline）')
    print('=' * 80)
    cur.execute("""
        SELECT target_video_id, pipeline_id, revenue, v_revenue_ratio, v_sg_revenue_ratio
        FROM yt_month_channel_revenue_source
        WHERE target_channel_id=%s AND month=%s AND pipeline_id != 'unattributed'
        ORDER BY target_video_id
    """, (CHANNEL, MONTH))
    attr = cur.fetchall()
    print('已归属视频数: {}'.format(len(attr)))
    print()

    # 4) 该频道 2026-01 整体占比汇总
    print('=' * 80)
    print('【4】频道 2026-01 占比汇总')
    print('=' * 80)
    cur.execute("""
        SELECT pipeline_id,
               COUNT(*) AS cnt,
               SUM(revenue) AS rev_sum,
               SUM(v_revenue_ratio) AS ratio_sum,
               SUM(v_sg_revenue_ratio) AS sg_ratio_sum
        FROM yt_month_channel_revenue_source
        WHERE target_channel_id=%s AND month=%s
        GROUP BY pipeline_id
    """, (CHANNEL, MONTH))
    for r in cur.fetchall():
        print('  pipeline={} | count={} | revenue={} | ratio_sum={} | sg_ratio_sum={}'.format(
            r['pipeline_id'], r['cnt'], r['rev_sum'], r['ratio_sum'], r['sg_ratio_sum']))
    print()

    # 5) 已有的 overdue 记录（之前是否被导入过）
    print('=' * 80)
    print('【5】video_composition_overdue 中是否已存在这些 videoId (历史导入)')
    print('=' * 80)
    all_videos = VIDEOS_V1 + VIDEOS_V2
    ph = ','.join(['%s'] * len(all_videos))
    cur.execute("""
        SELECT id, video_id, channel_id, receipted_month, status, pipeline_id,
               deleted, created_at
        FROM video_composition_overdue
        WHERE video_id IN ({})
        ORDER BY video_id, created_at
    """.format(ph), all_videos)
    rows = cur.fetchall()
    print('overdue 历史记录数: {}'.format(len(rows)))
    for r in rows:
        print('  {}'.format(r))
    print()

    # 6) 冲销表父行 + 所有子行
    print('=' * 80)
    print('【6】冲销表父行 + 所有子行 (channel+month)')
    print('=' * 80)
    cur.execute("""
        SELECT id, channel_id, month, channel_type, received_status, channel_split_status,
               settlement_created_status, unattributed_revenue, pipeline_id,
               created_at, updated_at
        FROM yt_reversal_report
        WHERE channel_id=%s AND month=%s
        ORDER BY id
    """, (CHANNEL, MONTH))
    dump(cur.fetchall(), 'yt_reversal_report (父行+子行)')
    print()

    # 7) 查该频道其他所有月份的 overdue 记录（确认是否是历史已占用）
    print('=' * 80)
    print('【7】频道其他月份 overdue 记录')
    print('=' * 80)
    cur.execute("""
        SELECT receipted_month, status, COUNT(*) AS cnt
        FROM video_composition_overdue
        WHERE channel_id=%s AND deleted=0
        GROUP BY receipted_month, status
        ORDER BY receipted_month
    """, (CHANNEL,))
    for r in cur.fetchall():
        print('  {}'.format(r))
    print()

    conn.close(); ssh.close()

if __name__ == '__main__':
    run()
