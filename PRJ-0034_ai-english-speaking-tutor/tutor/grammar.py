"""자주 하는 영어 실수를 규칙으로 찾는 간이 교정기(AI 아님). 확실한 것만 지적하고, 문장을 몽땅 고쳐 쓰지는 않는다."""
import re

THIRD = {"go": "goes", "have": "has", "do": "does", "like": "likes", "want": "wants", "need": "needs", "make": "makes", "take": "takes",
         "eat": "eats", "play": "plays", "work": "works", "live": "lives", "study": "studies", "watch": "watches", "love": "loves", "know": "knows"}
AN_EXC = {"hour", "honest", "honor", "heir"}                 # 모음 소리로 시작하는 h 단어
A_EXC = {"university", "unique", "uniform", "union", "one", "user", "european", "useful", "usual"}   # 자음 소리로 시작하는 모음 글자 단어


def check(text):
    out = []
    def add(rule, found, fix, ko): out.append({"rule": rule, "found": found, "suggest": fix, "ko": ko})
    for m in re.finditer(r"\b(he|she|it)\s+(" + "|".join(THIRD) + r")\b", text, re.I):
        add("3인칭 단수", m.group(0), f"{m.group(1)} {THIRD[m.group(2).lower()]}", "he/she/it 뒤의 동사에는 -s/-es가 붙어요.")
    for m in re.finditer(r"\b(I|you|we|they)\s+(is)\b", text, re.I):
        add("be동사", m.group(0), f"{m.group(1)} {'am' if m.group(1).lower() == 'i' else 'are'}", "주어에 맞는 be동사를 써요 (I am / you·we·they are).")
    for m in re.finditer(r"\b(he|she|it)\s+(are|am)\b", text, re.I):
        add("be동사", m.group(0), f"{m.group(1)} is", "he/she/it 뒤에는 is를 써요.")
    for m in re.finditer(r"\b(a|an)\s+([A-Za-z]+)", text, re.I):
        art, w = m.group(1).lower(), m.group(2).lower()
        vowel = (w[0] in "aeiou" and w not in A_EXC) or w in AN_EXC
        if art == "a" and vowel: add("관사", m.group(0), f"an {m.group(2)}", "모음 소리로 시작하면 an을 써요.")
        if art == "an" and not vowel: add("관사", m.group(0), f"a {m.group(2)}", "자음 소리로 시작하면 a를 써요.")
    for m in re.finditer(r"\bmore\s+(better|easier|bigger|faster)\b", text, re.I):
        add("비교급", m.group(0), m.group(1), "이미 비교급인 단어 앞에 more를 또 붙이지 않아요.")
    for m in re.finditer(r"(?<![A-Za-z'])i(?![A-Za-z'])", text):
        add("대문자 I", "i", "I", "'나'를 뜻하는 I는 항상 대문자예요.")
    if text.strip() and text.strip()[0].islower() and not re.match(r"\s*i\b", text): add("문장 시작", text.strip()[:12], text.strip()[0].upper() + text.strip()[1:12], "문장은 대문자로 시작해요.")
    if text.strip() and text.strip()[-1] not in ".?!": add("문장 끝", text.strip()[-10:], text.strip()[-10:] + ".", "문장 끝에 마침표·물음표를 붙여요.")
    if re.search(r"  +", text): add("공백", "두 칸 공백", "한 칸", "단어 사이는 한 칸만 띄워요.")
    return out
