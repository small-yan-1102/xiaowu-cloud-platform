# -*- coding: utf-8 -*-
"""找作品「不蓝姬」的所有视频 + 当前 pipeline_id"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko, pymysql

WORK_NAME = '不蓝姬'

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

def dump(rows, label):
    print('-' * 70)
    print('{} (n={})'.format(label, len(rows)))
    for r in rows:
        for k, v in r.items():
            print('  {}: {}'.format(k, v))
        print()

def run():
    # ===== 1) AMS 作品 =====
    ssh, conn = connect('silverdawn_ams')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("SELECT id, name, copyright_holder, cp_type FROM ams_composition WHERE name LIKE %s",
                ('%' + WORK_NAME + '%',))
    comps = cur.fetchall()
    dump(comps, 'ams_composition 匹配')
    ams_ids = [c['id'] for c in comps]
    print('ams_composition.id: {}'.format(ams_ids))
    conn.close(); ssh.close()
    print()

    if not ams_ids:
        print('作品不存在')
        return

    # ===== 2) 分销端 video_composition =====
    ssh, conn = connect('silverdawn_distribution')
    cur = conn.cursor(pymysql.cursors.DictCursor)

    ph = ','.join(['%s'] * len(ams_ids))
    print('=' * 80)
    print('【video_composition】作品的视频记录（关键：pipeline_id 列）')
    print('=' * 80)
    cur.execute("""
        SELECT id, video_id, channel_id, team_id, composition_name,
               ams_composition_id, pipeline_id, related, deleted
        FROM video_composition
        WHERE ams_composition_id IN ({})
        ORDER BY id
    """.format(ph), ams_ids)
    vcs = cur.fetchall()
    print('video_composition 记录数: {}'.format(len(vcs)))
    has_pipeline = 0
    has_null = 0
    for r in vcs:
        tag = '✅ 有' if r['pipeline_id'] else '⚠️ 空'
        if r['pipeline_id']:
            has_pipeline += 1
        else:
            has_null += 1
        print('  id={} vid={} ch={} team={} pipeline={} related={} deleted={} {}'.format(
            r['id'], r['video_id'], r['channel_id'], r['team_id'],
            r['pipeline_id'], r['related'], r['deleted'], tag))
    print()
    print('pipeline 非空: {}, 空: {}'.format(has_pipeline, has_null))
    print()

    vc_ids = [r['id'] for r in vcs if r['pipeline_id']]

    # ===== 3) 这些视频对应的 overdue 记录 =====
    vids = [r['video_id'] for r in vcs]
    if vids:
        print('=' * 80)
        print('【video_composition_overdue】这些视频的 overdue 状态')
        print('=' * 80)
        # finance 库的 overdue 表
        conn.close(); ssh.close()
        ssh2, conn2 = connect('silverdawn_finance')
        cur2 = conn2.cursor(pymysql.cursors.DictCursor)
        ph2 = ','.join(['%s'] * len(vids))
        cur2.execute("""
            SELECT id, video_id, channel_id, receipted_month, status,
                   pipeline_id, team_name, deleted
            FROM video_composition_overdue
            WHERE video_id IN ({})
            ORDER BY video_id, receipted_month
        """.format(ph2), vids)
        ov_rows = cur2.fetchall()
        print('overdue 记录数: {}'.format(len(ov_rows)))
        for r in ov_rows:
            print('  id={} vid={} ch={} month={} status={} pipe={} deleted={}'.format(
                r['id'], r['video_id'], r['channel_id'], r['receipted_month'],
                r['status'], r['pipeline_id'], r['deleted']))
        conn2.close(); ssh2.close()
        print()

    print('=' * 80)
    print('🎯 需要 UPDATE 的 video_composition.id: {}'.format(vc_ids))
    print('=' * 80)

if __name__ == '__main__':
    run()
