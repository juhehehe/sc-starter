"""Teach a small language model which ministry a parliamentary question goes to.

Usage: python run.py [SAMPLE]
Reads data/questions.csv.gz, trains on 80% of the questions, tests on 10%
it never saw, and writes to results/ (with SAMPLE, such as 400, only that
many questions, for a quick test on your computer):
  scores.txt       accuracy before training, with only the new top layer
                   trained and with the whole model trained; F1 and the
                   table of ministries against predictions
  predictions.csv  each test question with its ministry and the predicted one
  model/           the trained model, to load with transformers
"""

import csv
import gzip
import os
import sys
from collections import Counter
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    set_seed,
)

DATA = Path("data/questions.csv.gz")
RESULTS = Path("results")
# A small English language model; setup.slurm downloads it.
MODEL = "distilbert/distilbert-base-uncased"
# How often the model goes through all training questions.
EPOCHS = 3
SEED = 1


def read_questions(path):
    """Return one dict per question, with its ministry and its text."""
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def check_gpu():
    """Stop if Slurm gave this job a GPU that PyTorch cannot use.

    Otherwise the model would quietly train on the CPU, slowly, while the
    booked GPU sits idle.
    """
    if os.environ.get("SLURM_GPUS_ON_NODE") and not torch.cuda.is_available():
        sys.exit("This job has a GPU, but PyTorch cannot use it. See README.md.")


def split(questions):
    """80% to train on, 10% to check after each epoch, 10% for the final test.

    Stratified, so each part has the same share of each ministry; the seed
    makes the split the same in every run.
    """
    ministries = [question["ministry"] for question in questions]
    train, rest = train_test_split(
        questions, test_size=0.2, stratify=ministries, random_state=SEED
    )
    ministries = [question["ministry"] for question in rest]
    check, test = train_test_split(
        rest, test_size=0.5, stratify=ministries, random_state=SEED
    )
    return train, check, test


def encode(questions, tokenizer, label_of):
    """Turn questions into the numbers the model reads, with their answer.

    No padding here: the Trainer pads each batch to its longest question.
    """
    tokens = tokenizer(
        [question["question"] for question in questions], truncation=True
    )
    return [
        {
            "input_ids": tokens["input_ids"][i],
            "attention_mask": tokens["attention_mask"][i],
            "labels": label_of[question["ministry"]],
        }
        for i, question in enumerate(questions)
    ]


def accuracy(prediction):
    """Return the share of questions put to the right ministry, after each epoch."""
    return {
        "accuracy": accuracy_score(
            prediction.label_ids, prediction.predictions.argmax(axis=1)
        )
    }


def table(truth, predicted, names):
    """Return the ministries (rows) against the predictions (columns), as text.

    The columns are numbered in the order of the rows, so correct
    predictions read as a diagonal, as in python-embeddings.
    """
    count = Counter(zip(truth, predicted, strict=True))
    numbers = range(1, len(names) + 1)
    lines = [f"{'':<15}" + "".join(f"{n:>6}" for n in numbers)]
    for name in names:
        lines.append(
            f"{name:<15}" + "".join(f"{count[name, other]:>6}" for other in names)
        )
    lines += [
        "",
        "Columns: " + ", ".join(f"{n} {name}" for n, name in enumerate(names, 1)),
    ]
    return lines


def make_model(names, label_of):
    """Load the pre-trained model with a new layer on top that picks a ministry.

    The new layer starts from random numbers; setting the seed here makes
    them the same each time, so every variant starts from the same model.
    """
    set_seed(SEED)
    return AutoModelForSequenceClassification.from_pretrained(
        MODEL,
        num_labels=len(names),
        id2label=dict(enumerate(names)),
        label2id=label_of,
    )


def settings(learning_rate):
    """Return how to train: the same for both versions but the learning rate."""
    return TrainingArguments(
        output_dir=str(RESULTS),
        num_train_epochs=EPOCHS,
        learning_rate=learning_rate,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=64,
        weight_decay=0.01,
        eval_strategy="epoch",
        # Training takes under a minute, so no checkpoints along the way;
        # python-long-run shows how to plan runs that take longer.
        save_strategy="no",
        logging_steps=100,
        # Mixed precision where the GPU supports it: faster, nearly the same results.
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        # The GPU if there is one, else the CPU: the same on every computer,
        # also on Macs, whose own GPU the Trainer would otherwise pick.
        use_cpu=not torch.cuda.is_available(),
        # Progress bars would fill the Slurm output file.
        disable_tqdm=True,
        report_to="none",
        seed=SEED,
    )


def guesses(trainer, test_set, names):
    """Return the ministry that the model picks for each test question."""
    prediction = trainer.predict(test_set)
    return [names[i] for i in prediction.predictions.argmax(axis=1)]


def main():
    """Train and test both versions of the model, and write the results."""
    check_gpu()
    # PyTorch would start a thread for every core of the node; as many as
    # job.slurm booked, so they do not crowd onto the booked cores.
    if "SLURM_CPUS_PER_TASK" in os.environ:
        torch.set_num_threads(int(os.environ["SLURM_CPUS_PER_TASK"]))

    questions = read_questions(DATA)
    # A sample with the same share from each ministry, for a quick test.
    if len(sys.argv) > 1:
        questions, _ = train_test_split(
            questions,
            train_size=int(sys.argv[1]),
            stratify=[question["ministry"] for question in questions],
            random_state=SEED,
        )
    # The ministries in order, each with a number, as the model needs.
    names = sorted({question["ministry"] for question in questions})
    label_of = {name: i for i, name in enumerate(names)}
    train, check, test = split(questions)
    truth = [question["ministry"] for question in test]

    # The three parts, turned into the numbers that the model reads.
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    train_set = encode(train, tokenizer, label_of)
    check_set = encode(check, tokenizer, label_of)
    test_set = encode(test, tokenizer, label_of)

    # The whole model learns: the new layer and the pre-trained model below
    # it. Learning rate, batch size and weight decay as in the Hugging Face
    # guide to text classification with this model.
    trainer = Trainer(
        model=make_model(names, label_of),
        args=settings(learning_rate=2e-5),
        train_dataset=train_set,
        eval_dataset=check_set,
        processing_class=tokenizer,
        compute_metrics=accuracy,
    )
    # The same model before any training, for comparison.
    before = accuracy_score(truth, guesses(trainer, test_set, names))
    print("Training the whole model.")
    output = trainer.train()
    print(f"Trained in {output.metrics['train_runtime']:.0f} seconds.")
    predicted = guesses(trainer, test_set, names)

    # For comparison: only the new layer learns, the pre-trained model below
    # it stays as it is. Its larger learning rate is a choice: a new layer
    # alone hardly moves in three epochs with the small steps that suit the
    # whole model, and the comparison would be unfair.
    model = make_model(names, label_of)
    for parameter in model.base_model.parameters():
        parameter.requires_grad = False
    top_trainer = Trainer(
        model=model,
        args=settings(learning_rate=1e-3),
        train_dataset=train_set,
        eval_dataset=check_set,
        processing_class=tokenizer,
        compute_metrics=accuracy,
    )
    print("Training only the new top layer.")
    output = top_trainer.train()
    print(f"Trained in {output.metrics['train_runtime']:.0f} seconds.")
    top_only = accuracy_score(truth, guesses(top_trainer, test_set, names))

    # The trained model, and each test question with the predicted ministry.
    RESULTS.mkdir(exist_ok=True)
    trainer.save_model(str(RESULTS / "model"))
    # UTF-8: a few questions hold letters that Windows' own encoding
    # cannot write.
    with open(RESULTS / "predictions.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "ministry", "predicted", "heading", "question"])
        for question, guess in zip(test, predicted, strict=True):
            writer.writerow(
                [
                    question["id"],
                    question["ministry"],
                    guess,
                    question["heading"],
                    question["question"],
                ]
            )

    # The scores and the table, into scores.txt and onto the screen.
    lines = [
        f"{MODEL}, trained {EPOCHS} epochs on {len(train):,} questions; "
        f"tested on {len(test):,} questions it never saw.",
        "",
        "Accuracy, the share put to the right ministry:",
        f"  before training                  {before:.2f}",
        f"  only the new top layer trained   {top_only:.2f}",
        f"  whole model trained              {accuracy_score(truth, predicted):.2f}",
        "",
        "The whole model trained:",
        "",
        f"Macro F1: {f1_score(truth, predicted, average='macro'):.2f}   "
        "(0 to 1, each ministry counts the same)",
        "",
        "Questions of each ministry (rows) by predicted ministry (columns):",
        "",
        *table(truth, predicted, names),
    ]
    report = "\n".join(lines)
    (RESULTS / "scores.txt").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
