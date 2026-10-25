"""문제지·정답지 HTML. 모든 글자는 이스케이프한다(문제은행에 태그가 들어 있어도 실행되지 않음). 보기 순서는 seed로 섞는다."""
import html
import random


def shuffle_choices(q, seed):
    order = list(range(len(q["choices"]))); random.Random(f"{seed}-{q['id']}").shuffle(order)
    return dict(q, choices=[q["choices"][i] for i in order], answer=order.index(q["answer"]))


def page(title, body):
    return f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title><body style='font-family:sans-serif;max-width:720px;margin:auto;padding:16px'><h1>{html.escape(title)}</h1>{body}</body>"


def worksheet(quiz, title="맞춤 문제지"):
    out = []
    for i, q in enumerate(quiz, 1):
        opts = "".join(f"<li>{html.escape(str(c))}</li>" for c in q["choices"])
        out.append(f"<p><b>{i}. {html.escape(q['q'])}</b></p><ol type='A'>{opts}</ol>")
    return page(title, "".join(out))


def answer_sheet(quiz, title="정답과 해설"):
    out = [f"<p><b>{i}.</b> 정답 {'ABCDEFGH'[q['answer']]} ({html.escape(str(q['choices'][q['answer']]))}) — {html.escape(q['explanation'])}</p>" for i, q in enumerate(quiz, 1)]
    return page(title, "".join(out))
