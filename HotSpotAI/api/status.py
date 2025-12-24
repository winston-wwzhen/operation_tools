"""
状态相关 API
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from core import runtime_state, get_app_config
from core.auth import get_current_user, get_current_user_optional
import asyncio
import json
from typing import Optional

router = APIRouter(tags=["status"])


# 敏感配置字段，仅管理员可见
SENSITIVE_FIELDS = {
    'llmApiKey',
    'wechatSecret',
    'zhipuApiKey',
    'deepSeekApiKey',
    'openaiApiKey'
}

# 普通用户可见的配置字段
PUBLIC_CONFIG_FIELDS = {
    'llmBaseUrl',
    'llmModel',
    'topicLimit',
    'scheduleCron',
    'categoryScheduleCron',
    'autoRun',
    'categoryScrapingEnabled',
    'categoryTopicLimit',
    'wechatAppId'
}


def filter_config(config: dict, is_admin: bool) -> dict:
    """
    过滤配置信息，根据用户角色返回不同的字段

    Args:
        config: 原始配置字典
        is_admin: 是否为管理员

    Returns:
        过滤后的配置字典
    """
    if is_admin:
        # 管理员可以看到所有配置，但敏感字段只显示前几位
        filtered = config.copy()
        for field in SENSITIVE_FIELDS:
            if field in filtered and filtered[field]:
                value = filtered[field]
                if isinstance(value, str) and len(value) > 8:
                    filtered[field] = value[:4] + '...' + value[-4:]
                else:
                    filtered[field] = '***'
        return filtered
    else:
        # 普通用户只能看到公开字段
        return {
            k: v for k, v in config.items()
            if k in PUBLIC_CONFIG_FIELDS
        }


def filter_state(state: dict, is_admin: bool) -> dict:
    """
    过滤状态信息，普通用户不显示日志

    Args:
        state: 原始状态字典
        is_admin: 是否为管理员

    Returns:
        过滤后的状态字典（确保可序列化为 JSON）
    """
    # 三阶段任务状态
    task_stages = {
        'scraper_running': state.get('scraper_running', False),
        'analyzer_running': state.get('analyzer_running', False),
        'selector_running': state.get('selector_running', False),
    }

    # 任务统计信息
    task_stats = state.get('task_stats', {})

    if is_admin:
        # 管理员看到完整状态，但需要确保可序列化
        return {
            'isRunning': state.get('isRunning', False),
            'lastRunTime': str(state.get('lastRunTime', '')),
            'nextRunTime': str(state.get('nextRunTime', '')),
            'hot_topics': state.get('hot_topics', []),
            'logs': state.get('logs', []),
            'task_stages': task_stages,
            'task_stats': task_stats,
            'last_scraper_count': state.get('last_scraper_count', 0),
            'last_analyzer_count': state.get('last_analyzer_count', 0),
            'last_selector_count': state.get('last_selector_count', 0),
        }
    else:
        # 普通用户不显示日志和敏感信息
        return {
            'isRunning': state.get('isRunning', False),
            'lastRunTime': str(state.get('lastRunTime', '')),
            'nextRunTime': str(state.get('nextRunTime', '')),
            'hot_topics': state.get('hot_topics', []),
            'task_stages': task_stages,
        }


@router.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口（无需认证）"""
    return {"status": "ok", "service": "hotspotai-api"}


@router.get("/status/public", summary="获取公开状态")
async def get_public_status():
    """
    获取公开的系统状态信息（无需认证）

    未登录用户可以看到热点话题列表，但不包含日志和敏感配置

    Returns:
        {
            "isRunning": bool,  # 是否正在运行
            "hot_topics": list,  # 热点话题列表
            "lastRunTime": str  # 上次运行时间
        }
    """
    return {
        "isRunning": runtime_state.get('isRunning', False),
        "hot_topics": runtime_state.get('hot_topics', []),
        "lastRunTime": runtime_state.get('lastRunTime', '')
    }


@router.get("/status", summary="获取系统状态")
async def get_status(current_user: dict = Depends(get_current_user)):
    """
    获取当前系统状态和配置信息（需要认证）

    管理员可以看到完整配置（敏感字段脱敏）和日志
    普通用户只能看到公开配置和热点话题

    Returns:
        {
            "config": {...},  # 当前配置（根据角色过滤）
            "state": {...}    # 运行时状态（根据角色过滤）
        }
    """
    is_admin = current_user.get('is_admin', False) == 1

    config = get_app_config()
    filtered_config = filter_config(config, is_admin)
    filtered_state = filter_state(runtime_state, is_admin)

    return {
        "config": filtered_config,
        "state": filtered_state,
        "is_admin": is_admin
    }


@router.get("/events", summary="SSE 实时事件推送")
async def sse_events(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """
    Server-Sent Events 实时推送系统状态更新（可选认证）

    未认证用户只接收基本状态和热点话题更新
    认证用户根据角色接收不同的信息：
    - 管理员：完整状态 + 日志
    - 普通用户：基本状态 + 热点话题

    Returns:
        SSE 流，包含以下事件类型：
        - status: 状态更新
        - log: 新日志（仅管理员）
        - topics: 热点话题更新
    """
    is_admin = current_user is not None and current_user.get('is_admin', False) == 1

    async def event_generator():
        """生成 SSE 事件"""
        # 记录上一次的状态，用于检测变化
        last_state = {
            'isRunning': runtime_state.get('isRunning', False),
            'lastRunTime': runtime_state.get('lastRunTime', ''),
            'nextRunTime': runtime_state.get('nextRunTime', ''),
            'logs_count': len(runtime_state.get('logs', [])) if is_admin else 0,
            'topics_count': len(runtime_state.get('hot_topics', [])),
            'scraper_running': runtime_state.get('scraper_running', False),
            'analyzer_running': runtime_state.get('analyzer_running', False),
            'selector_running': runtime_state.get('selector_running', False),
        }

        # 首次发送过滤后的状态
        filtered_state = filter_state(runtime_state, is_admin)
        yield f"event: status\ndata: {json.dumps(filtered_state)}\n\n"

        try:
            while True:
                await asyncio.sleep(1)  # 每秒检查一次状态变化

                # 检测是否有新日志（仅管理员）
                if is_admin:
                    current_logs = runtime_state.get('logs', [])
                    current_logs_count = len(current_logs)
                    if current_logs_count > last_state['logs_count']:
                        # 发送新日志
                        new_logs = current_logs[last_state['logs_count']:]
                        for log in new_logs:
                            yield f"event: log\ndata: {json.dumps(log)}\n\n"
                        last_state['logs_count'] = current_logs_count

                # 检测热点话题是否更新（所有用户）
                current_topics_count = len(runtime_state.get('hot_topics', []))
                if current_topics_count != last_state['topics_count']:
                    yield f"event: topics\ndata: {json.dumps(runtime_state.get('hot_topics', []))}\n\n"
                    last_state['topics_count'] = current_topics_count

                # 检测状态变化（所有用户）
                state_changed = False
                if (runtime_state.get('isRunning') != last_state['isRunning'] or
                    runtime_state.get('lastRunTime') != last_state['lastRunTime'] or
                    runtime_state.get('nextRunTime') != last_state['nextRunTime'] or
                    runtime_state.get('scraper_running') != last_state['scraper_running'] or
                    runtime_state.get('analyzer_running') != last_state['analyzer_running'] or
                    runtime_state.get('selector_running') != last_state['selector_running']):
                    state_changed = True
                    last_state['isRunning'] = runtime_state.get('isRunning', False)
                    last_state['lastRunTime'] = runtime_state.get('lastRunTime', '')
                    last_state['nextRunTime'] = runtime_state.get('nextRunTime', '')
                    last_state['scraper_running'] = runtime_state.get('scraper_running', False)
                    last_state['analyzer_running'] = runtime_state.get('analyzer_running', False)
                    last_state['selector_running'] = runtime_state.get('selector_running', False)

                if state_changed:
                    filtered_state = filter_state(runtime_state, is_admin)
                    yield f"event: status\ndata: {json.dumps(filtered_state)}\n\n"

                # 发送心跳，保持连接
                yield ": heartbeat\n\n"

        except asyncio.CancelledError:
            # 客户端断开连接
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )
