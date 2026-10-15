"""
QA Dataset Sampling Tool

```
pip install pandas pyarrow
pip install openai
```

# 采样数据
python dataset/qa_dataset.py sample \
  --queries ~/dataset/mmarco-queries.parquet \
  --corpus ~/dataset/mmarco-corpus.parquet \
  --qrels ~/dataset/mmarco-qrels.parquet \
  --nq 100 \
  --output_dir ./dataset/samples

# 生成答案(基于采样结果)
# 可选：追加 --model <model-name> 指定 OpenAI 兼容服务中的模型
# 切换模型时使用新的 --output_dir；断点续跑仍会复用已有答案
python dataset/qa_dataset.py generate \
  --input_dir ./dataset/samples \
  --output_dir ./dataset/samples

# 展示结果
python dataset/qa_dataset.py show \
  --input_dir ./dataset/samples \
  -n 1
"""

import os
from pathlib import Path
import argparse

import pandas as pd
import openai


DEFAULT_QA_MODEL = "gpt-5.6-sol"


def read_parquet(path):
    return pd.read_parquet(path)


def save_to_parquet(df: pd.DataFrame, path: str):
    """将 DataFrame 保存为 Parquet 文件。"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)
    print(f"Saved to {path}")


def print_stats(df: pd.DataFrame, name: str):
    """输出 DataFrame 的记录数及唯一标识数量。"""
    print(f"\n{name} Statistics:")
    print(f"- Total records: {len(df)}")
    if "id" in df.columns:
        print(f"- Unique ids: {df['id'].nunique()}")
    if "qid" in df.columns:
        print(f"- Unique qids: {df['qid'].nunique()}")
    if "pid" in df.columns:
        print(f"- Unique pids: {df['pid'].nunique()}")


def sample_data(
    queries: pd.DataFrame, corpus: pd.DataFrame, qrels: pd.DataFrame, nq=1000
):
    """校验关联关系并从数据集中抽样。

    参数：
        queries: 查询数据，包含 id 和 text 列。
        corpus: 语料数据，包含 id 和 text 列。
        qrels: 查询与段落的多对多关联，包含 qid 和 pid 列。
        nq: 抽样查询数，默认 1000。

    返回：
        (sampled_queries, sampled_corpus, sampled_qrels) 元组。
    """
    # 1. 仅保留 queries 中存在的查询关联。
    valid_qids = set(queries["id"])
    qrels = qrels[qrels["qid"].isin(valid_qids)]

    # 2. 仅保留 corpus 中存在的段落关联。
    valid_pids = set(corpus["id"])
    qrels = qrels[qrels["pid"].isin(valid_pids)]

    # 3. 选择关联段落较多的查询进行抽样。
    # 优先选择关联 pid 最多的 qid，以覆盖更多相关段落。
    qid_counts = qrels["qid"].value_counts()
    sampled_qids = qid_counts.nlargest(min(nq, len(qid_counts))).index

    # 4. 收集抽样查询关联的全部 pid。
    sampled_qrels = qrels[qrels["qid"].isin(sampled_qids)]
    sampled_pids = set(sampled_qrels["pid"])

    # 5. 从语料中额外抽取段落作为冗余，数量为已抽样 pid 的 20%。
    extra_pids = set(corpus["id"].sample(int(0.2 * len(sampled_pids))))
    all_pids = sampled_pids.union(extra_pids)

    # 6. 构建最终的抽样数据集。
    sampled_queries = queries[queries["id"].isin(sampled_qids)]
    sampled_corpus = corpus[corpus["id"].isin(all_pids)]

    return sampled_queries, sampled_corpus, sampled_qrels


class QAAnsweringSystem:
    def __init__(
        self, queries: pd.DataFrame, corpus: pd.DataFrame, qrels: pd.DataFrame
    ):
        """使用查询、语料及关联数据初始化问答系统。

        参数：
            queries: 包含 id 和 text 的查询 DataFrame。
            corpus: 包含 id 和 text 的语料 DataFrame。
            qrels: 包含 qid 与 pid 映射的 DataFrame。
        """
        self.queries = queries
        self.corpus = corpus
        self.qrels = qrels
        self.client = openai.Client(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )

        # 构建按 ID 查找查询和语料的字典。
        self.qid_to_text = dict(zip(queries["id"], queries["text"]))
        self.pid_to_text = dict(zip(corpus["id"], corpus["text"]))
        self.qid_to_pids = qrels.groupby("qid")["pid"].apply(list).to_dict()

    def get_context_for_qid(self, qid: str) -> str:
        """按查询 ID 收集全部相关段落，并返回拼接后的上下文文本。

        参数：
            qid: 要查找的查询 ID。
        """
        if qid not in self.qid_to_pids:
            raise ValueError("Question ID not found")

        context_parts = []
        print(f"Context for Question ID {qid}: {self.qid_to_pids[qid]}")
        for pid in self.qid_to_pids[qid]:
            if pid in self.pid_to_text:
                context_parts.append(self.pid_to_text[pid])

        return "\n\n".join(context_parts)

    def answer_question(self, qid: str, model: str = DEFAULT_QA_MODEL) -> str:
        """调用 OpenAI API，依据查询对应的上下文回答问题。

        参数：
            qid: 待回答的查询 ID。
            model: 使用的模型名称。

        返回：
            大模型生成的答案。
        """
        if qid not in self.qid_to_text:
            raise ValueError("Question ID not found")

        question = self.qid_to_text[qid]
        context = self.get_context_for_qid(qid)

        if not context:
            raise ValueError("No context found for this question")

        prompt = f"""Answer the question based on the context below. Keep the answer concise.

Question: {question}

Context: {context}

Answer:"""
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        if not response.choices or response.choices[0].message is None:
            raise ValueError("LLM returned empty or filtered response")
        return response.choices[0].message.content


def sample_command(args):
    """处理 sample 子命令。"""
    # 加载数据。
    print("Loading data...")
    queries = read_parquet(args.queries)
    corpus = read_parquet(args.corpus)
    qrels = read_parquet(args.qrels)

    # 输出原始数据统计。
    print("\nOriginal Dataset Statistics:")
    print_stats(queries, "Queries")
    print_stats(corpus, "Corpus")
    print_stats(qrels, "Qrels")

    # 执行数据抽样。
    print(f"\nSampling {args.nq} queries...")
    sampled_queries, sampled_corpus, sampled_qrels = sample_data(
        queries, corpus, qrels, args.nq
    )

    # 输出抽样结果统计。
    print("\nSampled Dataset Statistics:")
    print_stats(sampled_queries, "Sampled Queries")
    print_stats(sampled_corpus, "Sampled Corpus")
    print_stats(sampled_qrels, "Sampled Qrels")

    # 保存抽样数据。
    print("\nSaving sampled data...")
    save_to_parquet(sampled_queries, f"{args.output_dir}/queries.parquet")
    save_to_parquet(sampled_corpus, f"{args.output_dir}/corpus.parquet")
    save_to_parquet(sampled_qrels, f"{args.output_dir}/qrels.parquet")
    print("\nSampling completed successfully!")


def generate_answers(
    input_dir: str,
    output_dir: str,
    max_retries: int = 3,
    *,
    model: str = DEFAULT_QA_MODEL,
):
    """为抽样查询生成答案，支持断点续跑。

    即使更换模型也会复用已保存的答案；如需全部重新生成，请使用新的输出目录。

    参数：
        input_dir: 存放抽样 queries、corpus 和 qrels 的目录。
        output_dir: 答案文件的输出目录。
        max_retries: 失败查询的最大重试次数。
        model: 用于生成答案的 OpenAI 兼容模型。
    """
    print("\nLoading sampled data...")
    queries = read_parquet(f"{input_dir}/queries.parquet")
    corpus = read_parquet(f"{input_dir}/corpus.parquet")
    qrels = read_parquet(f"{input_dir}/qrels.parquet")

    # 尝试加载已有答案，以便断点续跑。
    answers_path = f"{output_dir}/answers.parquet"
    qa_pairs_path = f"{output_dir}/qas.parquet"

    try:
        existing_answers = read_parquet(answers_path)
        existing_qas = read_parquet(qa_pairs_path)
        processed_qids = set(existing_qas["qid"])
        print(f"\nFound {len(processed_qids)} previously processed queries")
    except (FileNotFoundError, KeyError):
        print("No existing answers found, use empty state")
        existing_answers = pd.DataFrame(columns=["id", "text"])
        existing_qas = pd.DataFrame(columns=["qid", "aid"])
        processed_qids = set()

    qa_system = QAAnsweringSystem(queries, corpus, qrels)

    answers = existing_answers.to_dict("records")
    qa_pairs = existing_qas.to_dict("records")
    answer_id_counter = len(answers) + 1

    for qid in queries["id"]:
        if qid in processed_qids:
            continue

        retry_count = 0
        while retry_count <= max_retries:
            try:
                answer_text = qa_system.answer_question(qid, model=model)
                aid = answer_id_counter
                answers.append({"id": aid, "text": answer_text})
                qa_pairs.append({"qid": qid, "aid": aid})
                answer_id_counter += 1

                # 每成功生成一个答案就保存进度。
                save_to_parquet(pd.DataFrame(answers), answers_path)
                save_to_parquet(pd.DataFrame(qa_pairs), qa_pairs_path)
                print(f"Processed qid: {qid}")
                break
            except (openai.APIError, openai.APIConnectionError) as e:
                retry_count += 1
                if retry_count > max_retries:
                    print(
                        f"\nFailed to process qid {qid} after {max_retries} attempts: {str(e)}"
                    )
                    # 保存失败状态。
                    save_to_parquet(pd.DataFrame(answers), answers_path)
                    save_to_parquet(pd.DataFrame(qa_pairs), qa_pairs_path)
                else:
                    print(f"\nRetry {retry_count} for qid {qid}...")

    print("\nAnswer generation completed!")
    print(f"Total queries: {len(queries)}")
    print(f"Successfully processed: {len(qa_pairs)}")
    print(f"Failed queries: {len(queries) - len(qa_pairs)}")


def show_results(input_dir: str, n: int = 5):
    """展示 n 条问答结果，包含问题、上下文和答案。

    参数：
        input_dir: 问答数据目录。
        n: 展示数量，默认 5。
    """
    print(f"\nShowing {n} random results:")

    # 加载数据。
    queries = read_parquet(f"{input_dir}/queries.parquet")
    corpus = read_parquet(f"{input_dir}/corpus.parquet")
    qrels = read_parquet(f"{input_dir}/qrels.parquet")
    qa_pairs = read_parquet(f"{input_dir}/qas.parquet")
    answers = read_parquet(f"{input_dir}/answers.parquet")

    # 创建问答系统，用于查找查询上下文。
    qa_system = QAAnsweringSystem(queries, corpus, qrels)

    # 取前 n 条问答记录。
    for _, row in qa_pairs.sample(n).iterrows():
        qid = row["qid"]
        aid = row["aid"]

        # 获取问题。
        question = qa_system.qid_to_text[qid]

        # 获取上下文。
        context = qa_system.get_context_for_qid(qid)

        # 获取答案。
        answer = answers[answers["id"] == aid]["text"].values[0]

        print("\n" + "=" * 50)
        print(f"Question (qid={qid}):\n{question}")
        print("\nContext:")
        print(context)
        print(f"\nAnswer (aid={aid}):\n{answer}")
        print("=" * 50 + "\n")


def _model_argument(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("model must not be empty or whitespace-only")
    return value


def main():
    # 配置命令行参数。
    parser = argparse.ArgumentParser(description="QA Dataset Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 数据抽样子命令。
    sample_parser = subparsers.add_parser("sample", help="Sample dataset")
    sample_parser.add_argument(
        "--queries", type=str, required=True, help="Path to queries parquet file"
    )
    sample_parser.add_argument(
        "--corpus", type=str, required=True, help="Path to corpus parquet file"
    )
    sample_parser.add_argument(
        "--qrels", type=str, required=True, help="Path to qrels parquet file"
    )
    sample_parser.add_argument(
        "--nq", type=int, default=1000, help="Number of queries to sample"
    )
    sample_parser.add_argument(
        "--output_dir", type=str, default="./save", help="Output directory"
    )
    sample_parser.set_defaults(func=sample_command)

    # 答案生成子命令。
    generate_parser = subparsers.add_parser("generate", help="Generate answers")
    generate_parser.add_argument(
        "--input_dir", type=str, required=True, help="Directory with sampled data"
    )
    generate_parser.add_argument(
        "--output_dir", type=str, default="./save", help="Output directory"
    )
    generate_parser.add_argument(
        "--model",
        type=_model_argument,
        default=DEFAULT_QA_MODEL,
        help=(
            f"Model for answer generation (default: {DEFAULT_QA_MODEL}). "
            "Resume reuses saved answers; use a new --output_dir when changing models."
        ),
    )
    generate_parser.set_defaults(
        func=lambda args: generate_answers(
            args.input_dir, args.output_dir, model=args.model
        )
    )

    # 结果展示子命令。
    show_parser = subparsers.add_parser("show", help="Show QA results")
    show_parser.add_argument(
        "--input_dir", type=str, required=True, help="Directory with QA data"
    )
    show_parser.add_argument(
        "-n", type=int, default=5, help="Number of results to show (default: 5)"
    )
    show_parser.set_defaults(func=lambda args: show_results(args.input_dir, args.n))

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
