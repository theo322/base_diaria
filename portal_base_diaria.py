import streamlit as st
import pandas as pd
import os
import boto3
import pandas as pd
import datetime


# Load AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')
# Create an S3 client
s3 = boto3.client('s3', 
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                  region_name=AWS_DEFAULT_REGION)
# Name of your S3 bucket
bucket_name = 'myavbucket'
response = s3.list_objects_v2(Bucket=bucket_name)


# Start STREAMLIT
st.title("Baixe uma base diária 📂")
#if st.text_input('Insira senha') == "$avenida2024#!":
st.subheader("Por conta do volume de dados, não é possível gerar uma base diária contendo loja e item.")
st.markdown("É possível gerar bases nos formatos **'dia-item'** ou **'dia-loja'**.")
st.markdown("**:green[As duas bases contém a hierarquia de produto até subgrupo]**")



if 'run_clicked' not in st.session_state:
    st.session_state.run_clicked = False


formato = st.radio(":red[Escolha abaixo o formato desejado:]", options=["Loja", "Item"], index=None)
if formato is not None:
    ano = st.radio("Escolha o ano", options=[2023, 2024], index=None)
    if ano is not None:

        familia = st.selectbox("Escolha uma família", options=["01 Lar", "02 Masculino", "03 Feminino", "04 Infantil", "05 Calçados", "10 Acessorios Av" ], index= None)
        if familia is not None:
            st.subheader("Vamos escolher o período que você deseja analisar 📅")
            start_date = st.date_input(":red[Escolha a data inicial]", value= None, min_value=datetime.date(ano, 1, 1), max_value=datetime.date(ano, 12,31)) 
            if start_date is not None:
                end_date = st.date_input(":red[Escolha a data final]", min_value=datetime.date(ano, 1, 1), max_value=datetime.date(ano, 12,31))
                if start_date > end_date:
                    st.error("A data inicial deve ser menor(mais antiga) que a data final")
                else:
                
                    if st.button("Executar"):

                     
                        start_date = pd.to_datetime(start_date)
                        end_date = pd.to_datetime(end_date)
                        csv_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.csv')]
                        csv_obj = s3.get_object(Bucket=bucket_name, Key=f"{ano}_{familia}_{formato}.csv")
                        df = pd.read_csv(csv_obj['Body'], encoding='utf-8')
                        df['DATA'] = pd.to_datetime(df['DATA'])
                        df2 = df.loc[(df['DATA'] >= start_date) & (df['DATA'] <= end_date)]
                        df2["DATA"] = df2["DATA"].dt.date
                        if formato ==  "Item":
                            df2["ITEM"] = df2["ITEM"].astype(str)
                        st.dataframe(df2)

                        #Formatando decimais
                        formatted_df = df2.copy()
                        formatted_df["Venda R$"] = formatted_df["Venda R$"].astype(str).str.replace(",", "")
                        formatted_df["Venda R$"] = formatted_df["Venda R$"].astype(str).str.replace(".", ",")
                        formatted_df["R$ Margem"] = formatted_df["R$ Margem"].astype(str).str.replace(",", "")
                        formatted_df["R$ Margem"] = formatted_df["R$ Margem"].astype(str).str.replace(".", ",")
                        formatted_df["R$ Estoque"] = formatted_df["R$ Estoque"].astype(str).str.replace(",", "")
                        formatted_df["R$ Estoque"] = formatted_df["R$ Estoque"].astype(str).str.replace(".", ",")
                        formatted_df["Venda QTD"] = formatted_df["Venda QTD"].astype(str).str.replace(",", "")
                        formatted_df["Estoque QTD"] = formatted_df["Estoque QTD"].astype(str).str.replace(",", "")
                        formatted_df["Estoque trânsito peças"] = formatted_df["Estoque trânsito peças"].astype(str).str.replace(",", "")

                        csv = formatted_df.to_csv(index=False, encoding="Latin-1")
                        st.download_button("Baixar base", csv, "base.csv",mime="text/csv")
                        
