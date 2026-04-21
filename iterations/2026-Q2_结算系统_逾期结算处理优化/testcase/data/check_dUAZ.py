# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import paramiko, pymysql

VID = 'dUAZ4_KEM5g'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('172.16.24.200', port=22, username='test', password='wgu4&Q_2')
tr = ssh.get_transport()
ch = tr.open_channel('direct-tcpip', ('172.16.24.61', 3306), ('127.0.0.1', 0))
conn = pymysql.connect(host='127.0.0.1', port=3306, user='xiaowu_db',
                       password='}C7n%7Wklq6P', database='silverdawn_finance',
                       charset='utf8mb4', defer_connect=True)
conn.connect(ch)
cur = conn.cursor(pymysql.cursors.DictCursor)

print('=== overdue ===')
cur.execute("""
    SELECT id, video_id, channel_id, receipted_month, status, original_status,
           pipeline_id, deleted, updated_at
    FROM video_composition_overdue
    WHERE video_id=%s
""", (VID,))
rows = cur.fetchall()
for r in rows:
    print(r)

pipes = [r['pipeline_id'] for r in rows if r['pipeline_id']]
if pipes:
    print()
    print('=== yt_reversal_report same pipeline ===')
    ph = ','.join(['%s'] * len(pipes))
    cur.execute("""
        SELECT id, channel_id, month, channel_type, pipeline_id,
               channel_split_status, settlement_created_status,
               unattributed_revenue, created_at
        FROM yt_reversal_report
        WHERE pipeline_id IN ({})
        ORDER BY id
    """.format(ph), pipes)
    for r in cur.fetchall():
        print(r)

conn.close(); ssh.close()
