import pandas as pd
import streamlit as st
st.image("logon.jpg")
st.set_page_config(page_title="Tính lãi gửi tiết kiệm", page_icon="💰", layout="centered")


def fmt(x: float) -> str:
    """Định dạng số tiền kiểu Việt Nam: 1.234.567 đ"""
    return f"{x:,.0f}".replace(",", ".") + " đ"


def tinh_lai(goc, so_thang, lai_suat_nam, hinh_thuc, loai_lai):
    """
    Trả về bảng chi tiết từng kỳ.
    - Lãi đơn: lãi mỗi kỳ = gốc ban đầu x lãi suất x số tháng của kỳ / 12 (gốc không đổi).
    - Lãi kép: lãi mỗi kỳ được nhập vào gốc, kỳ sau tính lãi trên số dư mới.
    - Cuối kỳ: chỉ có 1 kỳ duy nhất = toàn bộ kỳ hạn (lãi đơn và lãi kép cho kết quả như nhau).
    """
    buoc = {"Hàng tháng": 1, "Hàng quý": 3, "Cuối kỳ": so_thang}[hinh_thuc]
    r = lai_suat_nam / 100

    so_du = goc
    lai_tich_luy = 0.0
    da_qua = 0
    rows = []
    ky = 0

    while da_qua < so_thang:
        ky += 1
        m = min(buoc, so_thang - da_qua)  # kỳ cuối có thể ngắn hơn
        co_so_tinh = so_du if loai_lai == "Lãi kép" else goc
        lai = co_so_tinh * r * m / 12
        lai_tich_luy += lai
        da_qua += m

        if loai_lai == "Lãi kép":
            so_du += lai
            tong = so_du
        else:
            tong = goc + lai_tich_luy

        rows.append(
            {
                "Kỳ": ky,
                "Đến tháng thứ": da_qua,
                "Số dư tính lãi": co_so_tinh,
                "Tiền lãi kỳ": lai,
                "Lãi tích lũy": lai_tich_luy,
                "Gốc + lãi": tong,
            }
        )

    return pd.DataFrame(rows), lai_tich_luy, goc + lai_tich_luy


# ---------------- Giao diện ----------------
st.title("💰 Tính lãi gửi tiết kiệm")
st.caption("Nhập thông tin khoản gửi để xem lãi và tổng tiền nhận được.")

col1, col2 = st.columns(2)

with col1:
    goc = st.number_input(
        "Số tiền gửi (VNĐ)", min_value=0.0, value=100_000_000.0, step=1_000_000.0, format="%.0f"
    )
    lai_suat = st.number_input(
        "Lãi suất (%/năm)", min_value=0.0, max_value=100.0, value=5.5, step=0.1, format="%.2f"
    )
    hinh_thuc = st.selectbox("Hình thức nhận lãi", ["Cuối kỳ", "Hàng tháng", "Hàng quý"])

with col2:
    c_a, c_b = st.columns([2, 1])
    with c_a:
        ky_han_so = st.number_input("Kỳ hạn", min_value=1, value=12, step=1)
    with c_b:
        don_vi = st.selectbox("Đơn vị", ["Tháng", "Năm"])
    loai_lai = st.radio("Loại lãi", ["Lãi đơn", "Lãi kép"], horizontal=True)

so_thang = int(ky_han_so) * (12 if don_vi == "Năm" else 1)

if hinh_thuc == "Cuối kỳ" and loai_lai == "Lãi kép":
    st.info("Với hình thức nhận lãi cuối kỳ chỉ có 1 kỳ tính lãi, nên lãi kép cho kết quả giống lãi đơn.")

if loai_lai == "Lãi kép":
    st.caption("Lãi kép: tiền lãi mỗi kỳ được cộng vào gốc để tính lãi cho kỳ sau (không rút lãi giữa kỳ).")
else:
    st.caption("Lãi đơn: lãi mỗi kỳ chỉ tính trên số tiền gốc ban đầu, lãi được nhận ra định kỳ.")

if st.button("Tính lãi", type="primary", use_container_width=True):
    if goc <= 0:
        st.error("Vui lòng nhập số tiền gửi lớn hơn 0.")
    else:
        df, tong_lai, tong_nhan = tinh_lai(goc, so_thang, lai_suat, hinh_thuc, loai_lai)

        st.subheader("Kết quả")

        lai_ky_dau = df.loc[0, "Tiền lãi kỳ"]
        if loai_lai == "Lãi đơn" or len(df) == 1:
            label_lai_ky = "Tiền lãi mỗi kỳ" if len(df) > 1 else "Tiền lãi nhận cuối kỳ"
        else:
            label_lai_ky = "Tiền lãi kỳ đầu tiên"

        m1, m2 = st.columns(2)
        m1.metric(label_lai_ky, fmt(lai_ky_dau))
        m2.metric("Tổng tiền lãi", fmt(tong_lai))

        m3, m4 = st.columns(2)
        m3.metric("Số tiền gốc", fmt(goc))
        m4.metric("Tổng gốc + lãi", fmt(tong_nhan))

        if loai_lai == "Lãi kép" and len(df) > 1:
            st.caption(
                f"Lãi kép tăng dần theo từng kỳ: kỳ đầu {fmt(df.iloc[0]['Tiền lãi kỳ'])}, "
                f"kỳ cuối {fmt(df.iloc[-1]['Tiền lãi kỳ'])}."
            )

        # Bảng chi tiết
        st.subheader("Chi tiết từng kỳ")
        hien_thi = df.copy()
        for c in ["Số dư tính lãi", "Tiền lãi kỳ", "Lãi tích lũy", "Gốc + lãi"]:
            hien_thi[c] = hien_thi[c].apply(fmt)
        st.dataframe(hien_thi, hide_index=True, use_container_width=True)

        # Biểu đồ
        st.subheader("Biểu đồ tăng trưởng")
        st.line_chart(df.set_index("Đến tháng thứ")[["Gốc + lãi"]])

        # Tải CSV
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Tải bảng chi tiết (CSV)", csv, "lich_tinh_lai.csv", "text/csv")

st.divider()
st.caption("Kết quả mang tính tham khảo (quy ước 1 năm = 12 tháng). Lãi thực tế phụ thuộc quy định của từng ngân hàng.")