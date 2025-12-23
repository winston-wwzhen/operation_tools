"""
状态相关 API
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from core import runtime_state, get_app_config
import asyncio
import json

router = APIRouter(tags=["status"])


@router.get("/status", summary="获取系统状态")
async def get_status():
    """
    获取当前系统状态和配置信息

    Returns:
        {
            "config": {...},  # 当前配置
            "state": {...}    # 运行时状态
        }
    """
    return {
        "config": get_app_config(),
        "state": runtime_state
    }


@router.get("/events", summary="SSE 实时事件推送")
async def sse_events():
    """
    Server-Sent Events 实时推送系统状态更新

    当运行时状态发生变化时，主动推送给客户端

    Returns:
        SSE 流，包含以下事件类型：
        - status: 完整状态更新
        - log: 新日志
        - topics: 热点话题更新
    """
    async def event_generator():
        """生成 SSE 事件"""
        # 记录上一次的状态，用于检测变化
        last_state = {
            'isRunning': runtime_state.get('isRunning', False),
            'lastRunTime': runtime_state.get('lastRunTime', ''),
            'nextRunTime': runtime_state.get('nextRunTime', ''),
            'logs_count': len(runtime_state.get('logs', [])),
            'topics_count': len(runtime_state.get('hot_topics', []))
        }

        # 首次发送完整状态
        yield f"event: status\ndata: {json.dumps(runtime_state)}\n\n"

        try:
            while True:
                await asyncio.sleep(1)  # 每秒检查一次状态变化

                # 检测是否有新日志
                current_logs = runtime_state.get('logs', [])
                current_logs_count = len(current_logs)
                if current_logs_count > last_state['logs_count']:
                    # 发送新日志
                    new_logs = current_logs[last_state['logs_count']:]
                    for log in new_logs:
                        yield f"event: log\ndata: {json.dumps(log)}\n\n"
                    last_state['logs_count'] = current_logs_count

                # 检测热点话题是否更新
                current_topics_count = len(runtime_state.get('hot_topics', []))
                if current_topics_count != last_state['topics_count']:
                    yield f"event: topics\ndata: {json.dumps(runtime_state.get('hot_topics', []))}\n\n"
                    last_state['topics_count'] = current_topics_count

                # 检测状态变化
                state_changed = False
                if (runtime_state.get('isRunning') != last_state['isRunning'] or
                    runtime_state.get('lastRunTime') != last_state['lastRunTime'] or
                    runtime_state.get('nextRunTime') != last_state['nextRunTime']):
                    state_changed = True
                    last_state['isRunning'] = runtime_state.get('isRunning', False)
                    last_state['lastRunTime'] = runtime_state.get('lastRunTime', '')
                    last_state['nextRunTime'] = runtime_state.get('nextRunTime', '')

                if state_changed:
                    yield f"event: status\ndata: {json.dumps(runtime_state)}\n\n"

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
