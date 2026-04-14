"""VT-017 数据准备脚本: 检查字段长度限制并更新"""
import pymysql

conn = pymysql.connect(
    host='172.16.24.61',
    port=3306,
    user='xiaowu_db',
    password='}C7n%7Wklq6P',
    database='silverdawn_ams',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 1. 检查 takedown_description 字段定义
cursor.execute("SHOW COLUMNS FROM video_takedown_task LIKE 'takedown_description'")
col_info = cursor.fetchone()
print(f'字段定义: {col_info}')

# 2. 根据字段类型选择合适长度的文本
# PRD说下架说明限制100字符, 所以字段可能是 varchar(100)
# 我们需要一条恰好100字符(满字段)的文本来测试"超出列宽度"的截断效果
long_text = '此任务单因版权方终止合作协议需要下架相关视频内容涉及多个频道的授权视频包含版权到期合同纠纷授权范围变更等多种原因需在截止日期前完成全部下架处理确保合规性满足法律要求并及时通知各分销商配合执行'
# 截取到100字符
long_text = long_text[:100]
print(f'文本长度: {len(long_text)} 字符')
print(f'文本内容: {long_text}')

# 3. 更新一条 COMPLETED 状态的任务单
cursor.execute("SELECT id, code FROM video_takedown_task WHERE status = 'COMPLETED' LIMIT 1")
target = cursor.fetchone()
if target:
    target_id = target[0]
    target_code = target[1]
    print(f'\n目标任务单: ID={target_id}, code={target_code}')
    
    cursor.execute(
        'UPDATE video_takedown_task SET takedown_description = %s WHERE id = %s',
        (long_text, target_id)
    )
    conn.commit()
    print('更新成功')
    
    # 验证
    cursor.execute('SELECT takedown_description FROM video_takedown_task WHERE id = %s', (target_id,))
    updated = cursor.fetchone()
    print(f'验证: len={len(updated[0])}, content={updated[0]}')
else:
    print('未找到 COMPLETED 状态的任务单')

conn.close()
