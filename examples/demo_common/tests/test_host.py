# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

import asyncio
import importlib
import os

import pytest

from demo_common import host as host_module
from demo_common import host_approval_default, load_demo_env, model_override, spawn_background
from demo_common.host import _background_tasks


@pytest.mark.parametrize(
    ("value", "expected"), [(None, True), ("0", False), ("1", True), ("", True), ("true", True)]
)
def test_only_an_explicit_zero_turns_host_approval_off(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv("MERCHANT_REQUIRE_HOST_APPROVAL", raising=False)
    else:
        monkeypatch.setenv("MERCHANT_REQUIRE_HOST_APPROVAL", value)
    assert host_approval_default() is expected


@pytest.mark.parametrize("value", [None, "", "  "])
def test_no_model_override_without_a_non_blank_anthropic_model(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    else:
        monkeypatch.setenv("ANTHROPIC_MODEL", value)
    assert model_override() == {}


def test_anthropic_model_names_the_turn_loop_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", " claude-opus-5 ")
    assert model_override() == {"model": "claude-opus-5"}


@pytest.mark.parametrize("vertical", ["retail", "travel", "telecom", "entertainment"])
def test_every_vertical_builds_both_configs_on_anthropic_model(monkeypatch, vertical):
    monkeypatch.setenv("ANTHROPIC_MODEL", "gateway-model")
    agent_config = importlib.import_module(f"{vertical}.api.agent_config")

    assert agent_config.build_shopping_config().model == "gateway-model"
    assert agent_config.build_merchant_config("ACME").model == "gateway-model"


@pytest.fixture
def env_dirs(tmp_path, monkeypatch):
    """A repo root and an example directory under ``tmp_path``, with the loader pointed at
    the former and no credential variables in the environment."""
    repo_root, example_root = tmp_path / "repo", tmp_path / "repo" / "examples" / "retail"
    example_root.mkdir(parents=True)
    monkeypatch.setattr(host_module, "REPO_ROOT", repo_root)
    for name in (
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "COMMERCE_DEMO_AUTH",
    ):
        monkeypatch.delenv(name, raising=False)
    return repo_root, example_root


def test_a_key_in_the_environment_survives_a_blank_env_file(env_dirs, monkeypatch):
    repo_root, example_root = env_dirs
    (repo_root / ".env").write_text("ANTHROPIC_API_KEY=\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-the-shell")

    load_demo_env(example_root)

    assert os.environ["ANTHROPIC_API_KEY"] == "from-the-shell"


def test_the_example_env_file_fills_in_before_the_repo_root_one(env_dirs):
    repo_root, example_root = env_dirs
    (repo_root / ".env").write_text("ANTHROPIC_API_KEY=root-key\n")
    (example_root / ".env").write_text("ANTHROPIC_API_KEY=example-key\n")

    load_demo_env(example_root)

    assert os.environ["ANTHROPIC_API_KEY"] == "example-key"


def test_the_repo_root_env_file_is_read_when_the_example_has_none(env_dirs):
    repo_root, example_root = env_dirs
    (repo_root / ".env").write_text("ANTHROPIC_API_KEY=root-key\n")

    load_demo_env(example_root)

    assert os.environ["ANTHROPIC_API_KEY"] == "root-key"


def test_sdk_auth_clears_key_variables_and_reads_no_file(env_dirs, monkeypatch):
    repo_root, example_root = env_dirs
    (repo_root / ".env").write_text("ANTHROPIC_API_KEY=root-key\n")
    monkeypatch.setenv("COMMERCE_DEMO_AUTH", "sdk")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-the-shell")

    load_demo_env(example_root)

    assert "ANTHROPIC_API_KEY" not in os.environ


def test_a_base_url_in_the_env_file_reaches_the_environment(env_dirs):
    repo_root, example_root = env_dirs
    (repo_root / ".env").write_text(
        "ANTHROPIC_API_KEY=root-key\nANTHROPIC_BASE_URL=https://llm-gateway.internal.example\n"
    )

    load_demo_env(example_root)

    assert os.environ["ANTHROPIC_BASE_URL"] == "https://llm-gateway.internal.example"


def test_a_base_url_in_the_environment_wins_over_the_env_file(env_dirs, monkeypatch):
    repo_root, example_root = env_dirs
    (repo_root / ".env").write_text("ANTHROPIC_BASE_URL=https://from-the-file.example\n")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://from-the-shell.example")

    load_demo_env(example_root)

    assert os.environ["ANTHROPIC_BASE_URL"] == "https://from-the-shell.example"


@pytest.mark.parametrize("auth_mode", [None, "sdk"])
def test_a_blank_base_url_is_dropped_so_the_client_keeps_its_default(
    env_dirs, monkeypatch, auth_mode
):
    repo_root, example_root = env_dirs
    (repo_root / ".env").write_text("ANTHROPIC_API_KEY=root-key\nANTHROPIC_BASE_URL=\n")
    if auth_mode:
        monkeypatch.setenv("COMMERCE_DEMO_AUTH", auth_mode)
        monkeypatch.setenv("ANTHROPIC_BASE_URL", " ")

    load_demo_env(example_root)

    assert "ANTHROPIC_BASE_URL" not in os.environ


async def test_spawn_background_holds_the_task_until_it_finishes():
    started, release = asyncio.Event(), asyncio.Event()

    async def work() -> None:
        started.set()
        await release.wait()

    spawn_background(work())
    await asyncio.wait_for(started.wait(), 1)
    assert _background_tasks
    release.set()
    for _ in range(10):
        if not _background_tasks:
            break
        await asyncio.sleep(0)
    assert not _background_tasks
