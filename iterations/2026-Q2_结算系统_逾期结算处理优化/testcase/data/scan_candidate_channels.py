# -*- coding: utf-8 -*-
"""扫描候选频道：
条件：
  1) 2026-01 冲销父行存在且 channel_split_status=0, received_status=1, channel_type=2
  2) 该频道 2026-01 有 >= 3 条 pipeline_id='unattributed' 的 revenue_source 记录
  3) target_channel 表中 2026-01 期间单一有效绑定 (terminate_date IS NULL 或 >= 2026-01-31, delivery_date <= 2026-01-01, bind_status=1, deleted=0)
  4) 所选的 3 个视频在 video_composition 中归属的 team_id 与 target_channel 当月 team_id 一致（或允许为空/未归属）
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

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
    # ===== Step 1: 在 finance 库找候选频道 =====
    ssh, conn = connect('silverdawn_finance')
    cur = conn.cursor(pymysql.cursors.DictCursor)

    print('=' * 80)
    print('Step 1: 扫描冲销父行 (月={}, channel_split_status=0, received_status=1, channel_type=2)'.format(MONTH))
    print('=' * 80)
    cur.execute("""
        SELECT r.id, r.channel_id, r.channel_name, r.unattributed_revenue,
               r.settlement_created_status
        FROM yt_reversal_report r
        WHERE r.month=%s
          AND r.channel_split_status=0
          AND r.received_status=1
          AND r.channel_type=2
          AND r.unattributed_revenue > 0
        ORDER BY r.id
    """, (MONTH,))
    candidates = cur.fetchall()
    print('初筛候选频道数: {}'.format(len(candidates)))
    # 只看前 30 个
    for r in candidates[:30]:
        print('  id={} ch={} name={} unattr_rev={} settle={}'.format(
            r['id'], r['channel_id'], r['channel_name'],
            r['unattributed_revenue'], r['settlement_created_status']))
    print()

    if not candidates:
        print('⚠️ 没有符合 channel_split_status=0 的父行，放宽到 settlement_created_status=0 再找')
        print()
        cur.execute("""
            SELECT r.id, r.channel_id, r.channel_name, r.unattributed_revenue,
                   r.channel_split_status, r.settlement_created_status
            FROM yt_reversal_report r
            WHERE r.month=%s
              AND r.received_status=1
              AND r.channel_type=2
              AND r.unattributed_revenue > 0
              AND r.settlement_created_status=0
            ORDER BY r.id LIMIT 50
        """, (MONTH,))
        candidates = cur.fetchall()
        for r in candidates:
            print('  id={} ch={} split={} settle={} unattr={}'.format(
                r['id'], r['channel_id'], r['channel_split_status'],
                r['settlement_created_status'], r['unattributed_revenue']))
        print()

    # ===== Step 2: 对每个候选，统计 unattributed 视频数 =====
    print('=' * 80)
    print('Step 2: 每个候选 ≥ 3 条 unattributed 视频 过滤')
    print('=' * 80)
    qualified = []
    for r in candidates[:100]:  # 限前 100 防爆
        ch = r['channel_id']
        cur.execute("""
            SELECT COUNT(*) AS cnt,
                   SUM(v_revenue_ratio) AS ratio_sum
            FROM yt_month_channel_revenue_source
            WHERE target_channel_id=%s AND month=%s
              AND pipeline_id='unattributed'
        """, (ch, MONTH))
        stat = cur.fetchone()
        if stat['cnt'] >= 3:
            qualified.append({**r, 'unattr_videos': stat['cnt'], 'unattr_ratio_sum': stat['ratio_sum']})
    print('条件 2 通过频道数: {}'.format(len(qualified)))
    for q in qualified[:30]:
        print('  ch={} unattr_videos={} ratio_sum={} unattr_rev={}'.format(
            q['channel_id'], q['unattr_videos'], q['unattr_ratio_sum'], q['unattributed_revenue']))
    print()

    conn.close(); ssh.close()

    if not qualified:
        print('❌ 无候选满足条件 1+2')
        return

    # ===== Step 3: 在 distribution 库过滤 target_channel 单一有效绑定 =====
    print('=' * 80)
    print('Step 3: target_channel 当月单一有效绑定')
    print('=' * 80)
    ssh2, conn2 = connect('silverdawn_distribution')
    c2 = conn2.cursor(pymysql.cursors.DictCursor)

    month_start = '2026-01-01'
    month_end = '2026-01-31'

    final = []
    for q in qualified:
        ch = q['channel_id']
        # 查 target_channel 中 2026-01 有效绑定（delivery_date <= 2026-01-01 AND (terminate_date IS NULL OR terminate_date >= 2026-01-31)）
        c2.execute("""
            SELECT id, team_id, delivery_date, terminate_date, bind_status
            FROM target_channel
            WHERE channel_id=%s AND deleted=0
        """, (ch,))
        bindings = c2.fetchall()
        # 过滤 2026-01 当月有效
        valid = [b for b in bindings
                 if (b['delivery_date'] is None or str(b['delivery_date']) <= month_start)
                 and (b['terminate_date'] is None or str(b['terminate_date']) >= month_end)
                 and b['bind_status'] == 1]
        if len(valid) == 1:
            q['target_team_id'] = valid[0]['team_id']
            final.append(q)
    print('条件 3 通过频道数: {}'.format(len(final)))
    for q in final[:20]:
        print('  ch={} team={} unattr_videos={}'.format(
            q['channel_id'], q['target_team_id'], q['unattr_videos']))
    print()

    if not final:
        print('❌ 无候选满足 1+2+3')
        conn2.close(); ssh2.close()
        return

    # ===== Step 4: 为每个 final 频道挑 3 个 team_id 匹配的视频 =====
    print('=' * 80)
    print('Step 4: 视频归属 team_id 与当月频道 team_id 一致的 ≥3 条视频')
    print('=' * 80)

    best = []  # 存 (channel, [3 videos])
    ssh_f, conn_f = connect('silverdawn_finance')
    cf = conn_f.cursor(pymysql.cursors.DictCursor)

    for q in final:
        ch = q['channel_id']
        tteam = q['target_team_id']
        # 查该频道 2026-01 unattributed 的视频 id 列表 + ratio
        cf.execute("""
            SELECT target_video_id, revenue, v_revenue_ratio, v_sg_revenue_ratio
            FROM yt_month_channel_revenue_source
            WHERE target_channel_id=%s AND month=%s AND pipeline_id='unattributed'
            ORDER BY revenue DESC
            LIMIT 50
        """, (ch, MONTH))
        unatt_videos = cf.fetchall()
        vids = [r['target_video_id'] for r in unatt_videos]
        if not vids:
            continue
        # 去 distribution 查 video_composition
        ph = ','.join(['%s'] * len(vids))
        c2.execute("""
            SELECT video_id, team_id, composition_name, ams_composition_id, related, deleted
            FROM video_composition
            WHERE video_id IN ({}) AND channel_id=%s
        """.format(ph), vids + [ch])
        vc_rows = c2.fetchall()
        vc_map = {r['video_id']: r for r in vc_rows if r['deleted'] == 0}
        # 匹配 team_id
        matched = []
        for rv in unatt_videos:
            vid = rv['target_video_id']
            vc = vc_map.get(vid)
            if vc and vc['team_id'] == tteam:
                matched.append({
                    'video_id': vid,
                    'revenue': rv['revenue'],
                    'v_revenue_ratio': rv['v_revenue_ratio'],
                    'v_sg_revenue_ratio': rv['v_sg_revenue_ratio'],
                    'composition_name': vc['composition_name'],
                    'ams_composition_id': vc['ams_composition_id'],
                })
            if len(matched) >= 3:
                break
        if len(matched) >= 3:
            best.append({
                'channel': q,
                'videos': matched,
            })

    conn_f.close(); ssh_f.close()
    conn2.close(); ssh2.close()

    print('最终全条件通过频道数: {}'.format(len(best)))
    print()

    # ===== 输出 top 5 =====
    print('=' * 80)
    print('🎯 推荐替代候选 (Top 5)')
    print('=' * 80)
    for i, b in enumerate(best[:5]):
        ch = b['channel']
        print('\n### 候选 #{} ####'.format(i + 1))
        print('channel_id: {}'.format(ch['channel_id']))
        print('channel_name: {}'.format(ch['channel_name']))
        print('冲销父行 id: {}'.format(ch['id']))
        print('  channel_split_status: {}'.format(ch.get('channel_split_status', 0)))
        print('  settlement_created_status: {}'.format(ch['settlement_created_status']))
        print('  unattributed_revenue: ${}'.format(ch['unattributed_revenue']))
        print('target_channel team_id: {}'.format(ch['target_team_id']))
        print('频道共 {} 条 unattributed 视频'.format(ch['unattr_videos']))
        print('推荐 3 个视频:')
        for v in b['videos']:
            print('  - {} | revenue=${} | ratio={} | composition={} | ams_id={}'.format(
                v['video_id'], v['revenue'], v['v_revenue_ratio'],
                v['composition_name'], v['ams_composition_id']))

if __name__ == '__main__':
    run()
