# -*- coding: utf-8 -*-
"""在原 18 个候选频道中，挑出 3 个完全无 overdue 历史的视频"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

# 原 scan 结果中条件 1+2+3 全通过的 18 个频道及其 target team_id
CANDIDATES = [
    ('UCADdJFvHXr_9N4K3Uh19pAQ', 'Xinbao Couple', '1985522863929118720'),
    ('UC49MSQdai1EUgy7cpUBqI7w', 'Funny Parent-Child Videos', '1988137461068951552'),
    ('UC1DpbYDIuB5kfesOVOQscAw', '农家宋姐', '1988137461068951552'),
    ('UC2NFP2NvOkNug8vkdA9_hyQ', '柳州二哥', '1988137461068951552'),
    ('UCaFj8yl__YDMBPdvcBeTCzQ', '洗了蒜了', '1985522863929118720'),
    ('UC49b56fKJm9LxCDnMUDneQQ', '阿锐与摄影师', '1988137461068951552'),
    ('UC1m2EHRsik9diZn7-btSzBg', '奶油短剧社', '1988137461068951552'),
    ('UC-GfF8ajbd-U69wSAkB692g', 'Sky Swing', '1988137461068951552'),
    ('UC_HuLArMZ_EDV0iO0fcSMmQ', '?', '1988137461068951552'),
    ('UCaUiU8Otrquu2c0l_8SkJbg', '?', '1988520080772243456'),
    ('UC8-mpK5dgmKEfNCjwy1rSag', '?', '1988526061061218304'),
    ('UC_tjwse2zeYyutkA6QYnJPA', '?', '1988137461068951552'),
    ('UC31-fVzJhcEB4WfeXeqdU9Q', '?', '1988137461068951552'),
    ('UC1442or1QNoEy_G2MvcXy3Q', '?', '1988137461068951552'),
    ('UC0qtzxuS71YpA6uRQoEP57w', '?', '1988137461068951552'),
    ('UCEW8gkdfQqCXu_yhMR9YrAQ', '?', '1988526061061218304'),
    ('UCfg-EBzK5SWG1EbA_XdTMqA', '?', '1988526061061218304'),
    ('UC7OzzxdDFzJvgZvDtasKS-w', '?', '1988526061061218304'),
]
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

def run():
    ssh_f, conn_f = connect('silverdawn_finance')
    cf = conn_f.cursor(pymysql.cursors.DictCursor)

    ssh_d, conn_d = connect('silverdawn_distribution')
    cd = conn_d.cursor(pymysql.cursors.DictCursor)

    clean_results = []

    for ch, name, team in CANDIDATES:
        # 取该频道 2026-01 pipeline=unattributed 的视频池（按 revenue DESC）
        cf.execute("""
            SELECT target_video_id, revenue, v_revenue_ratio
            FROM yt_month_channel_revenue_source
            WHERE target_channel_id=%s AND month=%s AND pipeline_id='unattributed'
            ORDER BY revenue DESC
            LIMIT 100
        """, (ch, MONTH))
        video_pool = cf.fetchall()
        if len(video_pool) < 3:
            continue
        vids = [r['target_video_id'] for r in video_pool]

        # 排除在 overdue 表任何月份有非删除记录的视频
        ph = ','.join(['%s'] * len(vids))
        cf.execute("""
            SELECT DISTINCT video_id FROM video_composition_overdue
            WHERE video_id IN ({}) AND deleted=0
        """.format(ph), vids)
        dirty = {r['video_id'] for r in cf.fetchall()}

        # 查 video_composition 归属匹配（team_id == target_channel.team_id）
        cd.execute("""
            SELECT video_id, team_id, composition_name, ams_composition_id
            FROM video_composition
            WHERE video_id IN ({}) AND channel_id=%s AND deleted=0
        """.format(ph), vids + [ch])
        vc_map = {r['video_id']: r for r in cd.fetchall()}

        # 挑 3 个：干净 + 归属 team 匹配
        picked = []
        for r in video_pool:
            vid = r['target_video_id']
            if vid in dirty:
                continue
            vc = vc_map.get(vid)
            if not vc:
                continue
            if str(vc['team_id']) != str(team):
                continue
            picked.append({
                'video_id': vid,
                'revenue': float(r['revenue']),
                'ratio': float(r['v_revenue_ratio']),
                'composition_name': vc['composition_name'],
                'ams_composition_id': vc['ams_composition_id'],
            })
            if len(picked) == 3:
                break

        if len(picked) == 3:
            clean_results.append({
                'channel_id': ch,
                'channel_name': name,
                'target_team_id': team,
                'videos': picked,
            })

    conn_f.close(); ssh_f.close()
    conn_d.close(); ssh_d.close()

    # ===== 查频道的 unattributed_revenue（再补上 revenue 信息）=====
    ssh_f, conn_f = connect('silverdawn_finance')
    cf = conn_f.cursor(pymysql.cursors.DictCursor)
    for c in clean_results:
        cf.execute("""
            SELECT unattributed_revenue, channel_name
            FROM yt_reversal_report
            WHERE channel_id=%s AND month='2026-01' AND channel_type=2
            LIMIT 1
        """, (c['channel_id'],))
        row = cf.fetchone()
        if row:
            c['unattributed_revenue'] = float(row['unattributed_revenue'])
            if c['channel_name'] == '?' and row.get('channel_name'):
                c['channel_name'] = row['channel_name']
    conn_f.close(); ssh_f.close()

    # 按 unattributed_revenue 降序
    clean_results.sort(key=lambda x: x.get('unattributed_revenue', 0), reverse=True)

    print('=' * 80)
    print('🟢 完全干净（无 overdue 历史）候选频道: {}/{}'.format(len(clean_results), len(CANDIDATES)))
    print('=' * 80)
    for i, c in enumerate(clean_results):
        print()
        print('### 候选 #{} #####'.format(i + 1))
        print('  channel_id:    {}'.format(c['channel_id']))
        print('  channel_name:  {}'.format(c['channel_name']))
        print('  target_team_id: {}'.format(c['target_team_id']))
        print('  unattributed_revenue: ${}'.format(c.get('unattributed_revenue', '-')))
        print('  推荐 3 个视频:')
        for v in c['videos']:
            print('    - {} | ${:.2f} | ratio={:.4%} | comp={} | ams_id={}'.format(
                v['video_id'], v['revenue'], v['ratio'],
                v['composition_name'], v['ams_composition_id']))

if __name__ == '__main__':
    run()
