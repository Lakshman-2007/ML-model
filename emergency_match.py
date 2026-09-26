import csv
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset" / "test"
OUT = ROOT / "output"
WORK = ROOT / "work"
DB = WORK / "emergency.sqlite"

OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)


def norm(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_index(file_path, table):
    print(f"Building index for {file_path.name}...")

    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")

    con.execute(f"DROP TABLE IF EXISTS {table}")

    con.execute(f"""
        CREATE TABLE {table} (
            entity_id TEXT PRIMARY KEY,
            country TEXT,
            norm_name TEXT
        )
    """)

    con.execute(
        f"CREATE INDEX {table}_idx "
        f"ON {table}(country, norm_name)"
    )

    with open(
        file_path,
        "r",
        encoding="utf-8",
        newline=""
    ) as f:

        reader = csv.DictReader(f, delimiter="\t")

        batch = []

        for row in reader:

            batch.append(
                (
                    row["entity_id"],
                    row["country"],
                    norm(row["business_name"])
                )
            )

            if len(batch) >= 50000:

                con.executemany(
                    f"INSERT INTO {table} VALUES (?, ?, ?)",
                    batch
                )

                con.commit()
                batch = []

        if batch:

            con.executemany(
                f"INSERT INTO {table} VALUES (?, ?, ?)",
                batch
            )

            con.commit()

    con.close()

    print(f"Finished {table}")


def generate_results():

    print("\nGenerating matching_results.tsv...")

    con = sqlite3.connect(DB)

    source1 = DATA / "test_source1.tsv"

    result_file = OUT / "matching_results.tsv"
    candidate_file = OUT / "candidate_pairs.tsv"

    with open(
        source1,
        "r",
        encoding="utf-8",
        newline=""
    ) as f, \
    open(
        result_file,
        "w",
        encoding="utf-8",
        newline=""
    ) as result_out, \
    open(
        candidate_file,
        "w",
        encoding="utf-8",
        newline=""
    ) as candidate_out:

        reader = csv.DictReader(
            f,
            delimiter="\t"
        )

        result_writer = csv.DictWriter(
            result_out,
            fieldnames=[
                "source1_entity_id",
                "matched_entity_ids"
            ],
            delimiter="\t"
        )

        candidate_writer = csv.DictWriter(
            candidate_out,
            fieldnames=[
                "source1_entity_id",
                "candidate_entity_ids"
            ],
            delimiter="\t"
        )

        result_writer.writeheader()
        candidate_writer.writeheader()

        for count, row in enumerate(reader, 1):

            entity_id = row["entity_id"]
            country = row["country"]
            business_name = norm(row["business_name"])

            matches = []

            for table in ["s2", "s3"]:

                query = f"""
                    SELECT entity_id
                    FROM {table}
                    WHERE country = ?
                    AND norm_name = ?
                    LIMIT 100
                """

                rows = con.execute(
                    query,
                    (country, business_name)
                ).fetchall()

                matches.extend(
                    x[0] for x in rows
                )

            matches = sorted(set(matches))

            result_writer.writerow({
                "source1_entity_id": entity_id,
                "matched_entity_ids": ",".join(matches)
            })

            candidate_writer.writerow({
                "source1_entity_id": entity_id,
                "candidate_entity_ids": ",".join(matches)
            })

            if count % 100000 == 0:

                print(
                    f"Processed {count:,} Source-1 records"
                )

    con.close()

    print("\nFinished!")
    print("Result:", result_file)
    print("Candidates:", candidate_file)


if __name__ == "__main__":

    print("=" * 60)
    print("EMERGENCY AMAZON ML CHALLENGE PIPELINE")
    print("=" * 60)

    build_index(
        DATA / "test_source2.tsv",
        "s2"
    )

    build_index(
        DATA / "test_source3.tsv",
        "s3"
    )

    generate_results()