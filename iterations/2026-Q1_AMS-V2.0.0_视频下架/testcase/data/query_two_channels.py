"""
查询两个指定 YT 频道的所有可用作品数据链。
目标频道：
  1. UCA17JOb1Bo5YQdggQwJN20Q - 橙汁的测试频道-0627-02
  2. UClDJc5bJntyxdJoHB94GVgg - @林

输出用于更新 smoke_test_data_config.md 的准备数据。
"""
import pymysql
import sys
import io
import json

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

TARGET_CHANNELS = {
    'UCA17JOb1Bo5YQdggQwJN20Q': '橙汁的测试频道-0627-02',
    'UClDJc5bJntyxdJoHB94GVgg': '@林'
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
    print("=" * 110)
    print(f"  {title}")
    print("=" * 110)


def query_channel_compositions():
    """查询两个频道下所有作品的完整数据链"""
    section("1. 查询两个目标频道的完整数据链（publish_channel + video_order）")

    channel_ids = list(TARGET_CHANNELS.keys())
    placeholders = ','.join(['%s'] * len(channel_ids))

    # 查询所有有完整数据链的记录（有已发布视频）
    sql = f"""
    SELECT 
        pc.sign_channel_name AS composition_name,
        ac.id AS composition_id,
        ac.type AS comp_type,
        ac.cp_type,
        ac.specification,
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
      AND pc.register_channel_id IN ({placeholders})
    ORDER BY pc.register_channel_id, pc.sign_channel_name, vo.upload_video_id
    """
    rows = query_db(sql, channel_ids)
    print(f"  找到 {len(rows)} 条完整数据链记录（有已发布视频）\n")

    # 同时查询有 publish_channel 但无已发布视频的记录
    sql_no_video = f"""
    SELECT 
        pc.sign_channel_name AS composition_name,
        ac.id AS composition_id,
        pc.register_channel_id,
        pc.register_channel_name AS channel_name,
        pc.pipeline_id
    FROM silverdawn_ams.ams_publish_channel pc
    LEFT JOIN silverdawn_ams.ams_composition ac 
        ON ac.name = pc.sign_channel_name
    LEFT JOIN dispatcher.video_order vo 
        ON vo.target_channel_id = pc.register_channel_id 
        AND vo.pipeline_id = pc.pipeline_id
        AND vo.publish_status = 'finished'
    WHERE pc.status = 1
      AND pc.register_channel_id IN ({placeholders})
      AND vo.upload_video_id IS NULL
    ORDER BY pc.register_channel_id, pc.sign_channel_name
    """
    rows_no_video = query_db(sql_no_video, channel_ids)
    print(f"  另有 {len(rows_no_video)} 条仅有发布通道但无视频的记录\n")

    return rows, rows_no_video


def check_takedowns(rows):
    """检查视频下架状态"""
    section("2. 检查视频下架状态")

    video_ids = list(set(r['youtube_video_id'] for r in rows))
    if not video_ids:
        print("  无视频需要检查")
        return {}

    placeholders = ','.join(['%s'] * len(video_ids))
    takedowns = query_db(f"""
        SELECT vtd.video_id, vtd.video_status, vtd.process_method, 
               t.code AS task_code, t.status AS task_status
        FROM silverdawn_ams.video_takedown_task_detail vtd
        JOIN silverdawn_ams.video_takedown_task t ON t.id = vtd.task_id
        WHERE vtd.video_id IN ({placeholders})
    """, video_ids)

    taken_down = {}
    for td in takedowns:
        vid = td['video_id']
        if vid not in taken_down:
            taken_down[vid] = []
        taken_down[vid].append(td)

    if taken_down:
        print(f"  发现 {len(taken_down)} 个视频有下架记录:\n")
        for vid, records in taken_down.items():
            for rec in records:
                print(f"    video={vid}, status={rec['video_status']}, method={rec['process_method']}, "
                      f"task={rec['task_code']}({rec['task_status']})")
    else:
        print("  所有视频均未被下架，全部可用！")

    return taken_down


def check_allocations(rows):
    """检查作品的分销商分配情况"""
    section("3. 检查作品的分销商分配情况")

    comp_ids = list(set(r['composition_id'] for r in rows if r['composition_id']))
    if not comp_ids:
        print("  无作品需要检查")
        return {}

    placeholders = ','.join(['%s'] * len(comp_ids))
    allocs = query_db(f"""
        SELECT ca.team_name, ca.team_id, ca.code AS allocate_code,
               cad.composition_id, cad.terminate_status
        FROM silverdawn_ams.composition_allocate ca
        JOIN silverdawn_ams.composition_allocate_detail cad ON ca.id = cad.allocate_id
        WHERE cad.composition_id IN ({placeholders})
        ORDER BY ca.team_name, cad.composition_id
    """, comp_ids)

    alloc_map = {}
    if allocs:
        print(f"  找到 {len(allocs)} 条分配记录:\n")
        for a in allocs:
            status = "已解约" if a.get('terminate_status') == 1 else "活跃"
            print(f"    comp_id={a['composition_id']} -> {a['team_name']}(team_id={a['team_id'][:20]}...) "
                  f"[{status}] allocate_code={a['allocate_code']}")
            if a['composition_id'] not in alloc_map:
                alloc_map[a['composition_id']] = []
            alloc_map[a['composition_id']].append(a)
    else:
        print("  这些作品未找到分配记录")

    return alloc_map


def generate_summary(rows, rows_no_video, taken_down, alloc_map):
    """生成最终汇总"""
    section("4. 两个频道可用数据汇总")

    # 按频道分组
    for ch_id, ch_name in TARGET_CHANNELS.items():
        print(f"\n  ---- 频道: {ch_name} ({ch_id}) ----\n")

        ch_rows = [r for r in rows if r['register_channel_id'] == ch_id]
        ch_no_video = [r for r in rows_no_video if r['register_channel_id'] == ch_id]

        # 按作品分组
        compositions = {}
        for r in ch_rows:
            name = r['composition_name']
            if name not in compositions:
                compositions[name] = {
                    'composition_id': r['composition_id'],
                    'comp_type': r['comp_type'],
                    'cp_type': r['cp_type'],
                    'specification': r['specification'],
                    'videos': []
                }
            is_taken_down = r['youtube_video_id'] in taken_down
            compositions[name]['videos'].append({
                'video_id': r['youtube_video_id'],
                'pipeline_id': r['pipeline_id'],
                'taken_down': is_taken_down
            })

        # 有视频的作品
        for name, info in sorted(compositions.items(), key=lambda x: len([v for v in x[1]['videos'] if not v['taken_down']]), reverse=True):
            usable_vids = [v for v in info['videos'] if not v['taken_down']]
            taken_vids = [v for v in info['videos'] if v['taken_down']]

            # 分配信息
            allocs = alloc_map.get(info['composition_id'], [])
            alloc_str = ", ".join(f"{a['team_name']}({'活跃' if a['terminate_status']==0 else '已解约'})" for a in allocs) if allocs else "未分配"

            marker = "OK" if usable_vids else "XX"
            print(f"  [{marker}] {name} (id={info['composition_id']}, type={info['comp_type']}, cp_type={info['cp_type']})")
            print(f"       分配: {alloc_str}")

            if usable_vids:
                print(f"       可用视频({len(usable_vids)}个):")
                for v in usable_vids:
                    print(f"         - {v['video_id']}  pipeline={v['pipeline_id']}")

            if taken_vids:
                print(f"       已下架视频({len(taken_vids)}个):")
                for v in taken_vids:
                    tasks = taken_down.get(v['video_id'], [])
                    task_str = ", ".join(f"{t['task_code']}" for t in tasks)
                    print(f"         - ~~{v['video_id']}~~  (被 {task_str} 处理)")
            print()

        # 无视频但有发布通道的作品
        if ch_no_video:
            print(f"  [仅有发布通道，无已发布视频]:")
            for r in ch_no_video:
                print(f"    - {r['composition_name']} (id={r['composition_id']}) pipeline={r['pipeline_id']}")
            print()

    # Markdown 格式输出
    section("5. Markdown 格式输出（可直接粘贴到文档）")

    for ch_id, ch_name in TARGET_CHANNELS.items():
        ch_rows = [r for r in rows if r['register_channel_id'] == ch_id]

        compositions = {}
        for r in ch_rows:
            name = r['composition_name']
            if name not in compositions:
                compositions[name] = {
                    'composition_id': r['composition_id'],
                    'comp_type': r['comp_type'],
                    'cp_type': r['cp_type'],
                    'videos': []
                }
            is_taken_down = r['youtube_video_id'] in taken_down
            compositions[name]['videos'].append({
                'video_id': r['youtube_video_id'],
                'pipeline_id': r['pipeline_id'],
                'taken_down': is_taken_down
            })

        print(f"\n#### {ch_name} (`{ch_id}`)\n")
        print(f"| 作品名称 | composition_id | pipeline_id | YouTube视频ID | 状态 |")
        print(f"|---------|:-----------:|-------------|--------------|------|")

        for name, info in sorted(compositions.items()):
            for v in info['videos']:
                status = "已下架" if v['taken_down'] else "可用"
                vid_display = f"~~{v['video_id']}~~" if v['taken_down'] else v['video_id']
                print(f"| {name} | {info['composition_id']} | {v['pipeline_id']} | {vid_display} | {status} |")

    # 按作品汇总 Markdown
    print(f"\n#### 按作品汇总（快速查阅）\n")
    print(f"| 作品名称 | composition_id | 频道 | 可用视频数 | 视频ID列表 |")
    print(f"|---------|:-----------:|------|:-------:|-----------|")

    # 合并两个频道
    all_compositions = {}
    for r in rows:
        name = r['composition_name']
        if name not in all_compositions:
            all_compositions[name] = {
                'composition_id': r['composition_id'],
                'channels': {}
            }
        ch_id = r['register_channel_id']
        ch_name_local = TARGET_CHANNELS.get(ch_id, ch_id)
        if ch_name_local not in all_compositions[name]['channels']:
            all_compositions[name]['channels'][ch_name_local] = []

        is_taken_down = r['youtube_video_id'] in taken_down
        if not is_taken_down:
            all_compositions[name]['channels'][ch_name_local].append(r['youtube_video_id'])

    for name, info in sorted(all_compositions.items()):
        for ch, vids in info['channels'].items():
            if vids:
                print(f"| {name} | {info['composition_id']} | {ch} | {len(vids)} | {', '.join(vids)} |")


if __name__ == '__main__':
    try:
        rows, rows_no_video = query_channel_compositions()
        taken_down = check_takedowns(rows)
        alloc_map = check_allocations(rows)
        generate_summary(rows, rows_no_video, taken_down, alloc_map)
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
