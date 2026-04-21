# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import paramiko, pymysql

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('172.16.24.200', port=22, username='test', password='wgu4&Q_2')
tr = ssh.get_transport()
ch = tr.open_channel('direct-tcpip', ('172.16.24.61', 3306), ('127.0.0.1', 0))
conn = pymysql.connect(host='127.0.0.1', port=3306, user='xiaowu_db',
                       password='}C7n%7Wklq6P', database='silverdawn_finance',
                       charset='utf8mb4', defer_connect=True)
conn.connect(ch)
c = conn.cursor(pymysql.cursors.DictCursor)
c.execute('''SELECT id, channel_id, month, channel_type, pipeline_id,
    channel_split_status, settlement_created_status, unattributed_revenue, created_at
    FROM yt_reversal_report WHERE id BETWEEN 1138900 AND 1138915 ORDER BY id''')
for r in c.fetchall():
    print('id={} ch={} month={} ch_type={} pipe={} split={} settle={} rev={} created={}'.format(
        r['id'], r['channel_id'], r['month'], r['channel_type'], r['pipeline_id'],
        r['channel_split_status'], r['settlement_created_status'],
        r['unattributed_revenue'], r['created_at']))
conn.close(); ssh.close()
