"""
冒烟测试数据查询脚本 v2 - 先探测schema再查询
通过pymysql连接数据库，查询所有冒烟测试用例所需数据
"""
import pymysql
import json

DB_CONFIG = {
    'host': '172.16.24.61',
    'port': 3306,
    'user': 'xiaowu_db',
    'password': '}C7n%7Wklq6P',
    'charset': 'utf8mb4'
}


def get_columns(cur, schema, table):
    """获取指定表的所有列名"""
    cur.execute(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
        (schema, table)
    )
    return [r['COLUMN_NAME'] for r in cur.fetchall()]


def dump_rows(rows, label=""):
    """打印查询结果"""
    if label:
        print(label)
    for r in rows:
        print(json.dumps(r, ensure_ascii=False, default=str))


def run_queries():
    """执行所有冒烟测试相关的数据库查询"""
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    # ========== 0. 探测所有相关表的schema ==========
    tables_to_check = [
        ('silverdawn_ams', 'video_takedown_task'),
        ('silverdawn_ams', 'video_takedown_task_composition'),
        ('silverdawn_ams', 'video_takedown_task_detail'),
        ('silverdawn_ams', 'ams_composition'),
        ('silverdawn_ams', 'ams_oversea_channel'),
        ('silverdawn_ams', 'composition_allocate_detail'),
        ('silverdawn_ams', 'composition_terminate'),
        ('dispatcher', 'video_takedown_queue'),
    ]
    schema_map = {}
    print("=" * 60)
    print("0. TABLE SCHEMA DISCOVERY")
    print("=" * 60)
    for db, tbl in tables_to_check:
        cols = get_columns(cur, db, tbl)
        key = f"{db}.{tbl}"
        schema_map[key] = cols
        if cols:
            print(f"\n[{key}] ({len(cols)} columns):")
            print(f"  {', '.join(cols)}")
        else:
            print(f"\n[{key}] NOT FOUND or NO COLUMNS")

    # ========== 1. 任务单数据 ==========
    print("\n" + "=" * 60)
    print("1. VIDEO_TAKEDOWN_TASK (最近20条)")
    print("=" * 60)
    cur.execute("SELECT * FROM silverdawn_ams.video_takedown_task ORDER BY created_at DESC LIMIT 20")
    dump_rows(cur.fetchall())

    print("\n--- 1.1 任务单状态分布 ---")
    cur.execute("SELECT status, COUNT(*) as cnt FROM silverdawn_ams.video_takedown_task GROUP BY status")
    dump_rows(cur.fetchall())
    cur.execute("SELECT COUNT(*) as total FROM silverdawn_ams.video_takedown_task")
    print(f"Total tasks: {cur.fetchone()['total']}")

    # ========== 2. 任务单关联作品 ==========
    print("\n" + "=" * 60)
    print("2. VIDEO_TAKEDOWN_TASK_COMPOSITION (最近20条)")
    print("=" * 60)
    cur.execute("SELECT * FROM silverdawn_ams.video_takedown_task_composition ORDER BY id DESC LIMIT 20")
    dump_rows(cur.fetchall())

    # ========== 3. 任务单视频明细 ==========
    print("\n" + "=" * 60)
    print("3. VIDEO_TAKEDOWN_TASK_DETAIL (最近30条)")
    print("=" * 60)
    cur.execute("SELECT * FROM silverdawn_ams.video_takedown_task_detail ORDER BY id DESC LIMIT 30")
    dump_rows(cur.fetchall())

    # ========== 4. 作品信息 ==========
    print("\n" + "=" * 60)
    print("4. AMS_COMPOSITION")
    print("=" * 60)
    ams_comp_cols = schema_map.get('silverdawn_ams.ams_composition', [])
    # 查找包含 name 的列
    name_cols = [c for c in ams_comp_cols if 'name' in c.lower()]
    print(f"Name-related columns: {name_cols}")

    # 先查看几条样本数据
    print("\n--- 4.1 样本数据(前5条) ---")
    cur.execute("SELECT * FROM silverdawn_ams.ams_composition LIMIT 5")
    dump_rows(cur.fetchall())

    # 搜索 亚历山大moto - 尝试所有可能的name列
    print("\n--- 4.2 搜索亚历山大moto ---")
    for col in name_cols:
        try:
            cur.execute(f"SELECT * FROM silverdawn_ams.ams_composition WHERE `{col}` LIKE %s LIMIT 5", ('%亚历山大moto%',))
            rows = cur.fetchall()
            if rows:
                print(f"Found via column '{col}':")
                dump_rows(rows)
        except Exception as e:
            print(f"Error querying column '{col}': {e}")

    # ========== 5. 频道信息 ==========
    print("\n" + "=" * 60)
    print("5. AMS_OVERSEA_CHANNEL")
    print("=" * 60)
    try:
        cur.execute("SELECT * FROM silverdawn_ams.ams_oversea_channel WHERE id = 'UClDJc5bJntyxdJoHB94GVgg'")
        rows = cur.fetchall()
        if rows:
            dump_rows(rows)
        else:
            print("Channel UClDJc5bJntyxdJoHB94GVgg NOT FOUND")
            # 查找样本数据
            print("--- Sample channels ---")
            cur.execute("SELECT * FROM silverdawn_ams.ams_oversea_channel LIMIT 5")
            dump_rows(cur.fetchall())
    except Exception as e:
        print(f"Error: {e}")

    # ========== 6. 分销商列表 ==========
    print("\n" + "=" * 60)
    print("6. DISTRIBUTOR LIST (from composition_allocate_detail)")
    print("=" * 60)
    alloc_cols = schema_map.get('silverdawn_ams.composition_allocate_detail', [])
    # 检查是否有 team_name, composition_name 等列
    print(f"Allocate detail columns: {', '.join(alloc_cols[:15])}...")

    try:
        cur.execute("""
            SELECT team_name, team_id, COUNT(DISTINCT composition_id) as work_count
            FROM silverdawn_ams.composition_allocate_detail
            WHERE is_terminate = 0
            GROUP BY team_name, team_id
            ORDER BY work_count DESC
        """)
        dump_rows(cur.fetchall())
    except Exception as e:
        print(f"Error: {e}")
        # fallback: 查看样本
        cur.execute("SELECT * FROM silverdawn_ams.composition_allocate_detail LIMIT 3")
        dump_rows(cur.fetchall(), "--- Sample allocate_detail ---")

    # ========== 7. HELLO BEAR 分配作品 ==========
    print("\n" + "=" * 60)
    print("7. HELLO BEAR WORKS (top 10)")
    print("=" * 60)
    try:
        cur.execute("""
            SELECT composition_id, composition_name
            FROM silverdawn_ams.composition_allocate_detail
            WHERE team_name = 'HELLO BEAR' AND is_terminate = 0
            ORDER BY composition_id LIMIT 10
        """)
        dump_rows(cur.fetchall())
        cur.execute("""
            SELECT COUNT(DISTINCT composition_id) as cnt
            FROM silverdawn_ams.composition_allocate_detail
            WHERE team_name='HELLO BEAR' AND is_terminate=0
        """)
        print(f"HELLO BEAR total works: {cur.fetchone()['cnt']}")
    except Exception as e:
        print(f"Error: {e}")

    # ========== 8. 解约单数据 ==========
    print("\n" + "=" * 60)
    print("8. COMPOSITION_TERMINATE")
    print("=" * 60)
    term_cols = schema_map.get('silverdawn_ams.composition_terminate', [])
    time_col = 'created_at' if 'created_at' in term_cols else 'create_time'

    try:
        cur.execute(f"SELECT * FROM silverdawn_ams.composition_terminate ORDER BY `{time_col}` DESC LIMIT 10")
        dump_rows(cur.fetchall())

        cur.execute("SELECT COUNT(*) as total FROM silverdawn_ams.composition_terminate")
        print(f"Total termination orders: {cur.fetchone()['total']}")

        # 统计 need_takedown 分布
        if 'need_takedown' in term_cols:
            cur.execute("SELECT need_takedown, COUNT(*) as cnt FROM silverdawn_ams.composition_terminate GROUP BY need_takedown")
            dump_rows(cur.fetchall(), "\n--- need_takedown distribution ---")

        # 统计 terminate_type 分布
        if 'terminate_type' in term_cols:
            cur.execute("SELECT terminate_type, COUNT(*) as cnt FROM silverdawn_ams.composition_terminate GROUP BY terminate_type")
            dump_rows(cur.fetchall(), "\n--- terminate_type distribution ---")
    except Exception as e:
        print(f"Error: {e}")

    # ========== 9. Dispatcher队列 ==========
    print("\n" + "=" * 60)
    print("9. DISPATCHER QUEUE")
    print("=" * 60)
    disp_cols = schema_map.get('dispatcher.video_takedown_queue', [])
    if disp_cols:
        try:
            cur.execute("SELECT * FROM dispatcher.video_takedown_queue ORDER BY id DESC LIMIT 20")
            dump_rows(cur.fetchall())

            cur.execute("SELECT queue_status, COUNT(*) as cnt FROM dispatcher.video_takedown_queue GROUP BY queue_status")
            dump_rows(cur.fetchall(), "\n--- queue_status distribution ---")

            cur.execute("SELECT COUNT(*) as total FROM dispatcher.video_takedown_queue")
            print(f"Total queue entries: {cur.fetchone()['total']}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Table dispatcher.video_takedown_queue NOT FOUND")

    # ========== 10. 亚历山大moto 分配检查 ==========
    print("\n" + "=" * 60)
    print("10. 亚历山大moto ALLOCATION CHECK")
    print("=" * 60)
    try:
        cur.execute("""
            SELECT team_name, team_id, composition_name, composition_id, is_terminate
            FROM silverdawn_ams.composition_allocate_detail
            WHERE composition_name LIKE %s
        """, ('%亚历山大moto%',))
        rows = cur.fetchall()
        if rows:
            dump_rows(rows)
        else:
            print("亚历山大moto NOT allocated to any distributor")
    except Exception as e:
        print(f"Error: {e}")

    # ========== 11. 可用于测试的作品（有分配记录且未解约的） ==========
    print("\n" + "=" * 60)
    print("11. WORKS WITH ALLOCATION (未解约, 前20条)")
    print("=" * 60)
    try:
        cur.execute("""
            SELECT composition_id, composition_name, team_name, team_id
            FROM silverdawn_ams.composition_allocate_detail
            WHERE is_terminate = 0
            ORDER BY id DESC LIMIT 20
        """)
        dump_rows(cur.fetchall())
    except Exception as e:
        print(f"Error: {e}")

    conn.close()
    print("\n" + "=" * 60)
    print("=== ALL QUERIES COMPLETED ===")
    print("=" * 60)


if __name__ == '__main__':
    run_queries()
