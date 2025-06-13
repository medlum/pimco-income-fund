import requests
import pandas as pd
from io import BytesIO
import streamlit as st
import altair as alt
from datetime import datetime, timedelta


# Get today's date in 'YYYY-MM-DD' format
today_str = datetime.today().strftime('%Y-%m-%d')

# Set Streamlit layout to wide mode
st.set_page_config(page_title = "Pimco Income Fund", 
                   initial_sidebar_state = "expanded",
                   layout = "centered")

st.title(":blue[PIMCO Income Fund]")
st.subheader(":gray[ISIN: IE00B91RQ825]")

#st.header("Historical Prices & Distributions")


text = """
ABOUT PIMCO INCOME FUND

- PIMCO GIS Income Fund Admin SGD Hedged – Inc, a globally diversified bond fund managed by PIMCO, with over S$100 billion under management and more than a decade of track record. The fund is currently available via Maribank, under MariInvest Income.
- Maribank a digital bank owned by SEA Limited. MariInvest Income aims to deliver monthly payouts directly to Mari Savings Account, or opt to reinvest them seamlessly through the Maribank app.  No fees from MariBank: no transaction, account, upfront, sales, or withdrawal charges. The underlying fund expense ratio: 1.05% p.a., factored into unit price. Refer to https://www.maribank.sg/product/mari-invest/income for more information.
- This visualisation app collects the historical NAV and dividends daily from Pimco's website. https://www.pimco.com/sg/en/investments/gis/income-fund/admin-sgd-hedged-income
- The estimated returns is based on the formulaes provided by Maribank under its FAQ.
"""

with st.sidebar:
    st.write(f"Updated on {today_str}")
    st.markdown(
        f"<div style='color: gray; font-size: 14px; white-space: pre-wrap;'>{text}</div>",
        unsafe_allow_html=True
    )


# Common headers
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "client": "WEB",
    "countrycode": "SG",
    "langcode": "en",
    "origin": "https://www.pimco.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.pimco.com/",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "userrole": "IND"
}

# URLs
base_url = "https://fund-ui.pimco.com/fund-detail-api/api/funds/G7098D524"
params = {
    "startAsOfDate": "2012-11-30",
    "endAsOfDate": today_str
}

# --- Download NAV data ---
nav_url = f"{base_url}/nav-timeseries/export"
nav_response = requests.get(nav_url, headers=headers, params=params)

# --- Download Distribution data ---
dist_url = f"{base_url}/distribution-timeseries/export"
dist_response = requests.get(dist_url, headers=headers, params=params)

if nav_response.status_code in (200, 201) and dist_response.status_code in (200, 201):
    # Read Excel files with header on third row (index 2)
    nav_df = pd.read_excel(BytesIO(nav_response.content), header=2, engine='openpyxl')
    dist_df = pd.read_excel(BytesIO(dist_response.content), header=2, engine='openpyxl')

    tab1, tab2, tab3 = st.tabs(
        ["📈:orange[Historical NAV]", "📊:orange[Historical Distribution]", "💵:orange[Estimated Returns]"])
    # NAV CHART

    with tab1:
        nav_df.columns = nav_df.columns.str.strip()
        nav_df['Date'] = pd.to_datetime(
            nav_df['Date'], dayfirst=True, errors='coerce')
        nav_df = nav_df.dropna(subset=['Date'])
        nav_df = nav_df.sort_values(by='Date', ascending=False)

        latest_nav = nav_df.iloc[0, [1]].astype(float).values[0]
        latest_nav_date = pd.to_datetime(nav_df['Date'].iloc[0]).strftime('%Y-%m-%d')

        st.info(f"Latest NAV: {latest_nav} ({latest_nav_date})", icon="ℹ️")

                # Filter by dates
        col1, col2 = st.columns(2, gap="medium", border=True)
        min_date, max_date = nav_df['Date'].min(
        ).date(), nav_df['Date'].max().date()
        date_range = col1.date_input(
            ":blue[Filter NAV by date range]", [min_date, max_date])

        if len(date_range) == 2:
            nav_df = nav_df[(nav_df['Date'] >= pd.to_datetime(date_range[0])) &
                            (nav_df['Date'] <= pd.to_datetime(date_range[1]))]

        sampling_step = col2.slider(":blue[Plot every Nth NAV point]", 1, 10, 1)
        nav_df_sampled = nav_df.iloc[::sampling_step]

        nav_chart = alt.Chart(nav_df_sampled).mark_line(point=False).encode(
            x='Date:T',
            y='NAV (SGD):Q',
            tooltip=['Date:T', 'NAV (SGD):Q']
        ).properties(
            title='NAV Over Time',
            width=800,
            height=400
        ).interactive()

        chg_chart = alt.Chart(nav_df_sampled).mark_line(point=False, color='orange').encode(
            x='Date:T',
            y='Chg (%):Q',
            tooltip=['Date:T', 'Chg (%):Q']
        ).properties(
            title='Daily % Change Over Time',
            width=800,
            height=400
        ).interactive()

        st.altair_chart(nav_chart, use_container_width=True)
        st.altair_chart(chg_chart, use_container_width=True)



    # DISTRIBUTION CHART
    with tab2:
        dist_df['Ex-dividend Date'] = pd.to_datetime(
            dist_df['Ex-dividend Date'], dayfirst=True, errors='coerce')
        dist_df = dist_df.dropna(subset=['Ex-dividend Date'])
        dist_df = dist_df.sort_values(by='Ex-dividend Date', ascending=False)
        latest_payout = dist_df.iloc[0, [1]].astype(float).values[0]
        latest_payout_date = pd.to_datetime(dist_df['Ex-dividend Date'].iloc[0]).strftime('%Y-%m-%d')
        with st.expander("Expand Data"):
            st.dataframe(dist_df)

        st.info(f"Latest Payout: {latest_payout} ({latest_payout_date})", icon="ℹ️")

        # Filter by date
        col1, col2 = st.columns(2, gap="medium", border=True)
        min_date, max_date = dist_df['Ex-dividend Date'].min(
        ).date(), dist_df['Ex-dividend Date'].max().date()
        date_range = col1.date_input(
            ":blue[Filter Distribution by date range]", [min_date, max_date])

        if len(date_range) == 2:
            dist_df = dist_df[(dist_df['Ex-dividend Date'] >= pd.to_datetime(date_range[0])) &
                              (dist_df['Ex-dividend Date'] <= pd.to_datetime(date_range[1]))]

        sampling_step = col2.slider(
            ":blue[Plot every Nth Distribution point]", 1, 10, 1, key="distribution")
        dist_df_sampled = dist_df.iloc[::sampling_step]

        dist_chart = alt.Chart(dist_df_sampled).mark_line(point=False).encode(
            x='Ex-dividend Date:T',
            y='Dividend Per Share (SGD):Q',
            tooltip=['Ex-dividend Date:T', 'Dividend Per Share (SGD):Q']
        ).properties(
            title='Dividend Per Share Over Time',
            width=800,
            height=400
        ).interactive()

        source_vs_capital = alt.Chart(dist_df_sampled).transform_fold(
            ['% Distribution From Net Distributable Income',
                '% Distribution From Capital'],
            as_=['Type', 'Percentage']
        ).mark_line(point=False).encode(
            x='Ex-dividend Date:T',
            y=alt.Y('Percentage:Q', title='%'),
            color=alt.Color('Type:N', legend=alt.Legend(
                orient='bottom', labelLimit=0)),
            tooltip=['Ex-dividend Date:T', 'Type:N', 'Percentage:Q']
        ).properties(
            title='Distribution Breakdown',
            width=800,
            height=400
        ).interactive()

        st.altair_chart(dist_chart, use_container_width=True)
        st.altair_chart(source_vs_capital, use_container_width=True)

    with tab3:
        #st.info(f"Latest Payout: {latest_payout} ({latest_payout_date})", icon="ℹ️")

        col1, col2, col3 = st.columns(3, vertical_alignment="bottom")
        amount_invested = col1.number_input("Amount Invested") 
        purchased_unit_price = col2.number_input("Purchased Unit Price")
        yesterday_str = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        #latest_nav_price = col3.number_input(
        #    f"Latest NAV (as of {yesterday_str})")

        text = """
        Enter the dollar amount invested and unit price purchased to calculate the returns and estimated payout. 
        """
        st.info(text)

        if col3.button("🔎 Calculate"):

            total_units = amount_invested / \
                purchased_unit_price if amount_invested != 0 and purchased_unit_price != 0 else 0
            current_market_value = total_units * latest_nav
            total_return = current_market_value - amount_invested

            col1, col2, col3, col4 = st.columns(4)
            col1.metric(":orange[Total units]", f"${total_units:.3f}")
            col2.metric(":orange[Current market value]",
                        f"${current_market_value:.3f}")
            col3.metric(":orange[Total return]", f"${total_return:.3f}")
            col4.metric(f":orange[Estimated monthly payout]",
                        f"${latest_payout * total_units:.3f}")
            
            text = """
            Estimated monthly payout is based on the ex-dividend date of the previous month.
            """
            st.info(text)

else:
    print(
        f"NAV status: {nav_response.status_code}, Distribution status: {dist_response.status_code}")
