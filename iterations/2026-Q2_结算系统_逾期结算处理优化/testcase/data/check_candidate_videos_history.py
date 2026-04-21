# -*- coding: utf-8 -*-
"""验证 Top 5 候选频道的推荐视频在 overdue 表是否有历史记录"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

CANDIDATES = [
    ('UCADdJFvHXr_9N4K3Uh19pAQ', 'Xinbao Couple', ['q65ku87lNGE', 'd1W0pQkXNaQ', '04L6spLBuS0']),
    ('UC49MSQdai1EUgy7cpUBqI7w', 'Funny Parent-Child Videos', ['k8NLm5XegO4', 'hfOsfibfqGY', 's34OWyMs40U']),
    ('UC1DpbYDIuB5kfesOVOQscAw', '农家宋姐', ['mpdl9OavXtc', 'DUFcmONoSRk', 'Or9b0ZmKtac']),
    ('UC2NFP2NvOkNug8vkdA9_hyQ', '柳州二哥', ['YZXYWm46S4M', 'PsVttq16v1o', 'BhvXPtO9tjI']),
    ('UCaFj8yl__YDMBPdvcBeTCzQ', '洗了蒜了', ['TMQuzdRSGGk', 'A_C2QSMp1Gw', 'vWCEYPz6Q68']),
]
ALL_VIDS = sorted({v for _, _, vids in CANDIDATES for v in vids})

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
    ssh, conn = connect('silverdawn_finance')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    ph = ','.join(['%s'] * len(ALL_VIDS))

    # ===== 1) video_composition_overdue =====
    print('=' * 80)
    print('【1】video_composition_overdue 历史记录（15 个视频）')
    print('=' * 80)
    cur.execute("""
        SELECT id, video_id, channel_id, receipted_month, status, pipeline_id,
               team_name, deleted, created_at
        FROM video_composition_overdue
        WHERE video_id IN ({})
        ORDER BY video_id, created_at
    """.format(ph), ALL_VIDS)
    rows = cur.fetchall()
    print('命中记录数: {}'.format(len(rows)))
    for r in rows:
        print('  vid={} ch={} month={} status={} pipeline={} deleted={} at={}'.format(
            r['video_id'], r['channel_id'], r['receipted_month'],
            r['status'], r['pipeline_id'], r['deleted'], r['created_at']))
    print()

    # 按候选汇总
    vid_to_overdue = {v: [] for v in ALL_VIDS}
    for r in rows:
        vid_to_overdue[r['video_id']].append(r)

    # ===== 2) 收益表再次确认 2026-01 状态 =====
    print('=' * 80)
    print('【2】yt_month_channel_revenue_source 2026-01 重新确认')
    print('=' * 80)
    cur.execute("""
        SELECT target_video_id, target_channel_id, month, revenue, pipeline_id,
               v_revenue_ratio, v_sg_revenue_ratio
        FROM yt_month_channel_revenue_source
        WHERE target_video_id IN ({}) AND month='2026-01'
        ORDER BY target_video_id
    """.format(ph), ALL_VIDS)
    rev_rows = cur.fetchall()
    vid_to_rev = {r['target_video_id']: r for r in rev_rows}
    for r in rev_rows:
        print('  vid={} ch={} pipeline={} revenue={} ratio={}'.format(
            r['target_video_id'], r['target_channel_id'],
            r['pipeline_id'], r['revenue'], r['v_revenue_ratio']))
    print()

    # ===== 3) 冲销父行再确认 =====
    print('=' * 80)
    print('【3】冲销父行再确认 (5 个频道)')
    print('=' * 80)
    channels = [c for c, _, _ in CANDIDATES]
    ph_ch = ','.join(['%s'] * len(channels))
    cur.execute("""
        SELECT id, channel_id, month, channel_type, received_status,
               channel_split_status, settlement_created_status,
               unattributed_revenue
        FROM yt_reversal_report
        WHERE channel_id IN ({}) AND month='2026-01' AND channel_type=2
        ORDER BY channel_id
    """.format(ph_ch), channels)
    ch_to_parent = {}
    for r in cur.fetchall():
        ch_to_parent[r['channel_id']] = r
        print('  ch={} id={} split={} settle={} rev={}'.format(
            r['channel_id'], r['id'], r['channel_split_status'],
            r['settlement_created_status'], r['unattributed_revenue']))
    print()

    conn.close(); ssh.close()

    # ===== 4) 汇总每个候选的就绪情况 =====
    print('=' * 80)
    print('🎯 候选就绪情况汇总')
    print('=' * 80)
    ready_candidates = []
    for ch, name, vids in CANDIDATES:
        print('\n### {} ({}) ###'.format(ch, name))
        parent = ch_to_parent.get(ch)
        if parent:
            print('  冲销父行: split={} settle={} rev=${}'.format(
                parent['channel_split_status'], parent['settlement_created_status'],
                parent['unattributed_revenue']))
        problems = []
        for v in vids:
            ov = vid_to_overdue.get(v, [])
            rev = vid_to_rev.get(v)
            rev_pipeline = rev['pipeline_id'] if rev else 'MISSING'
            rev_ratio = rev['v_revenue_ratio'] if rev else '-'

            # 判定
            active_overdue = [r for r in ov if r.get('deleted', 0) == 0]
            if active_overdue:
                status_tag = '⚠️ overdue 已有 {} 条'.format(len(active_overdue))
                problems.append(v)
            elif rev_pipeline != 'unattributed':
                status_tag = '❌ revenue pipeline={}'.format(rev_pipeline)
                problems.append(v)
            else:
                status_tag = '✅ 可用'
            print('  - {} | pipeline={} | ratio={} | {}'.format(
                v, rev_pipeline, rev_ratio, status_tag))

        if not problems:
            ready_candidates.append((ch, name, vids))
            print('  🟢 该候选全部 3 个视频可用')
        else:
            print('  🔴 存在问题视频: {}'.format(problems))

    print()
    print('=' * 80)
    print('结论：{}/{} 个候选完全可用'.format(len(ready_candidates), len(CANDIDATES)))
    print('=' * 80)
    for ch, name, vids in ready_candidates:
        print('  ✅ {} ({}) - videos={}'.format(ch, name, vids))

if __name__ == '__main__':
    run()
