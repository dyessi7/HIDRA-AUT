"""Instanciación centralizada del modelo de lenguaje.

Si hay ANTHROPIC_API_KEY, usa Claude real.
Si no, usa FakeListChatModel para que tests y desarrollo local funcionen sin red.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """Devuelve la instancia del modelo, creándola una sola vez."""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    model_name = os.environ.get(
        "ANTHROPIC_MODEL",
        "claude-sonnet-4-5",
    )

    if api_key:
        from langchain_anthropic import ChatAnthropic

        logger.info(
            "Usando Claude real: %s",
            model_name,
        )

        return ChatAnthropic(
        model_name=model_name,
        api_key=SecretStr(api_key),
        temperature=0,
        timeout=None,
        stop=None,
    )

    # Modo mock para desarrollo sin API key
    from langchain_core.language_models.fake_chat_models import (
        FakeListChatModel,
    )

    logger.warning(
        "ANTHROPIC_API_KEY no definido. Usando FakeListChatModel. "
        "Para ejecución real, configura la clave en .env."
    )

    return FakeListChatModel(
    responses=[
        "Análisis mock: agrupados 2 avisos como una sola falla.",
        (
            "Recomendación mock: CU-01 "
            "(misma zona, especialidad coincide)."
        ),
        "Orden mock: emitida correctamente.",
    ]
)