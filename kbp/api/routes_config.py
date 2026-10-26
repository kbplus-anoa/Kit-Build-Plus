"""配置路由：读写抽取配置。只回显密钥是否已配置，绝不回显密钥。"""

from fastapi import APIRouter, HTTPException

import kbp.api.config_store
import kbp.api.deps
import kbp.api.schemas
import kbp.contracts.extractconfig
import kbp.extract.chat_client

router = APIRouter(prefix="/api", tags=["配置"])


@router.get("/config", response_model=kbp.api.schemas.ConfigOut)
def read_config() -> kbp.api.schemas.ConfigOut:
    """读当前抽取配置；密钥只报“是否已配置”。"""
    return _to_out(_load())


@router.put("/config", response_model=kbp.api.schemas.ConfigOut)
def write_config(body: kbp.api.schemas.ConfigIn) -> kbp.api.schemas.ConfigOut:
    """保存抽取配置；不合法时在入口拦下，说明是哪里不对。"""
    cfg = body.to_config()
    reason = kbp.contracts.extractconfig.config_error(cfg)
    if reason:
        raise HTTPException(400, reason)
    with kbp.api.deps.db_lock():
        kbp.api.config_store.save(kbp.api.deps.get_conn(), _fields(cfg))
    return _to_out(cfg)


def _load() -> kbp.contracts.extractconfig.ExtractConfig:
    return kbp.api.config_store.load_config(kbp.api.deps.get_conn())


def _fields(cfg: kbp.contracts.extractconfig.ExtractConfig) -> tuple:
    return (cfg.provider, cfg.model, cfg.base_url, cfg.timeout_s,
            cfg.max_chars, int(cfg.enabled))


def _to_out(cfg: kbp.contracts.extractconfig.ExtractConfig
            ) -> kbp.api.schemas.ConfigOut:
    return kbp.api.schemas.ConfigOut(
        provider=cfg.provider, model=cfg.model, base_url=cfg.base_url,
        timeout_s=cfg.timeout_s, max_chars=cfg.max_chars, enabled=cfg.enabled,
        has_key=kbp.extract.chat_client.has_key(cfg),
        key_env=kbp.contracts.extractconfig.key_env(cfg.provider),
        error=kbp.contracts.extractconfig.config_error(cfg))
