# -*- coding: utf-8 -*-
"""作品「后妈变盟友」+ 视频 S5UXSb4EGQY 登记后的数据链路"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

AMS_COMP_ID = 100965
VIDEO_ID = 'S5UXSb4EGQY'

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
    ssh, conn = connect_db('silverdawn_distribution')
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # 1) video_composition 查 ams_composition_id 和 video_id
    print('=' * 80)
    print('【1】video_composition (按 ams_composition_id=100965)')
    print('=' * 80)
    cur.execute("SELECT * FROM video_composition WHERE ams_composition_id=%s", (AMS_COMP_ID,))
    dump(cur.fetchall(), 'video_composition by ams_composition_id')
    print()

    print('=' * 80)
    print('【2】video_composition (按 video_id={})'.format(VIDEO_ID))
    print('=' * 80)
    cur.execute("SELECT * FROM video_composition WHERE video_id=%s", (VIDEO_ID,))
    vc_rows = cur.fetchall()
    dump(vc_rows, 'video_composition by video_id')
    channel_ids = list(set(r.get('channel_id') for r in vc_rows if r.get('channel_id')))
    team_ids = list(set(r.get('team_id') for r in vc_rows if r.get('team_id')))
    print('📌 video 关联 channel_id: {}'.format(channel_ids))
    print('📌 video 关联 team_id: {}'.format(team_ids))
    print()

    # 3) target_channel 频道归属
    if channel_ids:
        print('=' * 80)
        print('【3】target_channel (频道归属)')
        print('=' * 80)
        ph = ','.join(['%s'] * len(channel_ids))
        cur.execute("SELECT * FROM target_channel WHERE channel_id IN ({})".format(ph), channel_ids)
        dump(cur.fetchall(), 'target_channel')
        print()

    # 4) composition 镜像再查一次
    print('=' * 80)
    print('【4】composition 镜像（分销端）')
    print('=' * 80)
    cur.execute("SELECT id, ams_composition_id, name, team_id, operated, terminate_date, terminate_type FROM composition WHERE ams_composition_id=%s", (AMS_COMP_ID,))
    dump(cur.fetchall(), 'composition')
    print()

    # 5) video_takedown_record
    print('=' * 80)
    print('【5】video_takedown_record')
    print('=' * 80)
    cur.execute("SELECT * FROM video_takedown_record WHERE ams_composition_id=%s OR video_id=%s", (AMS_COMP_ID, VIDEO_ID))
    dump(cur.fetchall(), 'video_takedown_record')
    print()

    conn.close(); ssh.close()

if __name__ == '__main__':
    run()
