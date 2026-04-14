# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - 云效 OpenAPI 客户端封装

基于 HTTP requests + 个人访问令牌（PAT）认证，
通过 x-yunxiao-token 请求头调用云效 Testhub OpenAPI。
支持 dry_run 模式和自动重试。

服务接入点文档: https://help.aliyun.com/zh/yunxiao/developer-reference/service-access-point-domain
中心版域名: openapi-rdc.aliyuncs.com
"""

import time
import logging
import requests
from typing import List, Dict, Any, Optional, Tuple
from .config import AppConfig

logger = logging.getLogger(__name__)


class YunxiaoApiClient:
    """云效 Testhub OpenAPI 客户端

    Attributes:
        config: 应用配置
        dry_run: 是否为模拟模式
        base_url: API 基础 URL
        headers: 公共请求头
        root_directory_id: 用例库根目录ID（运行时自动获取）
    """

    def __init__(self, config: AppConfig):
        """初始化 API 客户端

        Args:
            config: 应用配置（含 PAT、domain 等）
        """
        self.config = config
        self.dry_run = config.sync.dry_run
        self._org_id = config.yunxiao.organization_id
        self._repo_id = config.yunxiao.space_identifier

        domain = config.yunxiao.domain.rstrip('/')
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        self.base_url = f"{domain}/oapi/v1/testhub/organizations/{self._org_id}/testRepos/{self._repo_id}"

        self.headers = {
            'Content-Type': 'application/json',
            'x-yunxiao-token': config.yunxiao.personal_access_token,
        }

        # 根目录ID，延迟获取
        self._root_directory_id: Optional[str] = None

    def _retry(self, func, *args, **kwargs):
        """通用重试逻辑（指数退避）

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数返回值

        Raises:
            Exception: 重试耗尽后抛出最后一次异常
        """
        last_error = None
        for attempt in range(self.config.sync.retry_count):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                err_str = str(e)
                if 'Throttling' in err_str or '429' in err_str or '限流' in err_str:
                    wait = self.config.sync.retry_delay * (2 ** attempt)
                    logger.warning(f"API 限流，等待 {wait}s 后重试 ({attempt+1}/{self.config.sync.retry_count})")
                    time.sleep(wait)
                elif attempt < self.config.sync.retry_count - 1:
                    wait = self.config.sync.retry_delay * (attempt + 1)
                    logger.warning(f"API 调用失败: {e}，等待 {wait}s 后重试 ({attempt+1}/{self.config.sync.retry_count})")
                    time.sleep(wait)
                else:
                    raise
        raise last_error

    def _check_response(self, resp: requests.Response, action: str):
        """检查 HTTP 响应状态

        Args:
            resp: HTTP 响应对象
            action: 操作描述（用于错误信息）

        Raises:
            Exception: HTTP 状态码非 2xx 时抛出
        """
        if resp.status_code == 302:
            location = resp.headers.get('Location', '')
            raise Exception(f"{action}失败: 认证被拒绝 (302 -> {location})，请检查 PAT 令牌和域名配置")
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:200]
            raise Exception(f"{action}失败 (HTTP {resp.status_code}): {detail}")

    def get_root_directory_id(self) -> str:
        """获取用例库的根目录ID

        Returns:
            str: 根目录ID
        """
        if self._root_directory_id:
            return self._root_directory_id

        if self.dry_run:
            self._root_directory_id = "dry_run_root_dir"
            return self._root_directory_id

        dirs = self.list_directories()
        # 根目录是 parentId 为 null 的目录
        for d in dirs:
            if d.get('parentId') is None:
                self._root_directory_id = d['id']
                logger.info(f"根目录: {d.get('name', '')} -> {self._root_directory_id}")
                return self._root_directory_id

        # 如果没有找到根目录，使用第一个目录
        if dirs:
            self._root_directory_id = dirs[0]['id']
            return self._root_directory_id

        raise Exception("用例库中没有目录，请先在云效中创建用例库")

    def list_directories(self) -> List[Dict]:
        """获取用例库目录列表

        API: GET /oapi/v1/testhub/organizations/{orgId}/testRepos/{repoId}/directories

        Returns:
            list[dict]: 目录列表（含 id、name、parentId）
        """
        if self.dry_run:
            logger.info("[DRY-RUN] 查询目录列表 -> 空列表")
            return []

        def _do_list():
            """执行目录列表 API 调用"""
            url = f"{self.base_url}/directories"
            resp = requests.get(url, headers=self.headers, timeout=30, allow_redirects=False)
            self._check_response(resp, "查询目录列表")
            return resp.json()

        return self._retry(_do_list)

    def create_directory(self, name: str, parent_id: str = None) -> str:
        """在 Testhub 用例库内创建目录

        API: POST /oapi/v1/testhub/organizations/{orgId}/testRepos/{repoId}/directories

        Args:
            name: 目录名称
            parent_id: 父目录ID（为空则创建在根目录下）

        Returns:
            str: 新创建的目录ID
        """
        if self.dry_run:
            fake_id = f"dir_dry_{name}"
            logger.info(f"[DRY-RUN] 创建目录: {name} (parent={parent_id}) -> {fake_id}")
            return fake_id

        def _do_create():
            """执行目录创建 API 调用"""
            url = f"{self.base_url}/directories"
            body = {'name': name}
            if parent_id:
                body['parentIdentifier'] = parent_id

            resp = requests.post(url, json=body, headers=self.headers, timeout=30, allow_redirects=False)
            self._check_response(resp, f"创建目录 {name}")
            data = resp.json()
            dir_id = data.get('id', '')
            if not dir_id:
                raise Exception(f"创建目录 {name} 返回值中缺少 id: {data}")
            return dir_id

        result = self._retry(_do_create)
        logger.info(f"创建目录: {name} -> {result}")
        return result

    def search_test_cases(self, directory_id: str = None, page: int = 1, per_page: int = 200) -> Tuple[list, int]:
        """搜索用例库中的测试用例

        API: POST /oapi/v1/testhub/organizations/{orgId}/testRepos/{repoId}/testcases:search
        注意: directoryId 为必填字段，否则返回 400。

        Args:
            directory_id: 目录ID（为空时自动使用根目录ID）
            page: 页码
            per_page: 每页数量（最大200）

        Returns:
            tuple: (用例列表, 总数)
        """
        if self.dry_run:
            logger.info("[DRY-RUN] 搜索用例列表 -> 空列表")
            return [], 0

        # directoryId 是必填的，为空时使用根目录
        if not directory_id:
            directory_id = self.get_root_directory_id()

        def _do_search():
            """执行用例搜索 API 调用"""
            url = f"{self.base_url}/testcases:search"
            body = {
                'directoryId': directory_id,
                'page': page,
                'perPage': per_page,
                'orderBy': 'gmtCreate',
                'sort': 'desc',
            }

            resp = requests.post(url, json=body, headers=self.headers, timeout=30, allow_redirects=False)
            self._check_response(resp, "搜索用例")

            cases = resp.json()
            total = int(resp.headers.get('x-total', len(cases)))
            return cases, total

        return self._retry(_do_search)

    def list_all_test_cases(self, directory_id: str = None) -> List[Dict]:
        """分页查询用例库中的所有测试用例

        Args:
            directory_id: 目录ID（为空时使用根目录，搜索全库）

        Returns:
            list[dict]: 用例列表（含 id、subject 等字段）
        """
        if self.dry_run:
            logger.info("[DRY-RUN] 查询全部用例 -> 空列表")
            return []

        all_cases = []
        page = 1
        per_page = 200

        while True:
            cases, total = self.search_test_cases(directory_id=directory_id, page=page, per_page=per_page)
            all_cases.extend(cases)
            if len(all_cases) >= total or len(cases) < per_page:
                break
            page += 1

        return all_cases

    def create_test_case(self, request_body: Dict[str, Any]) -> str:
        """创建单条测试用例

        API: POST /oapi/v1/testhub/organizations/{orgId}/testRepos/{repoId}/testcases

        Args:
            request_body: 经 field_mapper 转换后的请求参数

        Returns:
            str: 云效分配的用例ID
        """
        if self.dry_run:
            subject = request_body.get('subject', '')
            fake_id = f"tc_dry_{subject[:20]}"
            logger.info(f"[DRY-RUN] 创建用例: {subject} -> {fake_id}")
            return fake_id

        def _do_create():
            """执行用例创建 API 调用"""
            url = f"{self.base_url}/testcases"
            resp = requests.post(url, json=request_body, headers=self.headers, timeout=30, allow_redirects=False)
            self._check_response(resp, f"创建用例 {request_body.get('subject', '')}")
            data = resp.json()
            case_id = data.get('id', '')
            if not case_id:
                raise Exception(f"创建用例返回值中缺少 id: {data}")
            return case_id

        return self._retry(_do_create)

    def update_test_case(self, case_id: str, request_body: Dict[str, Any]) -> str:
        """更新已有测试用例（删除后重建）

        云效 Testhub PUT API 仅支持更新 subject/assignedTo，
        无法更新 testSteps/preCondition/customFieldValues 等字段。
        因此采用 删除+重建 策略实现完整更新。

        Args:
            case_id: 云效用例ID
            request_body: 完整的用例请求体（同创建接口格式）

        Returns:
            str: 新创建的云效用例ID
        """
        if self.dry_run:
            subject = request_body.get('subject', '')
            logger.info(f"[DRY-RUN] 更新用例（删除+重建）: {subject} ({case_id})")
            return case_id

        # 先删除旧用例
        self.delete_test_case(case_id)

        # 再重新创建
        return self.create_test_case(request_body)

    def delete_test_case(self, case_id: str) -> None:
        """删除测试用例

        API: DELETE /oapi/v1/testhub/organizations/{orgId}/testRepos/{repoId}/testcases/{caseId}

        Args:
            case_id: 云效用例ID
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] 删除用例: {case_id}")
            return

        def _do_delete():
            """执行用例删除 API 调用"""
            url = f"{self.base_url}/testcases/{case_id}"
            resp = requests.delete(url, headers=self.headers, timeout=30, allow_redirects=False)
            if resp.status_code == 404:
                logger.warning(f"用例 {case_id} 不存在，跳过删除")
                return
            self._check_response(resp, f"删除用例 ({case_id})")

        self._retry(_do_delete)

    def get_field_config(self) -> List[Dict]:
        """获取用例库的字段配置（含优先级、类型等字段的选项ID）

        API: GET /oapi/v1/testhub/organizations/{orgId}/testRepos/{repoId}/testcases/fields

        Returns:
            list[dict]: 字段配置列表
        """
        if self.dry_run:
            logger.info("[DRY-RUN] 获取字段配置 -> 空列表")
            return []

        def _do_get():
            """执行字段配置查询 API 调用"""
            url = f"{self.base_url}/testcases/fields"
            resp = requests.get(url, headers=self.headers, timeout=30, allow_redirects=False)
            self._check_response(resp, "获取字段配置")
            return resp.json()

        return self._retry(_do_get)

    def build_field_option_map(self) -> Dict[str, Dict[str, str]]:
        """构建字段选项映射表：{fieldId: {displayValue: optionId}}

        Returns:
            dict: 如 {'tc.priority': {'P0': 'xxx', 'P1': 'yyy'}, 'tc.type': {'功能测试': 'zzz'}}
        """
        if self.dry_run:
            return {}

        fields = self.get_field_config()
        option_map = {}
        for field in fields:
            field_id = field.get('id', '')
            options = field.get('options', [])
            if options:
                option_map[field_id] = {}
                for opt in options:
                    display = opt.get('displayValue', '') or opt.get('value', '')
                    opt_id = opt.get('id', '')
                    if display and opt_id:
                        option_map[field_id][display] = opt_id
                        # 也映射英文值
                        value_en = opt.get('valueEn', '')
                        if value_en and value_en != display:
                            option_map[field_id][value_en] = opt_id
        return option_map

    def test_connection(self) -> bool:
        """测试 API 连接是否正常（通过列出目录验证）

        Returns:
            bool: 连接是否成功
        """
        if self.dry_run:
            print("[DRY-RUN] 跳过 API 连接测试")
            return True

        try:
            url = f"{self.base_url}/directories"
            resp = requests.get(url, headers=self.headers, timeout=15, allow_redirects=False)
            if resp.status_code == 200:
                logger.info("API 连接测试成功")
                return True
            elif resp.status_code == 302:
                logger.error("API 连接测试失败: 认证被拒绝 (302)，请检查 PAT 令牌和域名")
                return False
            else:
                logger.error(f"API 连接测试失败: HTTP {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"API 连接测试异常: {e}")
            return False
