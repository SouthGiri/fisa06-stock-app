
# 표준 라이브러리
import datetime
from io import BytesIO

# 서드파티 라이브러리
import datetime
from io import BytesIO
import streamlit as st
import pandas as pd
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import koreanize_matplotlib
import plotly.graph_objects as go

import os
from dotenv import load_dotenv

load_dotenv()

my_name = os.getenv('MY_NAME')
st.header(f'{my_name} 가 제작한 페이지')


def get_krx_company_list() -> pd.DataFrame:
    try:
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
        df_listing = pd.read_html(url, header=0, flavor='bs4', encoding='EUC-KR')[0]
        
        # 필요한 컬럼만 추출 및 종목코드 6자리 포맷 맞추기
        df_listing = df_listing[['회사명', '종목코드']].copy()
        df_listing['종목코드'] = df_listing['종목코드'].apply(lambda x: f'{x:06}')
        return df_listing
    except Exception as e:
        st.error(f"상장사 명단을 불러오는 데 실패했습니다: {e}")
        return pd.DataFrame(columns=['회사명', '종목코드'])


def get_stock_code_by_company(company_name: str) -> str:
    # 만약 입력값이 숫자 6자리라면 그대로 반환
    if company_name.isdigit() and len(company_name) == 6:
        return company_name
    
    company_df = get_krx_company_list()
    codes = company_df[company_df['회사명'] == company_name]['종목코드'].values
    if len(codes) > 0:
        return codes[0]
    else:
        raise ValueError(f"'{company_name}'을 찾을 수 없습니다. 종목코드 6자리를 직접 입력해보세요.")


# --- 메인 로직 ---
company_name = st.sidebar.text_input('회사명 또는 종목코드 입력하세요.')

today = datetime.datetime.now()
selected_dates = st.sidebar.date_input('날짜를 입력하세요.', (today, today))
confirm_btn = st.sidebar.button('조회하기')

if confirm_btn:
    if not company_name:
        st.warning("조회할 회사 이름을 입력하세요.")
    else:
        try:
            with st.spinner('데이터를 수집하는 중...'):
                stock_code = get_stock_code_by_company(company_name)
                start_date = selected_dates[0].strftime("%Y%m%d")
                end_date = selected_dates[1].strftime("%Y%m%d")
                
                price_df = fdr.DataReader(stock_code, start_date, end_date)
                
            if price_df.empty:
                st.info("해당 기간의 주가 데이터가 없습니다.")
            else:
                st.subheader(f"[{company_name}] 주가 데이터")
                st.dataframe(price_df.tail(10), width="stretch")

                # 엑셀 다운로드 기능
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    price_df.to_excel(writer, index=True, sheet_name='Sheet1')
                st.download_button(
                    label="📥 엑셀 파일 다운로드",
                    data=output.getvalue(),
                    file_name=f"{company_name}_주가.xlsx",
                    mime="application/vnd.ms-excel"
                )

                
                # CandleStick visualization
                fig = go.Figure(data=[go.Candlestick(x=price_df.index,
                                     open=price_df['Open'],
                                     high=price_df['High'],
                                     low=price_df['Low'],
                                     close=price_df['Close'])])
                st.plotly_chart(fig, use_container_width=True)

                # 인터랙티브 HTML 다운로드 (애니메이션/툴팁 포함)
                html_bytes = fig.to_html(full_html=False, include_plotlyjs='cdn').encode('utf-8')
                st.download_button(
                    label="📥 차트 다운로드",
                    data=html_bytes,
                    file_name=f"{company_name}_차트.html",
                    mime="text/html"
                )

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")