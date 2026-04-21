# -*- coding: utf-8 -*-
"""查询作品「后妈变盟友」在分销端 silverdawn_distribution 的下架链路"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

WORK_NAME = '后妈变盟友'
AMS_COMP_ID = 100965

def connect_db(database):
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
    if not rows:
        print('  (无)'); return
    for i, r in enumerate(rows):
        print('  #{}'.format(i + 1))
        for k, v in r.items():
            print('    {}: {}'.format(k, v))

def run():
    # ===== AMS allocate_detail =====
    print('=' * 80)
    print('【A】silverdawn_ams.composition_allocate_detail (分销明细)')
    print('=' * 80)
    ssh, conn = connect_db('silverdawn_ams')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SHOW COLUMNS FROM composition_allocate_detail")
    ad_cols = [r['Field'] for r in cur.fetchall()]
    print('字段: {}'.format(', '.join(ad_cols)))
    for f in ['ams_composition_id', 'composition_id', 'composition_ams_id']:
        if f in ad_cols:
            cur.execute("SELECT * FROM composition_allocate_detail WHERE {}=%s".format(f), (AMS_COMP_ID,))
            rows = cur.fetchall()
            dump(rows, 'composition_allocate_detail')
            alloc_ids = list(set(r.get('allocate_id') for r in rows if r.get('allocate_id')))
            if alloc_ids:
                ph = ','.join(['%s'] * len(alloc_ids))
                cur.execute("SELECT * FROM composition_allocate WHERE id IN ({})".format(ph), alloc_ids)
                dump(cur.fetchall(), 'composition_allocate (关联分销单)')
            break
    conn.close(); ssh.close()
    print()

    # ===== Distribution composition =====
    print('=' * 80)
    print('【B】silverdawn_distribution.composition (剧老板端作品镜像)')
    print('=' * 80)
    ssh, conn = connect_db('silverdawn_distribution')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SHOW COLUMNS FROM composition")
    cols = [r['Field'] for r in cur.fetchall()]
    print('composition 字段: {}'.format(', '.join(cols)))
    # 找 ams 映射字段
    name_field = next((c for c in cols if c == 'name' or 'name' in c.lower() and 'holder' not in c.lower()), None)
    cur.execute("SELECT * FROM composition WHERE name LIKE %s", ('%' + WORK_NAME + '%',))
    dist_comps = cur.fetchall()
    dump(dist_comps, 'composition (by name)')
    dist_ids = [r.get('id') for r in dist_comps]
    dist_ams_ids = list(set(r.get('ams_composition_id') for r in dist_comps if r.get('ams_composition_id') is not None))
    dist_team_ids = list(set(r.get('team_id') for r in dist_comps if r.get('team_id')))
    print('📌 distribution.composition.id: {}'.format(dist_ids))
    print('📌 distribution.composition.ams_composition_id: {}'.format(dist_ams_ids))
    print('📌 distribution.composition.team_id: {}'.format(dist_team_ids))
    print()

    # ===== video_composition =====
    print('=' * 80)
    print('【C】silverdawn_distribution.video_composition (视频-作品关联)')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM video_composition")
    vc_cols = [r['Field'] for r in cur.fetchall()]
    print('字段: {}'.format(', '.join(vc_cols)))
    # 试按 ams_composition_id
    for f in ['ams_composition_id', 'composition_id']:
        if f in vc_cols and dist_ams_ids:
            ph = ','.join(['%s'] * len(dist_ams_ids))
            cur.execute("SELECT * FROM video_composition WHERE {} IN ({}) LIMIT 20".format(f, ph), dist_ams_ids)
            dump(cur.fetchall(), 'video_composition (via {})'.format(f))
            break
    print()

    # ===== video_takedown_record =====
    print('=' * 80)
    print('【D】silverdawn_distribution.video_takedown_record (下架记录) ⭐')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM video_takedown_record")
    tr_cols = [r['Field'] for r in cur.fetchall()]
    print('字段: {}'.format(', '.join(tr_cols)))
    # 按 ams_composition_id
    if 'ams_composition_id' in tr_cols:
        cur.execute("SELECT * FROM video_takedown_record WHERE ams_composition_id=%s", (AMS_COMP_ID,))
        rs = cur.fetchall()
        dump(rs, 'video_takedown_record (by ams_composition_id)')
    print()

    # ===== target_channel =====
    print('=' * 80)
    print('【E】silverdawn_distribution.target_channel (频道)')
    print('=' * 80)
    cur.execute("SHOW COLUMNS FROM target_channel")
    tc_cols = [r['Field'] for r in cur.fetchall()]
    print('字段: {}'.format(', '.join(tc_cols)))
    print()

    conn.close(); ssh.close()

if __name__ == '__main__':
    run()
