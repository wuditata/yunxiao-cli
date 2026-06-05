from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from ..domain.store import Store
from ..infra.flow import FlowAPI
from .errors import CliError
from .profile_service import ProfileService


class FlowService:
    def __init__(self, store: Store, profile_service: ProfileService):
        self.store = store
        self.profile_service = profile_service

    def list_pipelines(
        self,
        *,
        profile_name: str | None,
        search: str | None = None,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        pipelines = self._flow_api(profile).list_pipelines(
            profile.org,
            search=search,
            status=status,
            page=page,
            per_page=per_page,
        )
        return {
            "pipelines": pipelines,
            "total": len(pipelines),
            "filters": {
                "search": search,
                "status": status,
                "page": page,
                "perPage": per_page,
            },
        }, self._profile_dict(profile)

    def get_pipeline(
        self,
        *,
        profile_name: str | None,
        pipeline_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        pipeline = self._flow_api(profile).get_pipeline(profile.org, pipeline_id)
        return {"pipeline": pipeline}, self._profile_dict(profile)

    def create_run(
        self,
        *,
        profile_name: str | None,
        pipeline_id: str,
        params: str | None = None,
        params_file: str | None = None,
        param_pairs: list[str] | None = None,
        branch: str | None = None,
        tag: str | None = None,
        branches: list[str] | None = None,
        branch_mode: bool = False,
        repositories: list[str] | None = None,
        repo_branch_pairs: list[str] | None = None,
        repo_tag_pairs: list[str] | None = None,
        env_pairs: list[str] | None = None,
        pipeline_artifact_pairs: list[str] | None = None,
        acr_artifact_pairs: list[str] | None = None,
        package_artifact_pairs: list[str] | None = None,
        release_branch: str | None = None,
        create_release_branch: bool = False,
        comment: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        api = self._flow_api(profile)
        run_params = self._build_run_params(
            api=api,
            org_id=profile.org,
            pipeline_id=pipeline_id,
            params=params,
            params_file=params_file,
            param_pairs=param_pairs or [],
            branch=branch,
            tag=tag,
            branches=branches or [],
            branch_mode=branch_mode,
            repositories=repositories or [],
            repo_branch_pairs=repo_branch_pairs or [],
            repo_tag_pairs=repo_tag_pairs or [],
            env_pairs=env_pairs or [],
            pipeline_artifact_pairs=pipeline_artifact_pairs or [],
            acr_artifact_pairs=acr_artifact_pairs or [],
            package_artifact_pairs=package_artifact_pairs or [],
            release_branch=release_branch,
            create_release_branch=create_release_branch,
            comment=comment,
        )
        run_id = api.create_pipeline_run(profile.org, pipeline_id, params=run_params)
        return {
            "pipelineId": pipeline_id,
            "pipelineRunId": run_id,
        }, self._profile_dict(profile)

    def start_job(
        self,
        *,
        profile_name: str | None,
        pipeline_id: str,
        pipeline_run_id: str,
        job_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        profile = self.profile_service.get_profile(profile_name)
        started = self._flow_api(profile).start_pipeline_job(
            profile.org,
            pipeline_id,
            pipeline_run_id,
            job_id,
        )
        return {
            "pipelineId": pipeline_id,
            "pipelineRunId": pipeline_run_id,
            "jobId": job_id,
            "started": started,
        }, self._profile_dict(profile)

    def _build_run_params(
        self,
        *,
        api: FlowAPI,
        org_id: str,
        pipeline_id: str,
        params: str | None,
        params_file: str | None,
        param_pairs: list[str],
        branch: str | None,
        tag: str | None,
        branches: list[str],
        branch_mode: bool,
        repositories: list[str],
        repo_branch_pairs: list[str],
        repo_tag_pairs: list[str],
        env_pairs: list[str],
        pipeline_artifact_pairs: list[str],
        acr_artifact_pairs: list[str],
        package_artifact_pairs: list[str],
        release_branch: str | None,
        create_release_branch: bool,
        comment: str | None,
    ) -> str | None:
        raw_params = self._read_raw_params(params=params, params_file=params_file)
        if raw_params is not None:
            return raw_params

        params_object = self._parse_param_pairs(param_pairs)
        self._apply_branch_mode_params(params_object, branch=branch, branches=branches, branch_mode=branch_mode)
        self._apply_release_params(
            params_object,
            release_branch=release_branch,
            create_release_branch=create_release_branch,
        )
        self._apply_optional_mapping(params_object, "envs", self._parse_string_pairs(env_pairs, "--env"))
        self._apply_optional_mapping(
            params_object,
            "runningPipelineArtifacts",
            self._parse_string_pairs(pipeline_artifact_pairs, "--pipeline-artifact"),
        )
        self._apply_optional_mapping(
            params_object,
            "runningAcrArtifacts",
            self._parse_string_pairs(acr_artifact_pairs, "--acr-artifact"),
        )
        self._apply_optional_mapping(
            params_object,
            "runningPackagesArtifacts",
            self._parse_string_pairs(package_artifact_pairs, "--package-artifact"),
        )
        self._apply_repository_params(
            params_object,
            api=api,
            org_id=org_id,
            pipeline_id=pipeline_id,
            repositories=repositories,
            repo_branch_pairs=repo_branch_pairs,
            repo_tag_pairs=repo_tag_pairs,
            branch=branch,
            tag=tag,
        )
        if comment:
            params_object["comment"] = comment
        if not params_object:
            return None
        return json.dumps(params_object, ensure_ascii=False, separators=(",", ":"))

    def _apply_repository_params(
        self,
        params_object: dict[str, Any],
        *,
        api: FlowAPI,
        org_id: str,
        pipeline_id: str,
        repositories: list[str],
        repo_branch_pairs: list[str],
        repo_tag_pairs: list[str],
        branch: str | None,
        tag: str | None,
    ) -> None:
        repo_configs = self._build_repository_configs(
            repositories=repositories,
            repo_branch_pairs=repo_branch_pairs,
            repo_tag_pairs=repo_tag_pairs,
            branch=branch,
            tag=tag,
        )
        if not repo_configs and (branch or tag):
            repo_configs = self._repository_configs_from_pipeline(api, org_id, pipeline_id, branch=branch, tag=tag)
        running_branchs = {item["url"]: item["branch"] for item in repo_configs if item.get("branch")}
        running_tags = {item["url"]: item["tag"] for item in repo_configs if item.get("tag")}
        if running_branchs:
            params_object["runningBranchs"] = running_branchs
        if running_tags:
            params_object["runningTags"] = running_tags
        if branch and not running_branchs and not running_tags and "branchModeBranchs" not in params_object:
            params_object["branchModeBranchs"] = [branch]

    def _build_repository_configs(
        self,
        *,
        repositories: list[str],
        repo_branch_pairs: list[str],
        repo_tag_pairs: list[str],
        branch: str | None,
        tag: str | None,
    ) -> list[dict[str, str]]:
        configs: dict[str, dict[str, str]] = {}
        for repo_url in self._split_values(repositories):
            configs[repo_url] = {"url": repo_url}
            if branch:
                configs[repo_url]["branch"] = branch
            if tag:
                configs[repo_url]["tag"] = tag
        for repo_url, repo_branch in self._parse_string_pairs(repo_branch_pairs, "--repo-branch").items():
            configs.setdefault(repo_url, {"url": repo_url})["branch"] = repo_branch
        for repo_url, repo_tag in self._parse_string_pairs(repo_tag_pairs, "--repo-tag").items():
            configs.setdefault(repo_url, {"url": repo_url})["tag"] = repo_tag
        return list(configs.values())

    def _repository_configs_from_pipeline(
        self,
        api: FlowAPI,
        org_id: str,
        pipeline_id: str,
        *,
        branch: str | None,
        tag: str | None,
    ) -> list[dict[str, str]]:
        pipeline = api.get_pipeline(org_id, pipeline_id)
        sources = (pipeline.get("pipelineConfig") or {}).get("sources") or []
        configs: list[dict[str, str]] = []
        for source in sources:
            data = source.get("data") if isinstance(source, dict) else {}
            repo_url = data.get("repo") if isinstance(data, dict) else None
            if not repo_url:
                continue
            item = {"url": str(repo_url)}
            if branch:
                item["branch"] = branch
            if tag:
                item["tag"] = tag
            configs.append(item)
        return configs

    def _read_raw_params(self, *, params: str | None, params_file: str | None) -> str | None:
        if params and params_file:
            raise CliError("--params 与 --params-file 不能同时使用")
        if params_file:
            try:
                params = Path(params_file).read_text(encoding="utf-8").strip()
            except OSError as error:
                raise CliError(f"读取运行参数文件失败：{params_file}") from error
        if params is None:
            return None
        self._parse_json_object(params, "--params")
        return params

    def _parse_param_pairs(self, values: list[str]) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        for key, raw_value in self._iter_key_value(values, "--param"):
            try:
                parsed[key] = json.loads(raw_value)
            except JSONDecodeError:
                parsed[key] = raw_value
        return parsed

    def _parse_string_pairs(self, values: list[str], option_name: str) -> dict[str, str]:
        return {key: raw_value for key, raw_value in self._iter_key_value(values, option_name)}

    def _iter_key_value(self, values: list[str], option_name: str):
        for value in values:
            for item in self._split_values([value]):
                if "=" not in item:
                    raise CliError(f"{option_name} 参数格式错误：{item}")
                key, raw_value = item.split("=", 1)
                key = key.strip()
                if not key:
                    raise CliError(f"{option_name} 参数 key 不能为空")
                yield key, raw_value

    @staticmethod
    def _split_values(values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            result.extend(item.strip() for item in value.split(",") if item.strip())
        return result

    @staticmethod
    def _apply_branch_mode_params(
        params_object: dict[str, Any],
        *,
        branch: str | None,
        branches: list[str],
        branch_mode: bool,
    ) -> None:
        branch_values = FlowService._split_values(branches)
        if branch_mode and branch and not branch_values:
            branch_values = [branch]
        if branch_values:
            params_object["branchModeBranchs"] = branch_values

    @staticmethod
    def _apply_release_params(
        params_object: dict[str, Any],
        *,
        release_branch: str | None,
        create_release_branch: bool,
    ) -> None:
        if create_release_branch:
            params_object["needCreateBranch"] = True
        if release_branch:
            params_object["releaseBranch"] = release_branch

    @staticmethod
    def _apply_optional_mapping(params_object: dict[str, Any], key: str, values: dict[str, str]) -> None:
        if values:
            params_object[key] = values

    @staticmethod
    def _parse_json_object(raw: str, source: str) -> dict[str, Any]:
        try:
            data = json.loads(raw)
        except JSONDecodeError as error:
            raise CliError(f"{source} 必须是 JSON 对象") from error
        if not isinstance(data, dict):
            raise CliError(f"{source} 必须是 JSON 对象")
        return data

    def _flow_api(self, profile) -> FlowAPI:
        account = self.store.get_account(profile.account)
        return FlowAPI(token=account.token)

    @staticmethod
    def _profile_dict(profile) -> dict[str, Any]:
        return {
            "name": profile.name,
            "account": profile.account,
            "org": profile.org,
            "project": profile.project,
            "projects": profile.projects,
        }
