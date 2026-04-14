"""
AMS 视频下架测试 - 数据库验证脚本
用于在测试执行过程中验证数据库状态
连接方式：SSH隧道（172.16.24.200 跳板 → 172.16.24.61 数据库）
"""

import paramiko
import pymysql
import json
from datetime import datetime


def create_db_connection():
    """
    通过SSH隧道创建数据库连接
    跳板机: 172.16.24.200 (test/wgu4&Q_2)
    数据库: 172.16.24.61:3306 (xiaowu_db/}C7n%7Wklq6P)
    """
    # SSH连接跳板机
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('172.16.24.200', port=22, username='test', password='wgu4&Q_2')

    # 创建SSH通道到数据库
    transport = ssh.get_transport()
    channel = transport.open_channel(
        'direct-tcpip',
        ('172.16.24.61', 3306),
        ('127.0.0.1', 0)
    )

    # 通过SSH通道连接MySQL
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='xiaowu_db',
        password='}C7n%7Wklq6P',
        database='silverdawn_ams',
        charset='utf8mb4',
        defer_connect=True
    )
    conn.connect(channel)

    return conn, ssh


def verify_termination_list():
    """
    验证解约单列表数据完整性
    对应用例: AMS-TER-001
    """
    conn, ssh = create_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询解约单总数
            cursor.execute("SELECT COUNT(*) as total FROM composition_terminate")
            total = cursor.fetchone()['total']
            print(f"[TER-001] 解约单总数: {total}")

            # 查询解约类型分布
            cursor.execute("""
                SELECT terminate_type, COUNT(*) as cnt
                FROM composition_terminate
                GROUP BY terminate_type
            """)
            types = cursor.fetchall()
            print(f"[TER-001] 解约类型分布: {json.dumps(types, default=str, ensure_ascii=False)}")

            # 查询有联动下架的解约单
            cursor.execute("""
                SELECT code, terminate_type, team_name, need_takedown, takedown_task_code
                FROM composition_terminate
                WHERE need_takedown = 1
                ORDER BY created_at DESC
            """)
            linked = cursor.fetchall()
            print(f"[TER-001] 联动下架解约单: {len(linked)} 条")
            for r in linked:
                print(f"  - {r['code']}: {r['team_name']}, 任务单={r['takedown_task_code']}")

            return {'total': total, 'types': types, 'linked': linked}
    finally:
        conn.close()
        ssh.close()


def verify_task_creation(task_code):
    """
    验证任务单创建状态
    对应用例: AMS-TER-003, AMS-TER-022 创建后的任务单验证
    """
    conn, ssh = create_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT t.code, t.status, t.process_method, t.takedown_reason,
                       t.create_source, t.terminate_id,
                       COUNT(c.id) as composition_count
                FROM video_takedown_task t
                LEFT JOIN video_takedown_task_composition c ON t.id = c.task_id
                WHERE t.code = %s
                GROUP BY t.id
            """, (task_code,))
            task = cursor.fetchone()
            if task:
                print(f"[任务单验证] {task_code}:")
                print(f"  状态={task['status']}, 处理方式={task['process_method']}")
                print(f"  下架原因={task['takedown_reason']}, 创建来源={task['create_source']}")
                print(f"  关联解约单ID={task['terminate_id']}, 作品数={task['composition_count']}")
            else:
                print(f"[任务单验证] {task_code}: 未找到")
            return task
    finally:
        conn.close()
        ssh.close()


def verify_termination_detail(terminate_code):
    """
    验证解约单详情数据
    对应用例: AMS-TER-008, AMS-TER-015, AMS-TER-016
    """
    conn, ssh = create_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT ct.code, ct.terminate_type, ct.team_name, ct.reason,
                       ct.terminate_date, ct.need_takedown,
                       ct.takedown_reason, ct.takedown_description,
                       ct.process_method, ct.takedown_deadline_date,
                       ct.takedown_task_code,
                       ct.created_user_id, ct.created_at
                FROM composition_terminate ct
                WHERE ct.code = %s
            """, (terminate_code,))
            detail = cursor.fetchone()

            if detail:
                # 查询关联作品
                cursor.execute("""
                    SELECT cad.composition_id, cad.composition_name
                    FROM composition_allocate_detail cad
                    JOIN composition_terminate_detail ctd ON ctd.allocate_detail_id = cad.id
                    WHERE ctd.terminate_id = (
                        SELECT id FROM composition_terminate WHERE code = %s
                    )
                """, (terminate_code,))
                compositions = cursor.fetchall()
                print(f"[解约单详情] {terminate_code}:")
                print(f"  解约类型={detail['terminate_type']}, 分销商={detail['team_name']}")
                print(f"  需下架={detail['need_takedown']}, 关联任务单={detail['takedown_task_code']}")
                print(f"  关联作品数: {len(compositions)}")
                return {'detail': detail, 'compositions': compositions}
            else:
                print(f"[解约单详情] {terminate_code}: 未找到")
                return None
    finally:
        conn.close()
        ssh.close()


def verify_all_tasks():
    """
    查询所有任务单当前状态
    用于 specification 和 quota_execution 套件的前置数据验证
    """
    conn, ssh = create_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT t.code, t.status, t.process_method, t.takedown_reason,
                       t.create_source, t.task_source,
                       COUNT(d.id) as video_count,
                       SUM(CASE WHEN d.video_status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_count,
                       SUM(CASE WHEN d.video_status = 'FAILED' THEN 1 ELSE 0 END) as failed_count
                FROM video_takedown_task t
                LEFT JOIN video_takedown_task_detail d ON t.id = d.task_id
                GROUP BY t.id
                ORDER BY t.code
            """)
            tasks = cursor.fetchall()
            print(f"\n{'='*80}")
            print(f"任务单状态总览 (共 {len(tasks)} 条)")
            print(f"{'='*80}")
            for t in tasks:
                print(f"  {t['code']}: status={t['status']}, method={t['process_method']}, "
                      f"videos={t['video_count']}(完成{t['completed_count']}/失败{t['failed_count']})")
            return tasks
    finally:
        conn.close()
        ssh.close()


def verify_dispatcher_queue():
    """
    查询分发调度队列状态
    对应 specification 套件的执行校验相关用例
    """
    conn, ssh = create_db_connection()
    try:
        # 切换到 dispatcher 数据库
        conn.select_db('dispatcher')
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT video_id, queue_status, process_method,
                       execute_time, complete_time, retry_count, status_detail
                FROM video_takedown_queue
                ORDER BY id DESC
            """)
            records = cursor.fetchall()
            print(f"\n{'='*80}")
            print(f"分发调度队列 (共 {len(records)} 条)")
            print(f"{'='*80}")
            for r in records:
                print(f"  video={r['video_id']}: status={r['queue_status']}, "
                      f"method={r['process_method']}, retry={r['retry_count']}")
            return records
    finally:
        conn.close()
        ssh.close()


if __name__ == '__main__':
    print("=" * 80)
    print(f"AMS 测试数据库验证 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    print("\n--- 1. 解约单列表验证 ---")
    verify_termination_list()

    print("\n--- 2. 任务单状态总览 ---")
    verify_all_tasks()

    print("\n--- 3. 分发调度队列 ---")
    verify_dispatcher_queue()
