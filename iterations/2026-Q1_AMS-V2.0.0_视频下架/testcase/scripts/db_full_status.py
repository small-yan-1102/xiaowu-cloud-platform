"""完整数据状态查询"""
import pymysql

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

def q(cur, sql, label=''):
    if label:
        print(f'\n=== {label} ===')
    cur.execute(sql)
    rows = cur.fetchall()
    if cur.description and rows:
        cols = [d[0] for d in cur.description]
        print('\t'.join(cols))
        for r in rows:
            vals = []
            for v in r:
                s = str(v) if v is not None else 'NULL'
                if len(s) > 60:
                    s = s[:57] + '...'
                vals.append(s)
            print('\t'.join(vals))
    elif not rows:
        print('(empty)')
    return rows

def main():
    conn = pymysql.connect(**DB, database='silverdawn_ams')
    c = conn.cursor()

    # 全部任务单
    q(c, "SELECT code, status, process_method, takedown_reason, "
         "create_source, create_type, task_source, team_id, team_name, "
         "IFNULL(create_fail_reason,'') as fail_reason, "
         "created_at "
         "FROM video_takedown_task ORDER BY created_at ASC",
      '全部任务单')

    # 各状态汇总
    q(c, "SELECT status, COUNT(*) as cnt FROM video_takedown_task GROUP BY status ORDER BY cnt DESC",
      '状态汇总')

    # 视频明细
    q(c, "SELECT vt.code, vtd.video_id, vtd.status as detail_status, vtd.process_method "
         "FROM video_takedown_task_detail vtd "
         "JOIN video_takedown_task vt ON vtd.task_id = vt.id "
         "ORDER BY vt.code, vtd.id LIMIT 30",
      '视频明细(前30条)')

    # 各作品关联
    q(c, "SELECT vt.code, vtc.composition_id, vtc.cp_name, vtc.video_count "
         "FROM video_takedown_task_composition vtc "
         "JOIN video_takedown_task vt ON vtc.task_id = vt.id "
         "ORDER BY vt.code",
      '任务-作品关联')

    # 解约单清单
    q(c, "SELECT id, code, team_name, terminate_type, need_takedown, "
         "takedown_task_code, created_at "
         "FROM composition_terminate ORDER BY created_at DESC LIMIT 10",
      '解约单(最近10条)')

    # 解约单统计
    q(c, "SELECT "
         "COUNT(*) as total, "
         "SUM(CASE WHEN need_takedown=1 THEN 1 ELSE 0 END) as has_takedown, "
         "SUM(CASE WHEN need_takedown IS NULL OR need_takedown=0 THEN 1 ELSE 0 END) as no_takedown "
         "FROM composition_terminate",
      '解约单统计')

    # 可用作品(测试频道)
    q(c, "SELECT apc.composition_id, apc.sign_channel_name, "
         "apc.register_channel_id "
         "FROM ams_publish_channel apc "
         "WHERE apc.register_channel_id IN "
         "('UClDJc5bJntyxdJoHB94GVgg','UCA17JOb1Bo5YQdggQwJN20Q') "
         "ORDER BY apc.composition_id LIMIT 15",
      '测试频道作品')

    # 查 BY_VIDEO_ID 那条卡住的任务单详情
    q(c, "SELECT code, status, create_type, create_fail_reason, "
         "task_source, team_id, created_at, updated_at "
         "FROM video_takedown_task "
         "WHERE create_type='BY_VIDEO_ID'",
      'BY_VIDEO_ID 任务单')

    # 查有哪些作品的视频可用于 BY_VIDEO_ID 创建
    q(c, "SELECT vo.video_id, vo.composition_id, vo.channel_id, vo.status "
         "FROM dispatcher.video_order vo "
         "WHERE vo.channel_id IN "
         "('UClDJc5bJntyxdJoHB94GVgg','UCA17JOb1Bo5YQdggQwJN20Q') "
         "AND vo.status = 'ONLINE' "
         "LIMIT 20",
      'dispatcher可用在线视频')

    conn.close()
    print('\n=== Done ===')

if __name__ == '__main__':
    main()
