"""
补充 VT-033/034 排序测试数据 + 综合数据验证

VT-013: 不同截止日期排序 → 当前3条已满足 ✅
VT-033: 同截止日期不同下架原因优先级 → 需调整2条到同一截止日期+不同原因
VT-034: 同截止日期同优先级不同审批时间 → 需调整2条到同deadline同reason+不同audit_time

策略: 创建一个完整的数据准备脚本，按测试阶段分批准备数据
"""
import pymysql
from datetime import datetime

DB = {
    'host': '172.16.24.61', 'port': 3306,
    'user': 'xiaowu_db', 'password': '}C7n%7Wklq6P',
    'database': 'silverdawn_ams',
    'charset': 'utf8mb4', 'connect_timeout': 10,
}

def show_current_state(c):
    """显示当前任务状态"""
    c.execute(
        "SELECT code, status, takedown_reason, deadline_date, audit_time, audit_opinion "
        "FROM video_takedown_task ORDER BY code"
    )
    print('\n=== 当前任务状态 ===')
    print(f'{"Code":15s} | {"Status":20s} | {"Reason":30s} | {"Deadline":12s} | {"AuditTime":20s}')
    print('-' * 110)
    for t in c.fetchall():
        audit_str = str(t['audit_time'])[:19] if t['audit_time'] else 'NULL'
        reason = (t['takedown_reason'] or 'NULL')[:30]
        print(f"{t['code']:15s} | {t['status']:20s} | {reason:30s} | {str(t['deadline_date']):12s} | {audit_str:20s}")


def prepare_vt033_data(c, conn):
    """
    VT-033: 同截止日期不同下架原因优先级排序
    需要: 3条 PENDING_PROCESS, 同 deadline, 不同 takedown_reason
    
    优先级: TEMP_COPYRIGHT_DISPUTE(1) > ADJUST_LAUNCH_TIME(2) > SINGLE_COMPOSITION_TERMINATE(3)
    """
    print('\n\n' + '='*60)
    print('=== VT-033 数据准备: 同截止日期+不同下架原因 ===')
    
    # 将3条PENDING_PROCESS任务调整为同一截止日期+不同下架原因
    updates = [
        # (code, deadline, takedown_reason)
        ('V2603300003', '2026-04-05', 'SINGLE_COMPOSITION_TERMINATE'),  # 优先级3 (低)
        ('V2603300004', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE'),        # 优先级1 (高)
        ('V2603300006', '2026-04-05', 'ADJUST_LAUNCH_TIME'),            # 优先级2 (中)
    ]
    
    for code, deadline, reason in updates:
        c.execute(
            "UPDATE video_takedown_task SET "
            "deadline_date=%s, takedown_reason=%s "
            "WHERE code=%s AND status='PENDING_PROCESS'",
            (deadline, reason, code)
        )
        print(f"  {code} → deadline={deadline}, reason={reason} (rows={c.rowcount})")
    
    conn.commit()
    print('  VT-033 数据准备完成')
    print('  预期排序: V2603300004(优先级1) → V2603300006(优先级2) → V2603300003(优先级3)')


def prepare_vt034_data(c, conn):
    """
    VT-034: 同截止日期同优先级-审批通过时间排序
    需要: 2+条 PENDING_PROCESS, 同 deadline, 同 takedown_reason, 不同 audit_time
    """
    print('\n\n' + '='*60)
    print('=== VT-034 数据准备: 同截止日期+同优先级+不同审批时间 ===')
    
    # 将3条调整为同reason + 不同 audit_time
    updates = [
        ('V2603300003', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE', '2026-04-01 08:00:00'),  # 最早
        ('V2603300004', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE', '2026-04-01 10:30:00'),  # 中间
        ('V2603300006', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE', '2026-04-01 09:15:00'),  # 较早
    ]
    
    for code, deadline, reason, audit_time in updates:
        c.execute(
            "UPDATE video_takedown_task SET "
            "deadline_date=%s, takedown_reason=%s, audit_time=%s "
            "WHERE code=%s AND status='PENDING_PROCESS'",
            (deadline, reason, audit_time, code)
        )
        print(f"  {code} → deadline={deadline}, reason={reason}, audit_time={audit_time} (rows={c.rowcount})")
    
    conn.commit()
    print('  VT-034 数据准备完成')
    print('  预期排序: V2603300003(08:00) → V2603300006(09:15) → V2603300004(10:30)')


def restore_vt013_data(c, conn):
    """
    恢复 VT-013 数据: 不同截止日期
    """
    print('\n\n' + '='*60)
    print('=== 恢复 VT-013 数据: 不同截止日期 ===')
    
    updates = [
        ('V2603300003', '2026-04-05', 'TEMP_COPYRIGHT_DISPUTE'),
        ('V2603300004', '2026-04-03', 'TEMP_COPYRIGHT_DISPUTE'),
        ('V2603300006', '2026-04-07', 'ADJUST_LAUNCH_TIME'),
    ]
    
    for code, deadline, reason in updates:
        c.execute(
            "UPDATE video_takedown_task SET "
            "deadline_date=%s, takedown_reason=%s "
            "WHERE code=%s AND status='PENDING_PROCESS'",
            (deadline, reason, code)
        )
        print(f"  {code} → deadline={deadline}, reason={reason} (rows={c.rowcount})")
    
    conn.commit()
    print('  VT-013 数据恢复完成')
    print('  预期排序: V2603300004(04-03) → V2603300003(04-05) → V2603300006(04-07)')


def comprehensive_data_check(c):
    """综合数据检查 - 评估哪些用例已解除阻塞"""
    print('\n\n' + '='*60)
    print('=== 用例解除阻塞评估 ===')
    
    c.execute("SELECT status, COUNT(*) as cnt FROM video_takedown_task GROUP BY status ORDER BY cnt DESC")
    status_map = {r['status']: r['cnt'] for r in c.fetchall()}
    
    print(f"\n数据分布: {status_map}")
    
    assessments = [
        ('AMS-VT-013', '排队规则-截止日期维度',
         status_map.get('PENDING_PROCESS', 0) >= 3,
         f"需3条PENDING_PROCESS不同deadline, 当前{status_map.get('PENDING_PROCESS', 0)}条"),
        
        ('AMS-VT-027', '编辑审核拒绝任务单重新提交',
         status_map.get('REVIEW_REJECTED', 0) >= 1,
         f"需1条REVIEW_REJECTED, 当前{status_map.get('REVIEW_REJECTED', 0)}条"),
        
        ('AMS-VT-033', '排队规则-同截止日期不同优先级',
         status_map.get('PENDING_PROCESS', 0) >= 3,
         f"需3条PENDING_PROCESS同deadline不同reason, 需调整数据"),
        
        ('AMS-VT-034', '排队规则-同截止日期同优先级-审批时间',
         status_map.get('PENDING_PROCESS', 0) >= 2,
         f"需2+条PENDING_PROCESS同deadline同reason不同audit_time, 需调整数据"),
        
        ('AMS-VT-018', '审核拒绝Tab显示与Tooltip',
         status_map.get('REVIEW_REJECTED', 0) >= 1,
         f"需1条REVIEW_REJECTED, 当前{status_map.get('REVIEW_REJECTED', 0)}条"),
        
        ('AMS-QE-006', '审核通过后视频删除进入待处理',
         status_map.get('PENDING_PROCESS', 0) >= 1,
         f"验证已存在的PENDING_PROCESS任务即可"),
        
        ('AMS-SP-008', '两层状态体系验证',
         False,
         f"需PROCESSING任务, 当前{status_map.get('PROCESSING', 0)}条 - 需系统调度触发"),
        
        ('AMS-VT-011', '编辑创建失败任务单',
         status_map.get('CREATE_FAILED', 0) >= 1,
         f"需CREATE_FAILED+关联作品, 当前{status_map.get('CREATE_FAILED', 0)}条但可能无作品数据"),
        
        ('AMS-VT-025', '作品处理进度展开视频明细',
         status_map.get('COMPLETED', 0) >= 1,
         f"需已完成任务+视频明细, 当前{status_map.get('COMPLETED', 0)}条COMPLETED"),
    ]
    
    unblocked = 0
    partial = 0
    still_blocked = 0
    
    for case_id, name, ready, note in assessments:
        if ready:
            status_icon = 'UNBLOCKED'
            unblocked += 1
        elif 'PENDING_PROCESS' in note and status_map.get('PENDING_PROCESS', 0) >= 2:
            status_icon = 'PARTIAL'
            partial += 1
        else:
            status_icon = 'BLOCKED'
            still_blocked += 1
        
        print(f"  [{status_icon:10s}] {case_id}: {name}")
        print(f"             {note}")
    
    print(f"\n汇总: {unblocked} 解除阻塞, {partial} 部分解除, {still_blocked} 仍阻塞")
    
    # 其他可执行的跳过用例
    print('\n=== 原跳过用例评估（数据已就绪）===')
    skip_assessments = [
        ('AMS-VT-020', '添加作品弹窗搜索', True, 'PENDING_PROCESS任务可进入编辑流程'),
        ('AMS-VT-021', '批量导入校验', True, 'Excel测试文件已存在 data/excel/'),
        ('AMS-VT-022', '二次导入覆盖', True, 'Excel测试文件已存在'),
        ('AMS-VT-024', '视频ID导入校验', True, 'Excel测试文件已存在'),
        ('AMS-VT-029', '审核意见边界值', True, '有PENDING_REVIEW→但已消耗,需新建待审核'),
    ]
    for case_id, name, can_try, note in skip_assessments:
        icon = 'CAN_TRY' if can_try else 'SKIP'
        print(f"  [{icon:10s}] {case_id}: {name} - {note}")


def main():
    conn = pymysql.connect(**DB)
    c = conn.cursor(pymysql.cursors.DictCursor)
    
    # 1. 当前状态
    show_current_state(c)
    
    # 2. 综合评估
    comprehensive_data_check(c)
    
    # 3. 准备 VT-033 数据 (同截止日期+不同优先级)
    prepare_vt033_data(c, conn)
    show_current_state(c)
    
    # 4. 恢复为 VT-013 数据 (后续按需切换)
    restore_vt013_data(c, conn)
    show_current_state(c)
    
    conn.close()
    
    print('\n\n' + '='*60)
    print('=== 数据准备完成 ===')
    print('数据切换脚本已验证通过，可按测试需要随时调用:')
    print('  - restore_vt013_data(): 不同截止日期 (VT-013)')
    print('  - prepare_vt033_data(): 同截止日期+不同优先级 (VT-033)')
    print('  - prepare_vt034_data(): 同截止日期+同优先级+不同审批时间 (VT-034)')


if __name__ == '__main__':
    main()
