!pip install pymupdf

import os
import re
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import numpy as np
import fitz  # PyMuPDF
import nltk
from enum import unique
nltk.download('punkt')

import warnings
warnings.filterwarnings("ignore")


positivity_henry = [] #fill with Henry pos words

negativity_henry = [] #fill with Henry neg words


file_path = #select file path for L&M word list

df = pd.read_csv(file_path)

df = df.dropna(subset=["Word"])
df["Word"] = df["Word"].astype(str)
df["Word"] = df["Word"].str.lower()

print(df.head())

loughran_dict = {}

for index, row in df.iterrows():
    word = row['Word']


    # Spara hela raden som dictionary
    loughran_dict[word] = row.to_dict()

# Skapa listor för varje kategori
positive_words = []
negative_words = []
uncertainty_words = []
litigious_words = []
strong_modal_words = []
weak_modal_words = []
constraining_words = []
complexity_words = []


for word, info in loughran_dict.items():
    if info.get("Positive", 0) > 0:
        positive_words.append(word)
    if info.get("Negative", 0) > 0:
        negative_words.append(word)
    if info.get("Uncertainty", 0) > 0:
        uncertainty_words.append(word)
    if info.get("Litigious", 0) > 0:
        litigious_words.append(word)
    if info.get("Strong_Modal", 0) > 0:
        strong_modal_words.append(word)
    if info.get("Weak_Modal", 0) > 0:
        weak_modal_words.append(word)
    if info.get("Constraining", 0) > 0:
        constraining_words.append(word)
    if info.get("Complexity", 0) > 0:
        complexity_words.append(word)


print(f"Positive: {len(positive_words)} ord")
print(f"Negative: {len(negative_words)} ord")
print(f"Uncertainty: {len(uncertainty_words)} ord")
print(f"Litigious: {len(litigious_words)} ord")
print(f"Strong_Modal: {len(strong_modal_words)} ord")
print(f"Weak_Modal: {len(weak_modal_words)} ord")
print(f"Constraining: {len(constraining_words)} ord")
print(f"Complexity: {len(complexity_words)} ord")


print(df["Word"].isna().sum())

print(df[df["Word"].isna()].head())




#functions

def extract_text_pdf(pdf_path):

    print(f"Read file (text mode): {pdf_path}")

    doc = fitz.open(pdf_path)
    full_text = ""

    for i, page in enumerate(doc, start=1):

        page_text = page.get_text()

        full_text += page_text + "\n\n"

        print(f"Page {i} text extracted")

    full_text = full_text.lower()
    full_text = re.sub(r"[^\w\s]", " ", full_text)
    full_text = re.sub(r"\s+", " ", full_text)
    #print(full_text)

    return full_text




def create_df(folder_path):
    data = []

    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):

            pdf_path = os.path.join(folder_path, file)

            text = extract_text_pdf(pdf_path)


            name = file.replace(".pdf", "")
            company, year = name.rsplit("_", 1)


            tokens = text.split()
            tokens = [t for t in tokens if t] #remove empty strings if any
            length = len(tokens)
            unique_tokens = len(set(tokens))


            data.append({
                "company": company,
                "year": int(year),
                "tokens": tokens,
                "length": length,
                "unique_tokens": unique_tokens
            })

    return pd.DataFrame(data)



def compute_dfi(docs):
    dfi = defaultdict(int)

    for _, row in docs.iterrows():
        tokens = set(row["tokens"])  #unikue words per CEO letter

        for word in tokens:
            dfi[word] += 1

    return dfi



def compute_tf(docs, positive_words, negative_words):
    results = []

    listed_words = set(positive_words + negative_words)

    for _, row in docs.iterrows():
        tokens = row["tokens"]

        tf = Counter(tokens)
        counts = {w: tf[w] for w in listed_words}

        row_data = {
            "company": row["company"],
            "year": row["year"],
            "tokens": tokens,
            "length": row["length"],
            "unique_tokens": row["unique_tokens"],
            #"loughran_tf": counts
            "tf": counts
        }

        results.append(row_data)

    return pd.DataFrame(results)



def compute_weights(df, df_i, N):
    results = []

    for _, row in df.iterrows():


        #tf_dict = row.loughran_tf
        tf_dict = row.tf
        length = row.length
        unique_tokens = row.unique_tokens

        #compute a_j
        a_j = length /unique_tokens

        #unigue = row.length

        weights = {}

        for word, tf_ij in tf_dict.items():

            if tf_ij > 0:
              weights[word] = ((1 + math.log2(tf_ij)) / (1 + math.log2(a_j))) * math.log2(N / df_i[word])
            else:
              weights[word] = 0

        row_data = {
            "company": row["company"],
            "year": row["year"],
            "tokens": row["tokens"],
            "length": row["length"],
            "loughran_tf": tf_dict,
            "weights": weights
        }

        results.append(row_data)

    return pd.DataFrame(results)




def compute_tone(df, positive_words, negative_words,
                 negation_words, positivity_henry, negativity_henry):

    results = []

    for _, row in df.iterrows():


        tokens = row["tokens_L"]
        length = row["length_L"] if row["length_L"] > 0 else 1


        # LOUGHRAN

        weights_L = row["weights_L"]

        pos_score_weighted = 0
        neg_score_weighted = 0

        pos_score_count = 0
        neg_score_count = 0

        for i, word in enumerate(tokens):

            weight = weights_L.get(word, 0)

            if word in positive_words:

                window_start = max(0, i-3)
                context_words = tokens[window_start:i]

                if any(w in negation_words for w in context_words):
                    neg_score_weighted += weight
                    neg_score_count += 1
                else:
                    pos_score_weighted += weight
                    pos_score_count += 1

            elif word in negative_words:
                neg_score_weighted += weight
                neg_score_count += 1


        # HENRY

        weights_H = row["weights_H"]

        pos_score_henry = 0
        neg_score_henry = 0

        pos_score_henry_weighted = 0
        neg_score_henry_weighted = 0

        for i, word in enumerate(tokens):

            weight = weights_H.get(word, 0)

            if word in positivity_henry:

                window_start = max(0, i-3)
                context_words = tokens[window_start:i]

                if any(w in negation_words for w in context_words):
                    neg_score_henry_weighted += weight
                    neg_score_henry += 1
                else:
                    pos_score_henry_weighted += weight
                    pos_score_henry += 1

            elif word in negativity_henry:
                neg_score_henry_weighted += weight
                neg_score_henry += 1


        results.append({
            "company": row["company"],
            "year": row["year"],

            "pos_score_weighted": pos_score_weighted,
            "neg_score_weighted": neg_score_weighted,
            "pos_score": pos_score_count,
            "neg_score": neg_score_count,

            "tone_weighted": (pos_score_weighted - neg_score_weighted), 
            "tone": (pos_score_count - neg_score_count) / length,

            "tone_pos_weighted": pos_score_weighted, 
            "tone_pos": pos_score_count / length,

            "tone_neg_weighted": neg_score_weighted, 
            "tone_neg": neg_score_count / length,

            "pos_score_HENREY_weighted": pos_score_henry_weighted,
            "neg_score_HENREY_weighted": neg_score_henry_weighted,
            "pos_score_HENREY": pos_score_henry,
            "neg_score_HENREY": neg_score_henry,

            "tone_HENREY_weighted":
                (pos_score_henry_weighted - neg_score_henry_weighted), 

            "tone_HENREY":
                (pos_score_henry - neg_score_henry) / length,

            "tone_pos_HENREY_weighted": pos_score_henry_weighted, 
            "tone_pos_HENREY": pos_score_henry / length,

            "tone_neg_HENREY_weighted": neg_score_henry_weighted, 
            "tone_neg_HENREY": neg_score_henry / length,

            #EXTRA
            "pos_score": pos_score_count,
            "neg_score": neg_score_count,
        })

    return pd.DataFrame(results)



def compute_tone(df_L,df_H, positive_words, negative_words, negation_words, positivity_henry, negativity_henry):

    results = []


    for _, row in df_L.iterrows():

        tokens = row["tokens"]
        weights = row["weights"]
        #length = row["length"]
        length = row["length"] if row["length"] > 0 else 1 #avoid zero division


        pos_score_weighted = 0    #positive weighted count count Loughran
        neg_score_weighted = 0    #negative weighted count count Loughran


        pos_score_count = 0     #straight pos count Loughran
        neg_score_count = 0     #straight neg count Loughran

        for i, word in enumerate(tokens):

            weight = weights.get(word, 0)


            if word in positive_words:

              window_start = max(0,i-3) #ned to be max since we can't step outside the beginning of the CEO letter

              context_words = tokens[window_start:i]

              if any(w in negation_words for w in context_words):
                neg_score_weighted +=weight
                neg_score_count += 1

              else:
                pos_score_weighted += weight
                pos_score_count += 1


            elif word in negative_words:
                neg_score_count += 1 #count for unweighted

                neg_score_weighted += weight



        pos_score_henry = 0   #straigth pos count Henry words
        neg_score_henry = 0   #straight neg count Henry words

        pos_score_henry_weighted = 0    #weighted pos count Henry words
        neg_score_henry_weighted = 0    #weighted neg count Henry words

        for i, word in enumerate(tokens):

            weight = weights.get(word, 0)


            if word in positivity_henry:

              window_start = max(0,i-3) #ned to be max since we can't step outside the beginning of the CEO letter

              context_words = tokens[window_start:i]

              if any(w in negation_words for w in context_words):
                neg_score_henry_weighted +=weight
                neg_score_henry += 1

              else:
                pos_score_henry_weighted += weight
                pos_score_henry += 1


            elif word in negativity_henry:
                neg_score_henry += 1 #count for unweighted

                neg_score_henry_weighted += weight

        results.append({
            "company": row["company"],
            "year": row["year"],
            "loughran_tf": row["loughran_tf"],
            "pos_score_weighted": pos_score_weighted,
            "neg_score_weighted": neg_score_weighted,
            "pos_score": pos_score_count,
            "neg_score": neg_score_count,
            "tone_weighted": (pos_score_weighted - neg_score_weighted), 
            "tone": (pos_score_count - neg_score_count) / length,
            "tone_pos_weighted": pos_score_weighted, 
            "tone_pos": pos_score_count / length,
            "tone_neg_weighted": neg_score_weighted, 
            "tone_neg": neg_score_count / length,

            #Henry
            "pos_score_HENREY_weighted": pos_score_henry_weighted,
            "neg_score_HENREY_weighted": neg_score_henry_weighted,
            "pos_score_HENREY": pos_score_henry,
            "neg_score_HENREY": neg_score_henry,
            "tone_HENREY_weighted": (pos_score_henry_weighted - neg_score_henry_weighted), 
            "tone_HENREY": (pos_score_henry - neg_score_henry) / length,
            "tone_pos_HENREY_weighted": pos_score_henry_weighted, 
            "tone_pos_HENREY": pos_score_henry / length,
            "tone_neg_HENREY_weighted": neg_score_henry_weighted, 
            "tone_neg_HENREY": neg_score_henry / length

        })

    return pd.DataFrame(results)



def compute_delta_tone(df):


    df = df.sort_values(["company", "year"])

    #L&M
    df["delta_tone_weighted"] = df.groupby("company")["tone_weighted"].diff()
    df["delta_tone"] = df.groupby("company")["tone"].diff()
    df["delta_tone_pos_weighted"] = df.groupby("company")["tone_pos_weighted"].diff()
    df["delta_tone_pos"] = df.groupby("company")["tone_pos"].diff()
    df["delta_tone_neg_weighted"] = df.groupby("company")["tone_neg_weighted"].diff()
    df["delta_tone_neg"] = df.groupby("company")["tone_neg"].diff()

    #Henry
    df["delta_tone_HENREY_weighted"] = df.groupby("company")["tone_HENREY_weighted"].diff()
    df["delta_tone_HENREY"] = df.groupby("company")["tone_HENREY"].diff()
    df["delta_tone_pos_HENREY_weighted"] = df.groupby("company")["tone_pos_HENREY_weighted"].diff()
    df["delta_tone_pos_HENREY"] = df.groupby("company")["tone_pos_HENREY"].diff()
    df["delta_tone_neg_HENREY_weighted"] = df.groupby("company")["tone_neg_HENREY_weighted"].diff()
    df["delta_tone_neg_HENREY"] = df.groupby("company")["tone_neg_HENREY"].diff()

    return df



def write_tone_to_csv(file_path, df):

    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)


            #header = ["company", "year", "pos_score", "neg_score", "tone_w", "tone_w_len", "tone_raw", "tone_raw_len"]
        header = ["company",
                      "year",

                      #Loughran
                      "tone_weighted","tone",
                      "tone_pos_weighted",
                      "tone_pos",
                      "tone_neg_weighted",
                      "tone_neg",
                      "delta_tone_weighted",
                      "delta_tone",
                      "delta_tone_pos_weighted",
                      "delta_tone_pos",
                      "delta_tone_neg_weighted",
                      "delta_tone_neg",
                      "pos_score_weighted",
                      "pos_score",
                      "neg_score_weighted","neg_score",

                      #Henry
                      "tone_HENREY_weighted",
                      "tone_HENREY",
                      "tone_pos_HENREY_weighted",
                      "tone_pos_HENREY",
                      "tone_neg_HENREY_weighted",
                      "tone_neg_HENREY",
                      "delta_tone_HENREY_weighted",
                      "delta_tone_HENREY",
                      "delta_tone_pos_HENREY_weighted",
                      "delta_tone_pos_HENREY",
                      "delta_tone_neg_HENREY_weighted",
                      "delta_tone_neg_HENREY",
                      "pos_score_HENREY_weighted",
                      "pos_score_HENREY",
                      "neg_score_HENREY_weighted",
                      "neg_score_HENREY"
                      ]
        writer.writerow(header)

        for _, row in df.iterrows():
            writer.writerow([
                row["company"],
                row["year"],

                #tone Loughran

                row["tone_weighted"],
                row["tone"],

                row["tone_pos_weighted"],
                row["tone_pos"],

                row["tone_neg_weighted"],
                row["tone_neg"],

                #Delta tone Loughran

                row["delta_tone_weighted"],
                row["delta_tone"],

                row["delta_tone_pos_weighted"],
                row["delta_tone_pos"],

                row["delta_tone_neg_weighted"],
                row["delta_tone_neg"],

                #tone score Loughran

                row["pos_score_weighted"],
                row["pos_score"],

                row["neg_score_weighted"],
                row["neg_score"],

                #tone Henry

                row["tone_HENREY_weighted"],
                row["tone_HENREY"],

                row["tone_pos_HENREY_weighted"],
                row["tone_pos_HENREY"],

                row["tone_neg_HENREY_weighted"],
                row["tone_neg_HENREY"],

                #Delta tone Henry

                row["delta_tone_HENREY_weighted"],
                row["delta_tone_HENREY"],

                row["delta_tone_pos_HENREY_weighted"],
                row["delta_tone_pos_HENREY"],

                row["delta_tone_neg_HENREY_weighted"],
                row["delta_tone_neg_HENREY"],

                #tone score Henry

                row["pos_score_HENREY_weighted"],
                row["pos_score_HENREY"],

                row["neg_score_HENREY_weighted"],
                row["neg_score_HENREY"]
            ])



def write_top_words_structured(file_path, df, positive_words, negative_words, top_n=10):

    file_exists = os.path.isfile(file_path)

    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

    
        header = ["company", "year"]

        for i in range(1, top_n + 1):
            header += [f"pos_word_{i}", f"pos_tf_{i}", f"pos_w_{i}"]

        for i in range(1, top_n + 1):
            header += [f"neg_word_{i}", f"neg_tf_{i}", f"neg_w_{i}"]

        writer.writerow(header)

        for _, row in df.iterrows():

            weights = row["weights"]
            tf_dict = row["loughran_tf"]

  
            pos_words = {w: weights[w] for w in weights if w in positive_words}
            neg_words = {w: weights[w] for w in weights if w in negative_words}


            top_pos = sorted(pos_words.items(), key=lambda x: x[1], reverse=True)[:top_n]
            top_neg = sorted(neg_words.items(), key=lambda x: x[1], reverse=True)[:top_n]

            row_out = [row["company"], row["year"]]

       
            for w, v in top_pos:
                row_out += [w, tf_dict[w], round(v, 3)]


            for _ in range(top_n - len(top_pos)):
                row_out += ["", "", ""]

    
            for w, v in top_neg:
                row_out += [w, tf_dict[w], round(v, 3)]

            for _ in range(top_n - len(top_neg)):
                row_out += ["", "", ""]

            writer.writerow(row_out)




#select your folders and paths


folder_path = #map with all your CEO letters
output_csv = #output


output_csv_extra_stat_words= #output extra stat L&M
output_csv_extra_stat_words_HENRY= #output extra stat Henrey




def main():

    negation_words = ["no", "not", "none", "neither", "never", "nobody"]


    df = create_df(folder_path)

    N = len(df)  # number of CEO letters


    df_i_L = compute_dfi(df)

    df_L = compute_tf(df, positive_words, negative_words)
    print(df_L.columns)

    df_weights_L = compute_weights(df_L, df_i_L, N)
    print(df_weights_L.columns)

    print("DEBUG TYPE:", type(df_weights_L))
    print("DEBUG COLUMNS:", df_weights_L.columns)
    print(df_weights_L.head(1))


    df_i_H = compute_dfi(df)

    df_H = compute_tf(df, positivity_henry, negativity_henry)
    print(df_H.columns)

    df_weights_H = compute_weights(df_H, df_i_H, N)
    print(df_weights_H.columns)

    print("DEBUG TYPE:", type(df_weights_H))
    print("DEBUG COLUMNS:", df_weights_H.columns)
    print(df_weights_H.head(1))



    df_merged = df_weights_L.merge(
        df_weights_H,
        on=["company", "year"],
        suffixes=("_L", "_H"),
        how="inner"
    )


    df_final = compute_tone(
        df_merged,
        positive_words,
        negative_words,
        negation_words,
        positivity_henry,
        negativity_henry
    )



    df_final_final = compute_delta_tone(df_final)



    write_tone_to_csv(output_csv, df_final_final)

    write_top_words_structured(
        output_csv_extra_stat_words,
        df_weights_L,
        positive_words,
        negative_words,
        top_n=10
    )

    write_top_words_structured(
        output_csv_extra_stat_words_HENRY,
        df_weights_H,
        positivity_henry,
        negativity_henry,
        top_n=10
    )


if __name__ == "__main__":
    main()
 
