<!-- @zone code -->

# UIE ONNX 权重构建

> 权重文件（约 448MB）不入 git，落在 `tmp/uie/`（`.gitignore` 已含 `tmp/`）。
> 本文件记录**如何重新生成**，转换环境是一次性的，项目 `.venv` 只依赖 onnxruntime + tokenizers。

## 为什么不用 paddlenlp

`paddlenlp 2.8.1`（PyPI 最新、已停更）在 Python 3.12 上装得上但导不进去：

1. `ImportError: cannot import name 'repo_type_and_id_from_hf_id' from 'huggingface_hub'`
2. `ImportError: cannot import name 'download' from 'aistudio_sdk.hub'`
3. `ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4`（paddlenlp 钉 numpy<2，pyarrow 要 2.0，互斥）

## 转换步骤（一次性，需联网）

```sh
# 1. 干净环境：不装 paddle，否则 convert.py 会走已移除的 paddle.fluid.dygraph
python3 -m venv /tmp/uieconv
/tmp/uieconv/bin/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
/tmp/uieconv/bin/python -m pip install 'transformers<5' onnx onnxruntime numpy colorlog colorama requests onnxscript

# 2. 取移植仓库（PaddleNLP UIE 的 PyTorch 版）
git clone --depth 1 https://github.com/LouisZango/uie_pytorch /tmp/uie_pt

# 3. 打补丁：transformers 4.57 把两个函数挪到了 pytorch_utils
#    ernie.py 与 ernie_m.py 各改一处 import

# 4. 转换权重（--no_validate_output 跳过需要 paddlenlp 的校验）
cd /tmp/uie_pt && /tmp/uieconv/bin/python convert.py --no_validate_output
```

## 导出 ONNX：必须关掉 dynamo 导出器

```python
torch.onnx.export(model, (inputs,), save_path,
                  opset_version=11, dynamo=False)   # 关键
```

**torch 2.14 默认走 dynamo 导出器，对这份 2022 年的 UIE 代码导出结果是错的**：
同一组输入，PyTorch 输出 `start_prob` 峰值 0.270，dynamo 版 ONNX 只有 0.0007。
加上 `dynamo=False` 后，最大绝对差降到 **1.3e-6**。

## 本项目的推理约定

- 分词用 `tokenizers` 直接构造 WordPiece + `BertNormalizer`，**不依赖 transformers**
- 特殊 token id 必须从词表取：`[CLS]=1`、`[SEP]=2`（不是 0）
- `token_type_ids` 必须区分句 A（prompt）与句 B（正文），全 0 会让概率归零
- 只有 fast tokenizer 能给出 `offset_mapping`，纯 Python 实现会抛 `NotImplementedError`

<!-- /@zone code -->
