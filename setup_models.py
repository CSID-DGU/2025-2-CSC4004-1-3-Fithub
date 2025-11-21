#!/usr/bin/env python3
"""
AI 모델 다운로드 및 설정 스크립트.

이 스크립트는 각 MCP 서비스에 필요한 모델들을 다운로드합니다.
당신의 커스텀 모델이 있다면, 해당 부분을 수정하세요.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 모델 캐시 디렉토리
MODELS_DIR = Path(__file__).parent / "models"

# 기본 모델 설정
MODELS_CONFIG = {
    "summarization": {
        "codet5": "Salesforce/codet5p-base",
        "starcoder2": "bigcode/starcoder2-3b",
        "codellama": "meta-llama/CodeLlama-7b-Instruct-hf",
        "unixcoder": "microsoft/unixcoder-base",
    },
    "structural_analysis": {
        "graphcodebert": "microsoft/graphcodebert-base",
        "codebert": "microsoft/codebert-base",
    },
    "semantic_embedding": {
        "codebert": "microsoft/codebert-base",
        "cubert": "google/cubert-base-pytorch",
    },
    "repository_analysis": {
        "codebert": "microsoft/codebert-base",
    },
    "task_recommender": {
        "codebert": "microsoft/codebert-base",
    },
}


def setup_model(model_id: str, cache_dir: Path, model_type: str = "transformer") -> bool:
    """
    단일 모델을 다운로드하고 캐싱합니다.

    Args:
        model_id: HuggingFace 모델 ID
        cache_dir: 캐시 디렉토리
        model_type: 모델 타입

    Returns:
        성공 여부
    """
    try:
        print(f"⏳ Downloading {model_id}...")

        cache_dir.mkdir(parents=True, exist_ok=True)

        if model_type == "transformer":
            from transformers import AutoModel, AutoTokenizer

            # 모델 다운로드
            model = AutoModel.from_pretrained(
                model_id,
                cache_dir=str(cache_dir),
                trust_remote_code=True,
            )

            # 토크나이저 다운로드
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=str(cache_dir),
                trust_remote_code=True,
            )

            print(f"✓ {model_id} downloaded successfully")
            return True

    except Exception as e:
        print(f"✗ Failed to download {model_id}: {e}")
        return False


def setup_all_models(interactive: bool = True) -> None:
    """
    모든 모델을 다운로드합니다.

    Args:
        interactive: 사용자 상호작용 여부
    """
    print("=" * 60)
    print("Code Analysis Agent - Model Setup")
    print("=" * 60)
    print()

    total_models = sum(len(models) for models in MODELS_CONFIG.values())
    downloaded = 0
    failed = 0

    for service, models in MODELS_CONFIG.items():
        service_dir = MODELS_DIR / service
        print(f"\n📦 {service.upper()}")
        print("-" * 40)

        for model_name, model_id in models.items():
            cache_dir = service_dir / model_name

            if cache_dir.exists() and any(cache_dir.iterdir()):
                print(f"  ✓ {model_name} (already cached)")
                downloaded += 1
                continue

            if interactive:
                response = input(
                    f"  Download {model_name} ({model_id})? [y/n/skip all]: "
                ).lower()

                if response == "skip all":
                    print(f"  ⊘ Skipped remaining models in {service}")
                    break
                elif response != "y":
                    continue

            if setup_model(model_id, cache_dir):
                downloaded += 1
            else:
                failed += 1

    print()
    print("=" * 60)
    print(f"Summary: {downloaded}/{total_models} models ready")
    if failed > 0:
        print(f"⚠️  {failed} models failed to download")
    print("=" * 60)
    print()

    if downloaded == total_models:
        print("✓ All models successfully set up!")
        print()
        print("Next steps:")
        print("  1. Start services: docker-compose up -d")
        print("  2. Run analysis: curl -X POST http://localhost:8000/analyze ...")
    else:
        print("⚠️  Some models are missing. Services may have limited functionality.")
        print()
        print("To retry setup:")
        print("  python setup_models.py")


def setup_custom_model(
    service: str,
    model_name: str,
    model_path: str,
) -> bool:
    """
    커스텀 모델을 설정합니다.

    Args:
        service: 서비스명 (summarization, structural_analysis 등)
        model_name: 모델 이름
        model_path: 모델 경로 (로컬 또는 HuggingFace ID)

    Returns:
        성공 여부
    """
    print(f"Setting up custom model: {model_name} for {service}")

    cache_dir = MODELS_DIR / service / model_name

    return setup_model(model_path, cache_dir, model_type="transformer")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup AI models for code analysis agent")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Download all models without prompting"
    )
    parser.add_argument(
        "--service",
        type=str,
        help="Setup specific service only"
    )
    parser.add_argument(
        "--skip-large",
        action="store_true",
        help="Skip large models (e.g., CodeLlama)"
    )

    args = parser.parse_args()

    try:
        interactive = not args.non_interactive

        # 큰 모델 제외
        if args.skip_large:
            if "summarization" in MODELS_CONFIG:
                MODELS_CONFIG["summarization"].pop("codellama", None)
                MODELS_CONFIG["summarization"].pop("starcoder2", None)
            print("⊘ Large models skipped")
            print()

        # 특정 서비스만 설정
        if args.service:
            if args.service not in MODELS_CONFIG:
                print(f"Unknown service: {args.service}")
                sys.exit(1)

            service_config = {args.service: MODELS_CONFIG[args.service]}
            MODELS_CONFIG = service_config

        setup_all_models(interactive=interactive)

    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)
