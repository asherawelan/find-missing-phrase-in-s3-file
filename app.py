# -*- coding: utf-8 -*-

from dotenv import load_dotenv
from alive_progress import alive_bar
from itertools import islice
from io import BytesIO
from html import escape
import os
import shutil
import sys
import boto3
import csv
import re
import atexit
import pandas as pd

load_dotenv()

csv_file = os.getenv("CSV_FILE")
bucket = os.getenv("BUCKET")

s3 = boto3.client("s3",
                  aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                  aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                  region_name=os.getenv("REGION_NAME")
                  )


class AlreadyCheckedException(Exception):
    """ Already Checked Exception """


class MissingMustPhraseException(Exception):
    """ Missing Must Phrase Exception """


class WhenPhraseDoesNotExistException(Exception):
    """ When Phrase Does Not Exist Exception """


def make_df_from_csv_file(filename):
    # Load the dataframe from the CSV
    df = pd.read_csv(filename, keep_default_na=False)
    # Add a few extra columns to the dataframe
    for column in ["checked", "correct"]:
        if not column in df:
            df.insert(column=column,
                      loc=len(df.columns),
                      value=False)

    return df


def update_csv_file(df, filename):
    print(f"Updating {filename}")
    df.to_csv(filename, index=False)


def save_local_file(content, filename):
    print(f"Saving {filename}")
    with open(filename, "wb") as file:
        file.write(content)


def get_remote_file(filename):
    f = BytesIO()
    s3.download_fileobj(bucket, filename, f)

    return f.getvalue()


def phrase_exists(content, phrase):
    return bytes(phrase, encoding="utf-8") in content


def main():
    # Create required directories
    if not os.path.exists("html"):
        os.makedirs("html")

    # Load the CSV into a dataframe
    df = make_df_from_csv_file(csv_file)

    try:
        expected_cols = ["filename", "when_phrase", "must_phrase", "checked", "correct"]
        if not set(expected_cols).issubset(df.columns):
            raise Exception('Missing some columns in CSV')

        with alive_bar(len(df.index)) as bar:
            # Iterate over every line of the CSV
            for index, row in df.iterrows():
                try:
                    # If this row is already checked, raise
                    if row["checked"]:
                        raise AlreadyCheckedException

                    # If there is no must_phrase, raise
                    if not row["must_phrase"]:
                        raise MissingMustPhraseException

                    # Get the content of the remote file
                    content = get_remote_file(
                        filename=row["filename"]
                    )

                    # If there is a where_phrase, check this first, if it does
                    # not exist, raise
                    if row["when_phrase"] and not phrase_exists(content, row["when_phrase"]):
                        raise WhenPhraseDoesNotExistException

                    # Check the must_phrase exists - if so mark as correct
                    if phrase_exists(content, row["must_phrase"]):
                        df.at[index, "correct"] = True
                    else:
                        # If the must_phrase not exist, then save the file
                        # for inspection
                        save_local_file(content, f"html/{row['filename']}")

                except (AlreadyCheckedException, WhenPhraseDoesNotExistException):
                    pass

                except MissingMustPhraseException:
                    print("Can not check content - missing must phrase")
                    continue

                except Exception as e:
                    print(e)

                row["checked"] = df.at[index, "checked"] = True
                bar()

                # After so many iterations, update the file
                if index % 1000 == 0:
                    update_csv_file(df, csv_file)

    except KeyboardInterrupt:
        pass

    finally:
        # Update the process file
        update_csv_file(df, csv_file)


@atexit.register
def exit_handler():
    print("Exiting")


if __name__ == "__main__":
    main()
