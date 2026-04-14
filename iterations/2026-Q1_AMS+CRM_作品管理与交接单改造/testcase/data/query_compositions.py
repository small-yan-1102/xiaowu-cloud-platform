"""
查询 silverdawn_ams 数据库中可用的作品数据
用于「作品管理与交接单改造」迭代的测试数据准备

ams_composition 表结构关键字段：
  id, name, type, specification, cp_type,
  allocate_status, internal_publish, 
  first_publish_time_type, first_publish_time,
  channel_limit, subtitle_lang_config, dubbing_lang_config,
  business_id, customer_id, category_id, ...
"""
import pymysql
import sys
import io

# 修复 Windows 控制台 GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_CONFIG = {
    'host': '172.16.24.61',
    'port': 3306,
    'user': 'xiaowu_db',
    'password': '}C7n%7Wklq6P',
    'database': 'silverdawn_ams',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def query_db(sql, params=None):
    """执行 SQL 查询并返回结果"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def section(title):
    """打印分隔标题"""
    print()
    print("=" * 100)
    print(f"  {title}")
    print("=" * 100)


# ==================== 1. AMS 作品统计 ====================

def show_ams_stats():
    """AMS 作品数据分布统计"""
    section("1. ams_composition 数据统计 (总量 874)")

    total = query_db("SELECT COUNT(*) as cnt FROM ams_composition")
    print(f"  总记录数: {total[0]['cnt']}")

    # 按 type 统计
    stats = query_db("SELECT IFNULL(type,'NULL') as t, COUNT(*) as cnt FROM ams_composition GROUP BY type ORDER BY cnt DESC")
    print(f"\n  按作品类型 (type):")
    for r in stats:
        print(f"    type={r['t']}: {r['cnt']} 条")

    # 按 specification 统计
    stats = query_db("SELECT IFNULL(specification,'NULL') as t, COUNT(*) as cnt FROM ams_composition GROUP BY specification ORDER BY cnt DESC")
    print(f"\n  按线索规格 (specification):")
    for r in stats:
        print(f"    {r['t']}: {r['cnt']} 条")

    # 按 cp_type 统计
    stats = query_db("SELECT IFNULL(cp_type,'NULL') as t, COUNT(*) as cnt FROM ams_composition GROUP BY cp_type ORDER BY cnt DESC")
    print(f"\n  按 CP 类型 (cp_type):")
    for r in stats:
        print(f"    cp_type={r['t']}: {r['cnt']} 条")

    # 按 allocate_status 统计
    stats = query_db("SELECT IFNULL(allocate_status,'NULL') as t, COUNT(*) as cnt FROM ams_composition GROUP BY allocate_status ORDER BY cnt DESC")
    print(f"\n  按交接状态 (allocate_status):")
    for r in stats:
        print(f"    allocate_status={r['t']}: {r['cnt']} 条")

    # 按 internal_publish 统计
    stats = query_db("SELECT IFNULL(internal_publish,'NULL') as t, COUNT(*) as cnt FROM ams_composition GROUP BY internal_publish ORDER BY cnt DESC")
    print(f"\n  按内部是否可发布 (internal_publish):")
    for r in stats:
        print(f"    internal_publish={r['t']}: {r['cnt']} 条")


# ==================== 2. AMS 作品列表 ====================

def show_ams_compositions():
    """查询 AMS 可用作品列表"""
    section("2. ams_composition 可用作品（最近更新，前 50 条）")

    sql = """
    SELECT 
        id, name, type, specification, cp_type,
        allocate_status, internal_publish,
        first_publish_time_type, channel_limit,
        subtitle_lang_config, dubbing_lang_config,
        business_id, customer_id,
        updated_at
    FROM ams_composition
    ORDER BY updated_at DESC
    LIMIT 50
    """
    rows = query_db(sql)

    if not rows:
        print("  [无数据]")
        return

    # 简要列表
    fmt = "{:>6s}  {:30s}  {:>4s}  {:>6s}  {:>5s}  {:>8s}  {:>8s}  {:>10s}  {:>8s}  {:19s}"
    header = fmt.format('ID', '作品名称', 'type', 'spec', 'cp_tp', 'alloc_st', 'int_pub', 'pub_time_t', 'ch_lmt', 'updated_at')
    print(f"  {header}")
    print("  " + "-" * 130)
    for row in rows:
        line = fmt.format(
            str(row['id']),
            str(row['name'] or '')[:30],
            str(row['type'] or ''),
            str(row['specification'] or '')[:6],
            str(row['cp_type'] or ''),
            str(row['allocate_status'] or ''),
            str(row['internal_publish'] or ''),
            str(row['first_publish_time_type'] or '')[:10],
            str(row['channel_limit'] or '')[:8],
            str(row['updated_at'] or '')[:19]
        )
        print(f"  {line}")
    print(f"\n  共返回 {len(rows)} 条记录")


# ==================== 3. 有发布配置的作品 ====================

def show_compositions_with_publish_config():
    """查询已配置发布信息的作品（internal_publish 不为 NULL）"""
    section("3. 已配置发布信息的作品 (internal_publish IS NOT NULL)")

    sql = """
    SELECT 
        id, name, type, specification, cp_type,
        allocate_status, internal_publish,
        first_publish_time_type, first_publish_time,
        channel_limit,
        subtitle_lang_config, dubbing_lang_config
    FROM ams_composition
    WHERE internal_publish IS NOT NULL
    ORDER BY updated_at DESC
    """
    rows = query_db(sql)

    if not rows:
        print("  [无数据] -- 暂无配置发布信息的作品")
        return

    print(f"  共 {len(rows)} 条有发布配置的作品\n")
    for i, row in enumerate(rows):
        print(f"  [{i+1}] ID={row['id']}  {row['name']}")
        print(f"      type={row['type']}, spec={row['specification']}, cp_type={row['cp_type']}")
        print(f"      allocate_status={row['allocate_status']}, internal_publish={row['internal_publish']}")
        print(f"      first_publish_time_type={row['first_publish_time_type']}, first_publish_time={row['first_publish_time']}")
        print(f"      channel_limit={row['channel_limit']}")
        print(f"      subtitle_lang_config={str(row['subtitle_lang_config'] or '')[:80]}")
        print(f"      dubbing_lang_config={str(row['dubbing_lang_config'] or '')[:80]}")
        print()
        if i >= 29:
            print(f"  ... 仅显示前 30 条")
            break


# ==================== 4. CRM 作品 + 交接单 ====================

def show_crm_and_allocate():
    """查询 CRM 作品和交接单"""
    section("4. crm_composition 作品列表")

    # CRM 作品表结构
    cols = query_db("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='silverdawn_ams' AND TABLE_NAME='crm_composition' ORDER BY ORDINAL_POSITION")
    col_names = [c['COLUMN_NAME'] for c in cols]
    print(f"  字段: {', '.join(col_names)}\n")

    total = query_db("SELECT COUNT(*) as cnt FROM crm_composition")
    print(f"  总记录数: {total[0]['cnt']}\n")

    sql = "SELECT * FROM crm_composition ORDER BY id DESC LIMIT 20"
    rows = query_db(sql)
    if rows:
        for i, row in enumerate(rows):
            print(f"  --- 记录 {i+1} ---")
            for k, v in row.items():
                val_str = str(v) if v is not None else 'NULL'
                if len(val_str) > 100:
                    val_str = val_str[:100] + '...'
                print(f"    {k}: {val_str}")
            print()
            if i >= 9:
                print(f"  ... 共 {len(rows)} 条，仅显示前 10 条")
                break

    # 交接单
    section("5. composition_allocate 交接单统计")
    total = query_db("SELECT COUNT(*) as cnt FROM composition_allocate")
    print(f"  总记录数: {total[0]['cnt']}")

    # 交接单表结构
    cols = query_db("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='silverdawn_ams' AND TABLE_NAME='composition_allocate' ORDER BY ORDINAL_POSITION")
    col_names = [c['COLUMN_NAME'] for c in cols]
    print(f"  字段: {', '.join(col_names)}\n")

    try:
        stats = query_db("SELECT IFNULL(status,'NULL') as s, COUNT(*) as cnt FROM composition_allocate GROUP BY status ORDER BY cnt DESC")
        print(f"  按状态:")
        for r in stats:
            print(f"    status={r['s']}: {r['cnt']} 条")
    except Exception:
        pass


if __name__ == '__main__':
    try:
        show_ams_stats()
        show_ams_compositions()
        show_compositions_with_publish_config()
        show_crm_and_allocate()
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
