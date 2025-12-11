"""
mcp/summarization/summarizer.py
Core summarization logic with Hugging Face API support (Polyglot).
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from huggingface_hub import InferenceClient
from agent.config import Config

logger = logging.getLogger(__name__)

class CodeSummarizer:
    def __init__(self, device: Optional[str] = None):
        token = Config.HF_API_KEY
        if not token:
            logger.warning("HF_API_KEY is missing via Config.")

        # self.client = InferenceClient(token=token)
        self.client = None # Force disable API client
        self.model_id = Config.MODEL_SUMMARIZER

        # 3개 Expert 모델 ID
        self.model_logic = Config.MODEL_SUMMARIZER_LOGIC
        self.model_intent = Config.MODEL_SUMMARIZER_INTENT
        self.model_structure = Config.MODEL_SUMMARIZER_STRUCTURE

        # 지원 확장자 (Polyglot)
        self.valid_exts = {'.py', '.js', '.ts', '.java', '.go', '.cpp', '.c', '.cs', '.rs'}

    def summarize_file(self, file_path: str, model_name: str = None) -> Dict[str, Any]:
        """단일 파일 요약"""
        target_model = self.model_id
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            summary = self._generate_summary(code, target_model)

            return {
                "code_id": Path(file_path).name,
                "text": summary,
                "level": "file",
                "model": target_model,
                "confidence": 0.85
            }
        except Exception as e:
            logger.error(f"File summary failed: {e}")
            return {"error": str(e)}

    def summarize_code(self, code: str, code_id: str, model_name: str = None) -> Dict[str, Any]:
        """코드 조각 요약"""
        target_model = self.model_id
        summary = self._generate_summary(code, target_model)
        return {
            "code_id": code_id,
            "text": summary,
            "level": "snippet",
            "model": target_model,
            "confidence": 0.85
        }

    def summarize_code_local(self, code: str) -> str:
        """[Local SLM] 로컬 모델을 사용한 요약 (CodeT5-small)"""
        try:
            from transformers import pipeline
            import torch

            # 파이프라인 캐싱 (싱글톤 패턴)
            if not hasattr(self, '_local_pipeline'):
                logger.info("Loading local summarization model (Salesforce/codet5-small)...")
                
                # Device Auto-detection
                device = -1 # CPU Default
                if torch.backends.mps.is_available():
                    device = "mps"
                    logger.info("🚀 Using MPS (Metal) acceleration on macOS.")
                elif torch.cuda.is_available():
                    device = 0
                    logger.info("🚀 Using CUDA acceleration.")
                
                self._local_pipeline = pipeline("summarization", model="Salesforce/codet5-small", device=device)
            
            # 입력 길이 제한 (CodeT5 max position embedding is usually 512)
            input_code = code[:512] 
            
            result = self._local_pipeline(input_code, max_length=50, min_length=10, do_sample=False)
            return result[0]['summary_text']
        except Exception as e:
            logger.error(f"Local summarization failed: {e}")
            return "Local summary generation failed."

        
    def summarize_repository(self, repo_path: str, max_files: int = Config.MAX_ANALYSIS_FILES, target_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """저장소 전체 앙상블 요약 (다국어 지원 & 선별적 재분석)"""
        try:
            repo_path = Path(repo_path)
            all_files = []

            # 파일 검색
            for root, dirs, files in os.walk(repo_path):
                # 불필요한 디렉토리 제외
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'venv', 'node_modules', 'dist', 'build', '.git'}]
                for file in files:
                    if Path(file).suffix in self.valid_exts:
                        all_files.append(Path(root) / file)

            target_files = []
            
            # [Filtering Logic]
            if target_ids:
                logger.info(f"Targeted Analysis Mode: Filtering {len(target_ids)} files.")
                for f in all_files:
                    fid = str(f.relative_to(repo_path)).replace("\\", "/")
                    if fid in target_ids:
                        target_files.append(f)
            else:
                target_files = all_files[:max_files]

            file_summaries = []

            logger.info(f"Ensemble summarizing {len(target_files)} files in {repo_path}")

            for file_path in target_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()

                    # 상대 경로 ID
                    code_id = str(file_path.relative_to(repo_path)).replace("\\", "/")

                    # ★ 앙상블 호출 (기존 단일 호출 대체)
                    if True or Config.USE_LOCAL_SUMMARIZER: # FORCE LOCAL FOR DEMO
                        # [Local Mode] Single Pass CodeT5 (No Ensemble to save time/resources)
                        local_text = self.summarize_code_local(code)
                        file_summaries.append({
                            "code_id": code_id,
                            "text": local_text,
                            "level": "file",
                            "model": "codet5-small-local"
                        })
                    else:
                        # [Cloud Mode] Ensemble
                        ensemble_result = self._generate_ensemble_summary(code[:2000], code_id)
                        file_summaries.append(ensemble_result)

                except Exception as e:
                    logger.warning(f"Failed to summarize {file_path}: {e}")

            return {
                "summary": f"Ensemble analyzed {len(file_summaries)} files.",
                "file_summaries": file_summaries,
                "metadata": {
                    "total_files": len(target_files),
                    "ensemble_mode": True,
                    "partial_retry": bool(target_ids)
                },
                "statistics": {"total_files": len(target_files)}
            }
        except Exception as e:
            logger.error(f"Repo summary failed: {e}")
            return {"error": str(e)}

    def _generate_ensemble_summary(self, code: str, code_id: str, ast_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """3개 모델 앙상블 요약 생성 (AST 메타데이터 활용)"""
        try:
            # 1. 3개 Expert 호출 (각각 다른 관점)
            # [Logic Expert] Local CodeT5 (Fast & Efficient) - User Request
            logic_summary = self.summarize_code_local(code)

            intent_summary = self._generate_summary(
                code,
                self.model_intent,
                prompt_type="intent"
            )

            # [Structure Expert] Qwen API + AST Context (Enhanced)
            structure_context = code
            if ast_metadata:
                # Enhance context with pre-extracted AST info
                structure_context = f"Detected Structure Metadata:\n- Complexity: {ast_metadata.get('complexity', '?')}\n- Imports: {ast_metadata.get('imports', [])}\n- Classes: {ast_metadata.get('classes', [])}\n\nCode:\n{code}"
            
            structure_summary = self._generate_summary(
                structure_context,
                self.model_structure,
                prompt_type="structure"
            )

            # 2. 통합
            unified = self._integrate_summaries(logic_summary, intent_summary, structure_summary)

            # 3. 품질 점수 계산
            quality = self._calculate_quality(logic_summary, intent_summary, structure_summary)

            # 4. 결과 반환
            return {
                "code_id": code_id,
                "text": unified,  # 호환성을 위해 "text" 키도 포함
                "unified_summary": unified,
                "expert_views": {
                    "logic": logic_summary,
                    "intent": intent_summary,
                    "structure": structure_summary
                },
                "quality_score": quality,
                "level": "file"
            }

        except Exception as e:
            logger.error(f"Ensemble summary failed for {code_id}: {e}")
            # 폴백: 단일 모델 사용
            fallback = self._generate_summary(code, self.model_logic)
            return {
                "code_id": code_id,
                "text": fallback,
                "unified_summary": fallback,
                "quality_score": 0.5,
                "level": "file"
            }

    def _integrate_summaries(self, logic: str, intent: str, structure: str) -> str:
        """유사도 기반 통합: 가장 긴 요약을 기준으로 나머지 정보 추가"""
        summaries = {
            "logic": logic,
            "intent": intent,
            "structure": structure
        }

        # 1. 가장 긴 요약 선택 (보통 가장 상세)
        base_key = max(summaries, key=lambda k: len(summaries[k]))
        base = summaries[base_key]

        # 2. 나머지 요약에서 unique 키워드 추출
        other_summaries = [s for k, s in summaries.items() if k != base_key]
        unique_info = []

        for summary in other_summaries:
            # 간단한 키워드 추출: 대문자로 시작하거나 특수 용어
            words = summary.split()
            for word in words:
                if word.istitle() and word not in base and word not in unique_info:
                    unique_info.append(word)

        # 3. 통합
        if unique_info:
            return f"{base} Related aspects: {', '.join(unique_info[:3])}."
        else:
            return base

    def _calculate_quality(self, logic: str, intent: str, structure: str) -> float:
        """3개 요약의 일관성 점수 계산 (TF-IDF 유사도)"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            # 1. TF-IDF 벡터화
            vectorizer = TfidfVectorizer()
            vectors = vectorizer.fit_transform([logic, intent, structure])

            # 2. 쌍별 유사도
            sim_matrix = cosine_similarity(vectors)
            sim_12 = sim_matrix[0][1]
            sim_23 = sim_matrix[1][2]
            sim_13 = sim_matrix[0][2]

            # 3. 평균 유사도 = 일관성
            avg_similarity = (sim_12 + sim_23 + sim_13) / 3

            return float(avg_similarity)

        except Exception as e:
            logger.warning(f"Quality calculation failed: {e}")
            return 0.7  # 기본값


    def _generate_summary_via_chat(self, prompt: str, model_id: str) -> str:
        """HF Chat Completion API 호출 (Instruct 모델용)"""
        if "starcoder" in model_id.lower():
            # StarCoder is completion-based usually, but StarCoder2-Instruct exists.
            # Assuming pure completion for base StarCoder2.
             messages = prompt # Pass string directly? No, client.chat_completion needs messages. 
             # Let's try text_generation for non-instruct StarCoder.
             # If "is_chat_model" logic caught it, it means we treat it as chat.
             pass 

        messages = [{"role": "user", "content": prompt}]
        try:
            response = self.client.chat_completion(
                messages,
                model=model_id,
                max_tokens=200,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
             # Fallback to text_generation if chat fails (common for non-instruct models)
             return self.client.text_generation(prompt, model=model_id, max_new_tokens=200)
        except Exception as e:
            raise e

    def _generate_summary(self, code: str, model_id: str, prompt_type: str = "general") -> str:
        """HF API 호출 (프롬프트 타입 기반, Text-Gen 및 Chat 지원)"""
        prompts = {
            "logic": f"Summarize the function inputs, outputs, and core algorithm in one sentence:\n\n{code}",
            "intent": f"Explain the business purpose and why this code exists in one sentence:\n\n{code}",
            "structure": f"Describe the code structure, patterns, and design in one sentence:\n\n{code}",
            "general": f"Summarize the following code's functionality in one sentence:\n\n{code}"
        }

        prompt = prompts.get(prompt_type, prompts["general"])

        # [SAFE MODE] Throttling & Retry (Aggressive)
        import time
        max_retries = 3
        base_delay = 5.0

        is_chat_model = "instruct" in model_id.lower() or "chat" in model_id.lower() or "qwen" in model_id.lower()

        if self.client is None:
             logger.warning(f"HF Client is None. Skipping API call for {model_id}. Using Local/Dummy.")
             return self._get_dummy_summary(prompt_type)

        for attempt in range(max_retries):
            try:
                # Throttling
                wait_time = base_delay * (attempt + 1)
                if attempt > 0:
                    logger.warning(f"Throttling HF API: Waiting {wait_time}s before retry {attempt+1}...")
                    time.sleep(wait_time) 
                
                # [Unified Role-Based Dispatch]
                # Since we use Qwen (Instruct Model) for all roles, we simply use the role prompt.
                if getattr(Config, 'USE_ROLE_BASED_ENSEMBLE', False):
                    # Specialized System Role Prompts for Qwen
                    system_roles = {
                        "logic": "You are a Code Logician. Analyze the code's logic, inputs, and outputs precisely.",
                        "intent": "You are a Senior Product Manager. Explain the business purpose and intent of this code.",
                        "structure": "You are a Software Architect. Describe the structural patterns, class hierarchy, and complexity.",
                        "general": "You are a generic code summarizer."
                    }
                    role_msg = system_roles.get(prompt_type, system_roles["general"])
                    
                    # Construct Chat Messages with System Role
                    messages = [
                        {"role": "system", "content": role_msg},
                        {"role": "user", "content": prompt}
                    ]
                    
                    response = self.client.chat_completion(
                        messages,
                        model=model_id,
                        max_tokens=200,
                        temperature=0.2
                    )
                    return response.choices[0].message.content.strip()
                
                # [Legacy/Compatibility Mode]
                if is_chat_model:
                     return self._generate_summary_via_chat(prompt, model_id)
                else:
                    response = self.client.text_generation(
                        prompt,
                        model=model_id,
                        max_new_tokens=100,
                        temperature=0.2,
                        do_sample=False
                    )
                    return response.strip()

            except Exception as e:
                logger.warning(f"HF API Attempt {attempt+1}/{max_retries} failed ({model_id}): {e}")
                if attempt == max_retries - 1:
                    break # Final failure, proceed to fallback

        # [Fallback Hierarchy]
        # [Fallback Hierarchy]
        # 1. API Failed/Circuit Open -> Check GPU.
        # 2. If GPU (CUDA/MPS) exists -> Try Local CodeT5.
        # 3. If No GPU (CPU only) -> Skip to Dummy (Too slow).
        # 4. If Local Failed -> Dummy Data.
        
        logger.warning(f"HF API Failed (or Circuit Tripped). Checking logic for Fallback...")
        
        try:
            import torch
            has_gpu = torch.cuda.is_available() or (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available())
            
            if has_gpu:
                 logger.info("🚀 GPU Detected. Attempting Local CodeT5 Fallback...")
                 local_summary = self.summarize_code_local(code)
                 return f"[Local Fallback (GPU)] {local_summary}"
            else:
                 logger.warning("⚠️ No GPU detected. Skip Local Model (CPU too slow). Using Dummy Data.")
                 return self._get_dummy_summary(prompt_type)

        except Exception as e:
             logger.warning(f"Local Fallback/GPU Check failed: {e}. Using Dummy Data.")
             return self._get_dummy_summary(prompt_type)

    def _get_dummy_summary(self, prompt_type: str) -> str:
        """[Safety Net] 통신 테스트용 더미 데이터 반환"""
        dummies = {
            "logic": "Input: Data -> Process: Validation -> Output: Result. (Dummy Logic)",
            "intent": "To process user requests and return valid responses. (Dummy Intent)",
            "structure": "Class MainController -> Method handle_request. (Dummy Structure)",
            "general": "This code performs a specific system function. (Dummy Summary)"
        }
        return f"[Dummy Fallback] {dummies.get(prompt_type, dummies['general'])}"

def create_summarizer(device: Optional[str] = None) -> CodeSummarizer:
    return CodeSummarizer(device=device)
