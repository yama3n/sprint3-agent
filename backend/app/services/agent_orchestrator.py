"""AGENT-01→AGENT-02の連鎖起動（agent-plan.md §2 エージェント間データフロー）。

HTTPリクエスト内でエージェント完了を同期待ちしない（agent-development.md）。
endpointsはこのモジュールの orchestrate_* をバックグラウンドタスクとして起動するだけで、
実際の待ち合わせ・連鎖はここで行う。個々のエージェント実行自体は jobs.start_agent_job()
経由（外側タイムアウト込み）を必ず通す。

AGENT-01分のagent_runsは inquiry_upload_service.create_inquiry_with_files/add_files_to_inquiry
がstage=uploadingで既に作成済み（05-api-ipo.mdのレスポンスにagent_run_idを即返すため）。
このモジュールはそれをstage=extractingへ進めてから起動する。
"""

import asyncio
import json
from typing import Literal

from app.agent import jobs
from app.agent.agent01.definition import AGENT01_SPEC
from app.agent.agent02.definition import AGENT02_SPEC
from app.core.db import AsyncSessionLocal
from app.models.agent_run import AgentRun
from app.models.inquiry import InquiryFile
from app.repositories.agent_run_repository import AgentRunRepository
from app.repositories.extraction_result_repository import ExtractionResultRepository

_STOPPED_REASONS = {"inner_timeout", "outer_timeout", "inactivity_timeout", "max_turns"}

Trigger = Literal["new_upload", "additional_upload"]


def _build_agent01_prompt(
    inquiry_id: int, agent_run_id: int, files: list[InquiryFile]
) -> str:
    file_list = "\n".join(
        f"- file_id={f.id}: {f.file_name}（形式: {f.file_type}）" for f in files
    )
    return (
        f"引合ID(inquiry_id)は{inquiry_id}、agent_run_idは{agent_run_id}です。"
        f"アップロードされたファイルは以下の{len(files)}件です。\n{file_list}\n\n"
        "これらのファイルを解析し、固定項目を抽出してExtractionResultを確定してください。"
    )


def _build_agent02_prompt(
    inquiry_id: int, agent_run_id: int, extraction_payload: dict, *, is_additional: bool
) -> str:
    mode_note = (
        "既存引合への追加アップロードです。load_existing_inquiryで既存データを取得してから"
        "統合してください。"
        if is_additional
        else "新規アップロードです（load_existing_inquiryは不要です）。"
    )
    return (
        f"引合ID(inquiry_id)は{inquiry_id}、agent_run_idは{agent_run_id}です。{mode_note}\n\n"
        "AGENT-01のExtractionResultは以下の通りです:\n\n"
        + json.dumps(extraction_payload, ensure_ascii=False)
        + "\n\nこの内容を検証・統合し、構造化JSON（確認中状態）として確定してください。"
    )


async def _await_job(run_id: str, *, poll_interval_s: float = 2.0):
    while (job := jobs.get_job(run_id)) is not None and job.status == "running":
        await asyncio.sleep(poll_interval_s)
    return job


async def _mark_failed(agent_run_id: int, job_status: str) -> None:
    async with AsyncSessionLocal() as session:
        agent_run = await AgentRunRepository(session).get(agent_run_id)
        if agent_run is None:
            return
        if job_status in _STOPPED_REASONS:
            agent_run.status = "stopped"
            agent_run.stage = "stopped"
            agent_run.error_message = (
                f"強制停止（{job_status}）。一部項目の処理が途中で停止しました。"
            )
        else:
            agent_run.status = "failed"
            agent_run.stage = "failed"
            agent_run.error_message = f"エージェント実行に失敗しました（{job_status}）"
        await session.commit()


async def _orchestrate(
    inquiry_id: int, agent_run_1_id: int, files: list[InquiryFile], *, trigger: Trigger
) -> None:
    async with AsyncSessionLocal() as session:
        agent_run_1 = await AgentRunRepository(session).get(agent_run_1_id)
        if agent_run_1 is not None:
            agent_run_1.stage = "extracting"
            await session.commit()

    prompt1 = _build_agent01_prompt(inquiry_id, agent_run_1_id, files)
    run_id_1 = jobs.start_agent_job(
        prompt1, AGENT01_SPEC, scenario=f"inquiry-{inquiry_id}-agent01-{trigger}"
    )
    job1 = await _await_job(run_id_1)
    if job1 is None or job1.status != "completed":
        await _mark_failed(agent_run_1_id, job1.status if job1 else "failed")
        return

    async with AsyncSessionLocal() as session:
        extraction_result = await ExtractionResultRepository(
            session
        ).get_unconsumed_by_inquiry(inquiry_id)
        if extraction_result is None:
            return
        extraction_payload = extraction_result.payload
        agent_run_2 = await AgentRunRepository(session).add(
            AgentRun(
                inquiry_id=inquiry_id,
                agent_name="agent02_verification",
                trigger=trigger,
                status="running",
                stage="structuring",
                progress_percent=55,
            )
        )
        await session.commit()
        agent_run_2_id = agent_run_2.id

    prompt2 = _build_agent02_prompt(
        inquiry_id,
        agent_run_2_id,
        extraction_payload,
        is_additional=(trigger == "additional_upload"),
    )
    run_id_2 = jobs.start_agent_job(
        prompt2, AGENT02_SPEC, scenario=f"inquiry-{inquiry_id}-agent02-{trigger}"
    )
    job2 = await _await_job(run_id_2)
    if job2 is None or job2.status != "completed":
        await _mark_failed(agent_run_2_id, job2.status if job2 else "failed")


async def orchestrate_new_upload(
    inquiry_id: int, agent_run_1_id: int, files: list[InquiryFile]
) -> None:
    """FUNC-01新規アップロード後のAGENT-01→AGENT-02連鎖。POST /inquiriesから
    バックグラウンドタスクとして起動される（HTTPレスポンスは待たない）。"""
    await _orchestrate(inquiry_id, agent_run_1_id, files, trigger="new_upload")


async def orchestrate_additional_upload(
    inquiry_id: int, agent_run_1_id: int, files: list[InquiryFile]
) -> None:
    """FUNC-01追加アップロード（SCR-05）後のAGENT-01→AGENT-02連鎖。"""
    await _orchestrate(inquiry_id, agent_run_1_id, files, trigger="additional_upload")
