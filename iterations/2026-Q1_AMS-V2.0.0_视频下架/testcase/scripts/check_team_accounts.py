# -*- coding: utf-8 -*-
"""查询两个 team 的剧老板登录账号"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import paramiko
import pymysql

TEAMS = ['1988520080772243456', '1988526061061218304']

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
    for r in rows:
        for k, v in r.items():
            print('  {}: {}'.format(k, v))
        print()

def run():
    ssh, conn = connect_db('silverdawn_distribution')
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # team 表 - 用 team_id 字段
    print('=== silverdawn_distribution.team by team_id ===')
    ph = ','.join(['%s'] * len(TEAMS))
    cur.execute("SELECT * FROM team WHERE team_id IN ({})".format(ph), TEAMS)
    dump(cur.fetchall(), 'team')

    # 找 user 和 team 的关联 - 可能有 team_user 表或 user 有 team_id
    cur.execute("""
        SELECT TABLE_NAME FROM information_schema.TABLES
        WHERE TABLE_SCHEMA='silverdawn_distribution' AND TABLE_NAME LIKE '%team%'
    """)
    print('含 team 的表:')
    for r in cur.fetchall():
        print('  - {}'.format(r['TABLE_NAME']))
    print()

    # saas_user_center / silverdawn_user_center
    for db in ['saas_user_center', 'silverdawn_user_center', 'silverdawn_sso']:
        try:
            ssh2, conn2 = connect_db(db)
            c = conn2.cursor(pymysql.cursors.DictCursor)
            # 查 cp_user
            try:
                c.execute("SHOW COLUMNS FROM cp_user")
                cols = [r['Field'] for r in c.fetchall()]
                if 'team_id' in cols:
                    c.execute("SELECT * FROM cp_user WHERE team_id IN ({})".format(ph), TEAMS)
                    dump(c.fetchall(), '{}.cp_user by team_id'.format(db))
            except Exception as e:
                print('{}.cp_user 失败: {}'.format(db, e))
            conn2.close(); ssh2.close()
        except Exception as e:
            print('DB {} 失败: {}'.format(db, e))

    conn.close(); ssh.close()

if __name__ == '__main__':
    run()
