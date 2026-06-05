from __future__ import annotations

from typing import Any

from .base import BaseAPI


class FlowAPI(BaseAPI):
    """云效 Flow 流水线 API。"""

    def list_pipelines(
        self,
        org_id: str,
        *,
        search: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"page": page, "perPage": per_page}
        if search:
            params["pipelineName"] = search
        if status:
            params["statusList"] = status
        items = self.get(f"/oapi/v1/flow/organizations/{org_id}/pipelines", params=params)
        if isinstance(items, list):
            return items
        return items.get("result") or items.get("items") or []

    def get_pipeline(self, org_id: str, pipeline_id: str) -> dict[str, Any]:
        return self.get(f"/oapi/v1/flow/organizations/{org_id}/pipelines/{pipeline_id}")

    def create_pipeline_run(
        self,
        org_id: str,
        pipeline_id: str,
        *,
        params: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {}
        if params is not None:
            payload["params"] = params
        return self.post(
            f"/oapi/v1/flow/organizations/{org_id}/pipelines/{pipeline_id}/runs",
            data=payload,
        )

    def start_pipeline_job(
        self,
        org_id: str,
        pipeline_id: str,
        pipeline_run_id: str,
        job_id: str,
    ) -> bool:
        response = self.post(
            f"/oapi/v1/flow/organizations/{org_id}/pipelines/{pipeline_id}"
            f"/pipelineRuns/{pipeline_run_id}/jobs/{job_id}/start"
        )
        return bool(response)
