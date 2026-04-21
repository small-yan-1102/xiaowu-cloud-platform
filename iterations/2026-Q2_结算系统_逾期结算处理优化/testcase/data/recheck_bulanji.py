# -*- coding: utf-8 -*-
"""重新查询 不蓝姬 的 pipeline_id，找所有可能的存储位置"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko, pymysql

AMS_ID = 100883
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
    # ===== 1) silverdawn_distribution.video_composition =====
    print('=' * 80)
    print('【1】silverdawn_distribution.video_composition（你刚 UPDATE 的表）')
    print('=' * 80)
    ssh, conn = connect('silverdawn_distribution')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT id, video_id, channel_id, ams_composition_id, pipeline_id, deleted, updated_at
        FROM video_composition
        WHERE ams_composition_id=%s
    """, (AMS_ID,))
    for r in cur.fetchall():
        print('  id={} vid={} ch={} pipeline={} deleted={} updated={}'.format(
            r['id'], r['video_id'], r['channel_id'],
            r['pipeline_id'], r['deleted'], r['updated_at']))
    print()

    # ===== 1b) distribution 库内所有包含 pipeline_id 列 + 有对应 video_id 的表 =====
    print('=' * 80)
    print('【1b】silverdawn_distribution 中所有 pipeline_id 列的表，该视频/作品是否有记录')
    print('=' * 80)
    cur.execute("""
        SELECT TABLE_NAME FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA='silverdawn_distribution' AND COLUMN_NAME='pipeline_id'
    """)
    tables = [r['TABLE_NAME'] for r in cur.fetchall()]
    print('含 pipeline_id 列的表: {}'.format(tables))
    print()
    for t in tables:
        # 确定能否按 video_id 查
        cur.execute("""
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA='silverdawn_distribution' AND TABLE_NAME=%s
        """, (t,))
        cols = [r['COLUMN_NAME'] for r in cur.fetchall()]
        ph = ','.join(['%s'] * len(VIDS))
        if 'video_id' in cols:
            cur.execute("""
                SELECT id, video_id, pipeline_id, deleted
                FROM `{}` WHERE video_id IN ({}) LIMIT 20
            """.format(t, ph), VIDS)
            rows = cur.fetchall()
            if rows:
                print('  >>> {}: 命中 {} 条'.format(t, len(rows)))
                for r in rows:
                    print('      id={} vid={} pipeline={} deleted={}'.format(
                        r.get('id'), r.get('video_id'), r.get('pipeline_id'), r.get('deleted')))
        if 'ams_composition_id' in cols:
            cur.execute("""
                SELECT id, ams_composition_id, pipeline_id
                FROM `{}` WHERE ams_composition_id=%s LIMIT 20
            """.format(t), (AMS_ID,))
            rows = cur.fetchall()
            if rows:
                print('  >>> {} (by ams_composition_id): 命中 {} 条'.format(t, len(rows)))
                for r in rows:
                    print('      id={} ams_id={} pipeline={}'.format(
                        r.get('id'), r.get('ams_composition_id'), r.get('pipeline_id')))
    conn.close(); ssh.close()
    print()

    # ===== 2) silverdawn_finance 库包含 pipeline_id 的表 =====
    print('=' * 80)
    print('【2】silverdawn_finance 库的 pipeline_id（overdue + revenue_source + reversal）')
    print('=' * 80)
    ssh, conn = connect('silverdawn_finance')
    cur = conn.cursor(pymysql.cursors.DictCursor)
    ph = ','.join(['%s'] * len(VIDS))

    print('-- video_composition_overdue --')
    cur.execute("""
        SELECT id, video_id, channel_id, receipted_month, status, pipeline_id, deleted
        FROM video_composition_overdue
        WHERE video_id IN ({})
    """.format(ph), VIDS)
    for r in cur.fetchall():
        print('  id={} vid={} ch={} month={} status={} pipeline={} deleted={}'.format(
            r['id'], r['video_id'], r['channel_id'], r['receipted_month'],
            r['status'], r['pipeline_id'], r['deleted']))

    print()
    print('-- yt_month_channel_revenue_source --')
    cur.execute("""
        SELECT target_video_id, month, target_channel_id, pipeline_id, revenue
        FROM yt_month_channel_revenue_source
        WHERE target_video_id IN ({})
    """.format(ph), VIDS)
    for r in cur.fetchall():
        print('  vid={} month={} ch={} pipeline={} revenue={}'.format(
            r['target_video_id'], r['month'], r['target_channel_id'],
            r['pipeline_id'], r['revenue']))

    conn.close(); ssh.close()

if __name__ == '__main__':
    run()
