import logging
import os
from typing import Generator, Union

import runpod
from ctransformers import AutoModelForCausalLM
from huggingface_hub import hf_hub_download
job_stream = ""
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

repo_file = hf_hub_download(repo_id=os.environ["GGML_REPO"], filename=os.environ["GGML_FILE"], revision=os.environ.get("GGML_REVISION", "main"))
llm = None


def get_llm():
    global llm
    if not llm:
        llm = AutoModelForCausalLM.from_pretrained(repo_file, model_type=os.environ.get("GGML_TYPE", "llama"), gpu_layers=int(os.environ.get("GGML_LAYERS", 0)))
    return llm


def inference(event) -> Generator[str, None, None]:
    logging.info(event)
    job_input = event["input"]
    prompt: str = job_input.pop("prompt")
    stream: bool = job_input.pop("stream", True)
    llm_res: Union[str, Generator[str, None, None]] = get_llm()(prompt, stream=stream, **job_input)
    if stream:
        for res in llm_res:
            yield res
    else:
        # because this fn is always a generator, we have to yield
        yield llm_res


runpod.serverless.start({"handler": inference})
