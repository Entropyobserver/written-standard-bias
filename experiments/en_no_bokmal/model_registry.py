MODELS = {
    "nllb_600m": {
        "hf_name": "facebook/nllb-200-distilled-600M",
        "output_prefix": "p2",
    },
    "nllb_1_3b": {
        "hf_name": "facebook/nllb-200-1.3B",
        "output_prefix": "p2_robust_nllb_1_3b",
    },
    "nllb_3_3b": {
        "hf_name": "facebook/nllb-200-3.3B",
        "output_prefix": "p2_robust_nllb_3_3b",
    },
}


def get_model_spec(model_id: str) -> dict:
    if model_id not in MODELS:
        known = ", ".join(sorted(MODELS))
        raise ValueError(f"Unknown model_id={model_id!r}. Expected one of: {known}")
    return MODELS[model_id]


def apply_model_spec(cfg: dict, model_id: str) -> dict:
    spec = get_model_spec(model_id)
    cfg = dict(cfg)
    cfg["model"] = dict(cfg["model"])
    cfg["model"]["pretrained"] = spec["hf_name"]
    cfg["model"]["model_id"] = model_id
    cfg["model"]["output_prefix"] = spec["output_prefix"]
    return cfg


def output_prefix(model_id: str) -> str:
    return get_model_spec(model_id)["output_prefix"]
