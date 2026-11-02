"""
make_sample_data.py

Turns a real survey export into a shareable sample file with the same shape.

    python tools/make_sample_data.py <real_export.xlsx> <sample_output.xlsx> [--seed N]

What it does
  - identity columns (names, emails, phones, job titles, company names, IDs,
    session keys) are REPLACED with made-up values
  - company and subject-company codes are REMAPPED to fake codes, consistently
    everywhere they appear (cell values and column headers), so grouping still works
  - open-ended comments are replaced with placeholder text
  - every other answer column is SHUFFLED across respondents, so the file keeps
    realistic values and blanks, but no row is any real person's answers
  - only the first sheet is kept (the Datamap sheet links codes to real brand names)

The output has the same columns, in the same order, with the same header
patterns, so the same reformadder config runs on it unchanged.
"""
import argparse
import random
import re
import string

from openpyxl import Workbook, load_workbook

# ---------------------------------------------------------------- fake value pools
FIRST_NAMES = ["Lucia", "Mateo", "Sofia", "Hugo", "Martina", "Pablo", "Julia",
               "Daniel", "Paula", "Alvaro", "Elena", "Diego", "Carmen", "Javier",
               "Laura", "Marcos", "Irene", "Adrian", "Nora", "Sergio"]
LAST_NAMES = ["Garcia", "Lopez", "Moreno", "Navarro", "Romero", "Torres", "Ruiz",
              "Vidal", "Castro", "Ortega", "Molina", "Serrano", "Blanco", "Gil",
              "Rubio", "Marin", "Iglesias", "Cano", "Prieto", "Herrera"]
JOB_TITLES = ["Buyer", "Senior Buyer", "Category Manager", "Marketing Manager",
              "Trade Marketing Lead", "Brand Partnerships Manager", "Purchasing Director",
              "E-commerce Manager"]

# ---------------------------------------------------------------- column roles
# column header -> how it is handled. Anything not listed is shuffled.
KEEP = {"record", "date", "start_date", "markers", "status", "dQ1r2", "dQ1r8",
        "dQ1r9", "dQ1r10", "decLang", "dcua"}
COMPANY_NAME_COLS = {"dQ1r1", "dQ1r6"}
COMPANY_EMAIL_COLS = {"dQ1r3"}
COMPANY_CODE_COLS = {"dQ1r7", "Q1a"}
CASE_ID_COLS = {"CaseID", "userid"}
RANDOM_KEY_COLS = {"uuid", "session"}
FIRST_NAME, LAST_NAME, EMAIL, PHONE, JOB_TITLE = "Q1r1", "Q1r2", "Q1r3", "Q1r4", "Q1r5"
COMMENT_PREFIXES = ("Q8x", "Q8_", "Q9a")
GENERIC_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Sample/1.0"

SUBJECT_CODE = re.compile(r"R\d{2,}")  # e.g. R16829 in dAllRatings_R16829r1022


def random_key(rng: random.Random, length: int = 16) -> str:
    return "".join(rng.choices(string.ascii_lowercase + string.digits, k=length))


def build_mapping(values, make_new) -> dict:
    """map each distinct original value to a new one, in first-seen order"""
    mapping = {}
    for value in values:
        if value is not None and value not in mapping:
            mapping[value] = make_new(len(mapping))
    return mapping


def anonymize(rows: list[list], rng: random.Random) -> list[list]:
    header, data = list(rows[0]), [list(r) for r in rows[1:]]
    col = {name: i for i, name in enumerate(header)}
    column = lambda name: [r[col[name]] for r in data]

    # ---- consistent fake codes / names for the respondent companies
    company_codes = build_mapping(column("dQ1r7") + column("Q1a"), lambda n: 90001 + n)
    company_names = build_mapping(column("dQ1r1") + column("dQ1r6"),
                                  lambda n: f"Retailer {string.ascii_uppercase[n]}")
    case_ids = build_mapping(column("CaseID") + column("userid"),
                             lambda n: f"SAMPLE25_{n + 1:04d}")

    # ---- consistent fake subject-company codes in the HEADERS
    subject_codes = build_mapping(
        [code for h in header for code in SUBJECT_CODE.findall(str(h))],
        lambda n: f"R{60001 + n}")
    new_header = [SUBJECT_CODE.sub(lambda m: subject_codes[m.group()], str(h)) for h in header]

    # ---- shuffle every answer column independently across respondents
    handled = (KEEP | COMPANY_NAME_COLS | COMPANY_EMAIL_COLS | COMPANY_CODE_COLS | CASE_ID_COLS
               | RANDOM_KEY_COLS | {FIRST_NAME, LAST_NAME, EMAIL, PHONE, JOB_TITLE, "url", "userAgent"})
    for name, i in col.items():
        if name in handled or str(name).startswith(COMMENT_PREFIXES):
            continue
        values = [r[i] for r in data]
        rng.shuffle(values)
        for r, v in zip(data, values):
            r[i] = v

    # ---- replace identity fields row by row
    used_names = set()
    for r in data:
        while True:
            first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            if (first, last) not in used_names:
                used_names.add((first, last))
                break
        company = company_names.get(r[col["dQ1r1"]], "Retailer")
        domain = company.lower().replace(" ", "-") + ".example"

        r[col[FIRST_NAME]] = first
        r[col[LAST_NAME]] = last
        r[col[EMAIL]] = f"{first.lower()}.{last.lower()}@{domain}"
        r[col[PHONE]] = f"600{rng.randrange(1_000_000):06d}"
        r[col[JOB_TITLE]] = rng.choice(JOB_TITLES)

        for name in COMPANY_NAME_COLS:
            r[col[name]] = company_names.get(r[col[name]], r[col[name]])
        for name in COMPANY_EMAIL_COLS:
            r[col[name]] = f"{company.replace(' ', '')}@openlink.example"
        for name in COMPANY_CODE_COLS:
            r[col[name]] = company_codes.get(r[col[name]], r[col[name]])

        old_case = r[col["CaseID"]]
        for name in CASE_ID_COLS:
            r[col[name]] = case_ids.get(r[col[name]], r[col[name]])
        if r[col["url"]] is not None and old_case is not None:
            r[col["url"]] = str(r[col["url"]]).replace(str(old_case), case_ids[old_case])

        for name in RANDOM_KEY_COLS:
            r[col[name]] = random_key(rng)
        if r[col["userAgent"]] is not None:
            r[col["userAgent"]] = GENERIC_USER_AGENT

        for name, i in col.items():  # open-ended comments
            if str(name).startswith(COMMENT_PREFIXES) and isinstance(r[i], str):
                r[i] = "Sample open-ended comment."

    return [new_header] + data


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--seed", type=int, default=250408)
    args = parser.parse_args()

    sheet = load_workbook(args.source, read_only=True).worksheets[0]
    rows = [list(r) for r in sheet.iter_rows(values_only=True)]
    sample = anonymize(rows, random.Random(args.seed))

    wb = Workbook(write_only=True)
    ws = wb.create_sheet("A1")
    for row in sample:
        ws.append(row)
    wb.properties.creator = "make_sample_data.py"
    wb.save(args.output)
    print(f"Wrote {len(sample) - 1} anonymized rows x {len(sample[0])} columns to {args.output}")


if __name__ == "__main__":
    main()
