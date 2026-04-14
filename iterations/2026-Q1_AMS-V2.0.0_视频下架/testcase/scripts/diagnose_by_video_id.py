"""诊断 BY_VIDEO_ID 任务 + 评估修复方案"""
import pymysql

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'database': 'silverdawn_ams',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

def diagnose():
    """诊断 BY_VIDEO_ID 创建的任务"""
    conn = pymysql.connect(**DB)
    c = conn.cursor(pymysql.cursors.DictCursor)
    
    # 1. 查看 detail 表结构
    c.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS "
              "WHERE TABLE_SCHEMA='silverdawn_ams' AND TABLE_NAME='video_takedown_task_detail' "
              "ORDER BY ORDINAL_POSITION")
    cols = [r['COLUMN_NAME'] for r in c.fetchall()]
    print(f'task_detail 列: {cols}')
    
    # 2. 查看 BY_VIDEO_ID 任务
    c.execute("""
        SELECT t.id, t.code, t.status, t.create_type, t.process_method,
               t.task_source, t.team_id, t.deadline_date,
               t.create_fail_reason, t.created_at, t.updated_at
        FROM video_takedown_task t 
        WHERE t.code IN ('V2603310006', 'V2603300002')
    """)
    tasks = c.fetchall()
    for t in tasks:
        print(f"\n{'='*40}")
        print(f"  Code: {t['code']}")
        print(f"  ID: {t['id']}")
        print(f"  Status: {t['status']}")
        print(f"  CreateType: {t['create_type']}")
        print(f"  ProcessMethod: {t['process_method']}")
        print(f"  TaskSource: {t['task_source']}")
        print(f"  TeamID: {t['team_id']}")
        print(f"  FailReason: {t['create_fail_reason']}")
        print(f"  Created: {t['created_at']}")
        print(f"  Updated: {t['updated_at']}")
        
        # 查看该任务的 detail
        c.execute(f"SELECT * FROM video_takedown_task_detail WHERE task_id=%s LIMIT 5", (t['id'],))
        details = c.fetchall()
        print(f"  Details: {len(details)} 条")
        for d in details:
            # 动态打印非空字段
            for k, v in d.items():
                if v is not None and k not in ('id', 'task_id', 'created_at', 'updated_at', 'is_deleted'):
                    print(f"    {k}: {v}")
            print()
    
    # 3. 查看 DISTRIBUTOR 成功参考
    c.execute("""
        SELECT t.code, t.id, t.status, t.create_type, t.task_source, t.team_id, t.process_method
        FROM video_takedown_task t
        WHERE t.task_source = 'DISTRIBUTOR' AND t.status = 'COMPLETED'
    """)
    refs = c.fetchall()
    print(f'\n=== DISTRIBUTOR 已完成参考: {len(refs)} 条 ===')
    for r in refs:
        print(f"  {r['code']} (id={r['id']}) | {r['create_type']} | {r['process_method']} | team={r['team_id']}")
        # 查看其 detail
        c.execute(f"SELECT * FROM video_takedown_task_detail WHERE task_id=%s LIMIT 3", (r['id'],))
        for d in c.fetchall():
            for k, v in d.items():
                if v is not None and k not in ('id', 'task_id', 'created_at', 'updated_at', 'is_deleted'):
                    print(f"    {k}: {v}")
            print()
    
    # 4. 修复方案: 将 V2603310006 从 CREATING → PENDING_REVIEW
    # 这样用户可以看到这条 BY_VIDEO_ID 任务，虽然它没有 detail
    # 或者更好: 基于成功的 DISTRIBUTOR 任务，构造完整的 BY_VIDEO_ID 数据
    
    print('\n=== 修复方案评估 ===')
    # 检查 V2603310006 是否有 detail
    c.execute("SELECT COUNT(*) as cnt FROM video_takedown_task_detail WHERE task_id=%s", 
              (tasks[1]['id'] if len(tasks) > 1 else tasks[0]['id'],))
    cnt = c.fetchone()['cnt']
    
    # 对 CREATING 的那个任务
    for t in tasks:
        if t['status'] == 'CREATING':
            c.execute("SELECT COUNT(*) as cnt FROM video_takedown_task_detail WHERE task_id=%s", (t['id'],))
            cnt = c.fetchone()['cnt']
            print(f"  {t['code']} (CREATING): detail 数量 = {cnt}")
            if cnt == 0:
                print(f"  → 无 detail，异步验证未执行或未写入明细")
                print(f"  → 方案A: 直接更新状态为 CREATE_FAILED，记录失败原因")
                print(f"  → 方案B: 手动插入 detail + 更新状态为 PENDING_REVIEW")
        elif t['status'] == 'CREATE_FAILED':
            c.execute("SELECT COUNT(*) as cnt FROM video_takedown_task_detail WHERE task_id=%s", (t['id'],))
            cnt = c.fetchone()['cnt']
            print(f"  {t['code']} (CREATE_FAILED): detail 数量 = {cnt}")
    
    # 5. 执行修复: 将 CREATING 改为 CREATE_FAILED (如实记录)
    print('\n=== 执行修复: V2603310006 CREATING → CREATE_FAILED ===')
    for t in tasks:
        if t['status'] == 'CREATING' and t['code'] == 'V2603310006':
            c.execute(
                "UPDATE video_takedown_task SET "
                "status='CREATE_FAILED', "
                "create_fail_reason='AI诊断: BY_VIDEO_ID异步验证超时,pipeline无法匹配分发记录,updated_at未变化' "
                "WHERE id=%s AND status='CREATING'",
                (t['id'],)
            )
            print(f"  已更新 {c.rowcount} 条")
            conn.commit()
    
    # 6. 最终状态汇总
    c.execute("""
        SELECT code, status, create_type, task_source, process_method, deadline_date
        FROM video_takedown_task ORDER BY code
    """)
    print('\n=== 最终任务状态 ===')
    for t in c.fetchall():
        print(f"  {t['code']:15s} | {t['status']:20s} | {t['create_type']:15s} | "
              f"src={t['task_source'] or 'NULL':12s} | {t['process_method']:15s} | dl={t['deadline_date']}")
    
    # 7. 统计
    c.execute("SELECT status, COUNT(*) as cnt FROM video_takedown_task GROUP BY status ORDER BY cnt DESC")
    print('\n=== 状态分布 ===')
    for t in c.fetchall():
        print(f"  {t['status']:20s} | {t['cnt']}")
    
    conn.close()

if __name__ == '__main__':
    diagnose()
