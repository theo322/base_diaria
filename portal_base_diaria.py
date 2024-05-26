import streamlit as st
import pandas as pd
import boto3
import datetime
from dotenv import load_dotenv
import io
import os

# Load AWS credentials from .env file
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')

# Create an S3 client
s3 = boto3.client('s3', 
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                  region_name=AWS_DEFAULT_REGION)

# Name of your S3 bucket
bucket_name = 'myavbucket'

# Column names
column_names = ["Data", "Loja", "Departamento", "Grupo", "Subgrupo", "Item", "Venda QTD", "Venda R$", "R$ Margem", "Estoque R$", "Estoque QTD", "Estoque transito QTD", "Estoque alocado CD"]

# Start STREAMLIT
st.set_page_config(page_title= "Base diária", page_icon="💾")
st.title("Baixe uma base diária 📂")
st.subheader("Por conta do volume de dados, é recomendado escolher períodos inferiores à 3 meses.")
st.markdown("**:green[É possível gerar bases do período completo! Isso pode demorar um pouco ⏳, tenha paciência...]**")
st.markdown("**As bases são geradas no formato CSV**")

ano = st.radio("Escolha o ano", options=[2023, 2024], index=None)
if ano is not None:
    familia = st.selectbox("Escolha uma família", options=["Lar", "Masculino", "Feminino", "Infantil", "Calçados", "Acessorios Av"], index=None)
    if familia is not None:
        st.subheader("Vamos escolher o período que você deseja analisar 📅")
        start_date = st.date_input(":red[Escolha a data inicial] (Ano/Mês/Dia)", value=None, min_value=datetime.date(ano, 1, 1), max_value=datetime.date(ano, 12, 31))
        if start_date is not None:
            end_date = st.date_input(":red[Escolha a data final] (Ano/Mês/Dia)", min_value=start_date, max_value=datetime.date(ano, 12, 31))
            if start_date > end_date:
                st.error("A data inicial deve ser menor(mais antiga) que a data final")
            else:
                if st.button("Executar"):
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    end_date_str = end_date.strftime('%Y-%m-%d')
                    
                    # SQL query to filter data based on date range
                    sql_query = f"SELECT * FROM s3object s WHERE s._1 >= '{start_date_str}' AND s._1 <= '{end_date_str}'"
                    response = s3.select_object_content(
                        Bucket=bucket_name,
                        Key=f"{ano}_{familia}.csv",
                        ExpressionType='SQL',
                        Expression=sql_query,
                        InputSerialization={'CSV': {'FileHeaderInfo': 'IGNORE', 'RecordDelimiter': '\n', 'FieldDelimiter': ','}},
                        OutputSerialization={'CSV': {}}
                    ) 

                    records = []
                    for event in response["Payload"]:
                        if "Records" in event:
                            records.append(event["Records"]["Payload"])
                    csv_data = b''.join(records)
                    csv_buffer = io.BytesIO(csv_data)
                    df = pd.read_csv(csv_buffer, names=column_names, encoding='latin1')

                    df["Item"] = df["Item"].astype(str)

                    st.dataframe(df.head(200))
                    formatted_df = df.copy()
                    formatted_df["Venda R$"] = formatted_df["Venda R$"].astype(str).str.replace(",", "")
                    formatted_df["Venda R$"] = formatted_df["Venda R$"].astype(str).str.replace(".", ",")
                    formatted_df["R$ Margem"] = formatted_df["R$ Margem"].astype(str).str.replace(",", "")
                    formatted_df["R$ Margem"] = formatted_df["R$ Margem"].astype(str).str.replace(".", ",")
                    formatted_df["Estoque R$"] = formatted_df["Estoque R$"].astype(str).str.replace(",", "")
                    formatted_df["Estoque R$"] = formatted_df["Estoque R$"].astype(str).str.replace(".", ",")
                    formatted_df["Venda QTD"] = formatted_df["Venda QTD"].astype(str).str.replace(",", "")
                    formatted_df["Estoque QTD"] = formatted_df["Estoque QTD"].astype(str).str.replace(",", "")
                    formatted_df["Estoque transito QTD"] = formatted_df["Estoque transito QTD"].astype(str).str.replace(",", "")
                    formatted_df["Estoque alocado CD"] = formatted_df["Estoque alocado CD"].astype(str).str.replace(",", "")
                        

                    # Provide a download button for the CSV file
                    csv = formatted_df.to_csv(index=False, encoding="utf-8")
                    st.download_button("📥", csv, f"{familia}_{start_date}_{end_date}.csv", mime="text/csv")
