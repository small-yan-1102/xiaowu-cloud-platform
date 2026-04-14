"""
视频下架测试数据查询脚本
参考「方方^」作品的数据链结构，查找所有具备完整数据链的可用作品。

数据链路：
  ams_composition.name (作品名)
    ↕ 通过 sign_channel_name 匹配
  ams_publish_channel (发布通道)
    ├── sign_channel_name = 作品名
    ├── register_channel_id = YouTube频道ID
    ├── pipeline_id = 管道ID
    └── status = 1 (有效)
         ↓ 通过 target_channel_id + pipeline_id 关联
  dispatcher.video_order (视频订单)
    ├── target_channel_id = register_channel_id
    ├── pipeline_id = pipeline_id
    ├── upload_video_id = YouTube视频ID
    └── publish_status = 'finished' (已发布)
"""
import pymysql
import sys
import io

# 修复 Windows 控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_CONFIG = {
    'host': '172.16.24.61',
    'port': 3306,
    'user': 'xiaowu_db',
    'password': '}C7n%7Wklq6P',
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


def step1_reference_fangfang():
    """查看「方方^」的完整数据链作为参考"""
    section("STEP 1: 参考作品「方方^」(99351) 的完整数据链")

    # 1.1 ams_composition
    rows = query_db("SELECT id, name, type, specification, cp_type FROM silverdawn_ams.ams_composition WHERE id = 99351")
    if rows:
        r = rows[0]
        print(f"  [ams_composition] id={r['id']}, name={r['name']}, type={r['type']}, spec={r['specification']}, cp_type={r['cp_type']}")

    # 1.2 ams_publish_channel
    rows = query_db("""
        SELECT sign_channel_name, register_channel_id, register_channel_name, pipeline_id, status
        FROM silverdawn_ams.ams_publish_channel
        WHERE sign_channel_name = '方方^'
    """)
    print(f"\n  [ams_publish_channel] 共 {len(rows)} 条发布通道:")
    for r in rows:
        print(f"    sign_channel_name={r['sign_channel_name']}, channel={r['register_channel_name']}({r['register_channel_id']}), "
              f"pipeline={r['pipeline_id']}, status={r['status']}")

    # 1.3 dispatcher.video_order
    for r in rows:
        vids = query_db("""
            SELECT upload_video_id, publish_status, target_channel_id, pipeline_id
            FROM dispatcher.video_order
            WHERE target_channel_id = %s AND pipeline_id = %s AND publish_status = 'finished'
        """, (r['register_channel_id'], r['pipeline_id']))
        print(f"\n  [video_order] pipeline={r['pipeline_id'][:12]}... channel={r['register_channel_name']}:")
        if vids:
            for v in vids:
                print(f"    video_id={v['upload_video_id']}, status={v['publish_status']}")
        else:
            print(f"    (无已发布视频)")

    # 1.4 检查是否已被下架
    takedowns = query_db("""
        SELECT vtd.video_id, vtd.video_status, t.code AS task_code
        FROM silverdawn_ams.video_takedown_task_detail vtd
        JOIN silverdawn_ams.video_takedown_task t ON t.id = vtd.task_id
        WHERE vtd.composition_name = '方方^'
    """)
    if takedowns:
        print(f"\n  [已下架记录] {len(takedowns)} 条:")
        for td in takedowns:
            print(f"    video={td['video_id']}, status={td['video_status']}, task={td['task_code']}")
    else:
        print(f"\n  [已下架记录] 无 -- 视频未被下架，可用")

    # 1.5 检查分配情况（composition_allocate_detail 用 composition_id 关联，分销商在父表 composition_allocate）
    alloc = query_db("""
        SELECT ca.team_name, ca.team_id, cad.composition_id, cad.terminate_status
        FROM silverdawn_ams.composition_allocate ca
        JOIN silverdawn_ams.composition_allocate_detail cad ON ca.id = cad.allocate_id
        WHERE cad.composition_id = 99351
    """)
    if alloc:
        print(f"\n  [分配情况] 分配给:")
        for a in alloc:
            status = "已解约" if a['terminate_status'] == 1 else "活跃"
            print(f"    team={a['team_name']}({a['team_id']}), comp_id={a['composition_id']} [{status}]")
    else:
        print(f"\n  [分配情况] 未分配给任何分销商")


def step2_find_all_usable():
    """查找所有具备完整数据链的可用作品"""
    section("STEP 2: 查找所有具备完整数据链的作品（publish_channel + video_order）")

    # 核心查询：从 ams_publish_channel 找到有 pipeline_id 的作品，
    # 再关联 video_order 找到有已发布视频的
    sql = """
    SELECT 
        pc.sign_channel_name AS composition_name,
        ac.id AS composition_id,
        ac.type AS comp_type,
        ac.cp_type,
        pc.register_channel_id,
        pc.register_channel_name AS channel_name,
        pc.pipeline_id,
        vo.upload_video_id AS youtube_video_id,
        vo.publish_status
    FROM silverdawn_ams.ams_publish_channel pc
    JOIN dispatcher.video_order vo 
        ON vo.target_channel_id = pc.register_channel_id 
        AND vo.pipeline_id = pc.pipeline_id
        AND vo.publish_status = 'finished'
    LEFT JOIN silverdawn_ams.ams_composition ac 
        ON ac.name = pc.sign_channel_name
    WHERE pc.status = 1
    ORDER BY pc.sign_channel_name, pc.register_channel_id, vo.upload_video_id
    """
    rows = query_db(sql)
    print(f"  找到 {len(rows)} 条完整数据链记录\n")

    if not rows:
        print("  [无数据] 未找到任何具备完整数据链的作品")
        return []

    # 按作品名汇总
    compositions = {}
    for r in rows:
        name = r['composition_name']
        if name not in compositions:
            compositions[name] = {
                'composition_id': r['composition_id'],
                'comp_type': r['comp_type'],
                'cp_type': r['cp_type'],
                'channels': {},
                'videos': []
            }
        ch_id = r['register_channel_id']
        if ch_id not in compositions[name]['channels']:
            compositions[name]['channels'][ch_id] = r['channel_name']
        compositions[name]['videos'].append({
            'video_id': r['youtube_video_id'],
            'channel_id': ch_id,
            'channel_name': r['channel_name'],
            'pipeline_id': r['pipeline_id']
        })

    print(f"  汇总后 {len(compositions)} 个不同作品:\n")

    for name, info in sorted(compositions.items(), key=lambda x: len(x[1]['videos']), reverse=True):
        channels_str = ", ".join(f"{n}({cid[:8]}...)" for cid, n in info['channels'].items())
        print(f"  [{name}] id={info['composition_id']}, type={info['comp_type']}, cp_type={info['cp_type']}")
        print(f"    频道: {channels_str}")
        print(f"    可用视频({len(info['videos'])}个): {', '.join(v['video_id'] for v in info['videos'])}")
        print()

    return compositions


def step3_check_takedowns(compositions):
    """检查哪些视频已被下架"""
    section("STEP 3: 检查视频下架状态")

    all_videos = []
    for name, info in compositions.items():
        for v in info['videos']:
            all_videos.append((name, v['video_id']))

    if not all_videos:
        print("  无视频需要检查")
        return

    # 查询所有已下架的视频
    video_ids = list(set(v[1] for v in all_videos))
    placeholders = ','.join(['%s'] * len(video_ids))
    takedowns = query_db(f"""
        SELECT vtd.video_id, vtd.video_status, vtd.process_method, t.code AS task_code, t.status AS task_status
        FROM silverdawn_ams.video_takedown_task_detail vtd
        JOIN silverdawn_ams.video_takedown_task t ON t.id = vtd.task_id
        WHERE vtd.video_id IN ({placeholders})
    """, video_ids)

    taken_down_videos = {}
    for td in takedowns:
        vid = td['video_id']
        if vid not in taken_down_videos:
            taken_down_videos[vid] = []
        taken_down_videos[vid].append(td)

    if taken_down_videos:
        print(f"  发现 {len(taken_down_videos)} 个视频有下架记录:\n")
        for vid, records in taken_down_videos.items():
            for rec in records:
                print(f"    video={vid}, status={rec['video_status']}, method={rec['process_method']}, "
                      f"task={rec['task_code']}({rec['task_status']})")
    else:
        print("  所有视频均未被下架，全部可用")

    return taken_down_videos


def step4_check_allocations(compositions):
    """检查作品的分销商分配情况（通过 composition_id 关联）"""
    section("STEP 4: 检查作品的分销商分配情况")

    comp_ids = [info['composition_id'] for info in compositions.values() if info['composition_id']]
    if not comp_ids:
        print("  无作品需要检查")
        return

    placeholders = ','.join(['%s'] * len(comp_ids))
    allocs = query_db(f"""
        SELECT ca.team_name, ca.team_id, cad.composition_id, cad.terminate_status
        FROM silverdawn_ams.composition_allocate ca
        JOIN silverdawn_ams.composition_allocate_detail cad ON ca.id = cad.allocate_id
        WHERE cad.composition_id IN ({placeholders})
    """, comp_ids)

    # 建立 composition_id -> name 的映射
    id_to_name = {info['composition_id']: name for name, info in compositions.items() if info['composition_id']}

    if allocs:
        print(f"  找到 {len(allocs)} 条分配记录:\n")
        for a in allocs:
            status = "已解约" if a.get('terminate_status') == 1 else "活跃"
            comp_name = id_to_name.get(a['composition_id'], f"id={a['composition_id']}")
            print(f"    {comp_name}(id={a['composition_id']}) -> {a['team_name']}({a['team_id'][:16]}...) [{status}]")
    else:
        print("  这些作品未找到分配记录")

    return allocs


def step5_summary(compositions, taken_down_videos):
    """输出最终可用作品汇总"""
    section("STEP 5: 最终可用作品汇总")

    print("  ┌────────────────────┬────────────┬──────────┬──────────┬────────────────────────────────────────┐")
    print("  │ 作品名称           │ comp_id    │ 总视频数 │ 可用视频 │ 视频ID列表                             │")
    print("  ├────────────────────┼────────────┼──────────┼──────────┼────────────────────────────────────────┤")

    usable_count = 0
    for name, info in sorted(compositions.items(), key=lambda x: len(x[1]['videos']), reverse=True):
        total = len(info['videos'])
        usable_vids = [v['video_id'] for v in info['videos'] if v['video_id'] not in (taken_down_videos or {})]
        usable = len(usable_vids)

        status_marker = "OK" if usable > 0 else "XX"
        vid_list = ", ".join(usable_vids[:5])
        if len(usable_vids) > 5:
            vid_list += f" ...+{len(usable_vids)-5}"

        comp_id = str(info['composition_id'] or '?')
        print(f"  │ {name:18s} │ {comp_id:>10s} │ {total:>8d} │ {usable:>8d} │ {vid_list:38s} │")

        if usable > 0:
            usable_count += 1

    print("  └────────────────────┴────────────┴──────────┴──────────┴────────────────────────────────────────┘")
    print(f"\n  总计: {len(compositions)} 个作品, 其中 {usable_count} 个有可用视频")

    # 推荐
    section("STEP 6: 测试用例推荐")
    print("  按用途推荐可用作品:\n")

    by_video_count = sorted(compositions.items(), key=lambda x: len([
        v for v in x[1]['videos'] if v['video_id'] not in (taken_down_videos or {})
    ]), reverse=True)

    for name, info in by_video_count:
        usable_vids = [v for v in info['videos'] if v['video_id'] not in (taken_down_videos or {})]
        if not usable_vids:
            continue
        print(f"  [{name}] (comp_id={info['composition_id']}, {len(usable_vids)}个可用视频)")
        for v in usable_vids:
            print(f"    - {v['video_id']} (channel={v['channel_name']}, pipeline={v['pipeline_id'][:16]}...)")
        print()


if __name__ == '__main__':
    try:
        step1_reference_fangfang()
        compositions = step2_find_all_usable()
        taken_down_videos = step3_check_takedowns(compositions) if compositions else {}
        step4_check_allocations(compositions) if compositions else None
        step5_summary(compositions, taken_down_videos)
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
