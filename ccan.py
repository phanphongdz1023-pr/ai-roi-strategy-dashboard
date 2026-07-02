import streamlit as st
from tab3_roi_view import render_tab3

# Thiết lập cấu hình trang
st.set_page_config(
    page_title="AI Agent CS Strategy & Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Tiêu đề chính
st.title("📊 AI Agent CS Strategy & Analytics Dashboard")
st.markdown("Hệ thống Hỗ trợ Ra Quyết định (DSS) phân bổ nguồn lực tự động hóa doanh nghiệp.")

# Chỉ giữ lại duy nhất nội dung của Tab 3
# Chúng ta không cần dùng st.tabs nữa mà gọi trực tiếp hàm render
render_tab3()