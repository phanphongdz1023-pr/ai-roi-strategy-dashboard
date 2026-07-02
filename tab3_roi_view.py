import streamlit as st
import plotly.express as px
from data_engine import load_and_process_roi_data


def render_tab3():
    st.header("📈 Phân Hệ 3: Tối Ưu Hóa ROI Điều Chỉnh Theo Rủi Ro")
    st.markdown(
        r"""
        Phân hệ này không chỉ tính toán dòng tiền cơ bản ($Tần\ suất \times Mức\ lương$)
        mà còn áp dụng ma trận phạt rủi ro dựa trên **Giới hạn công nghệ** và
        **Sự ủng hộ/phản kháng của con người**.
        Mục tiêu: Tìm ra các tác vụ "Vàng" để ưu tiên rót ngân sách phát triển AI Agent.
        """
    )

    roi_data = load_and_process_roi_data()

    # Chốt chặn an toàn thứ 2: dù data_engine.py đã lọc NaN, vẫn kiểm tra lại
    # ở đây trước khi vẽ, để không bao giờ đưa NaN vào thuộc tính 'size' của Plotly.
    if roi_data is not None:
        roi_data = roi_data.dropna(subset=['Priority_Score', 'frequency', 'salary'])

    if roi_data is not None and not roi_data.empty:
        st.subheader("1. Bản Đồ Phân Bổ Ngân Sách Đầu Tư")
        st.caption(
            "Kích thước bong bóng = **Điểm ưu tiên đã chuẩn hóa (0-100)**, kết hợp cân bằng "
            "giá trị kinh tế (lương + tần suất), năng lực công nghệ và mức ủng hộ của người lao động — "
            "thay vì dùng trực tiếp số USD, để lương cao không còn áp đảo các yếu tố khả thi khác."
        )

        fig = px.scatter(
            roi_data,
            x='frequency',
            y='salary',
            size='Priority_Score',
            color='seniority',  # Junior / Senior / Unknown
            hover_name='task_name',
            hover_data={
                'Priority_Score': ':.1f',
                'Adjusted_ROI': ':.2f',
                'Base_ROI': ':.2f',
                'expert_score': ':.2f',
                'worker_support': ':.2f',
            },
            title="Ma Trận Điểm Mù Ngân Sách (Kích thước bong bóng = Điểm ưu tiên chuẩn hóa 0-100)",
            labels={
                'frequency': 'Tần suất tác vụ (thang O*NET 3-7)',
                'salary': 'Lương trung bình của nghề (USD/năm)',
                'seniority': 'Cấp bậc nhân sự (đa số người chấm)',
            },
            color_discrete_map={'Senior': '#1f77b4', 'Junior': '#ff7f0e', 'Unknown': '#999999'},
            template='plotly_white',
        )

        max_score = roi_data['Priority_Score'].max()
        if max_score and max_score > 0:
            fig.update_traces(marker=dict(sizemin=5, sizemode='area', sizeref=2. * max_score / (50. ** 2)))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("2. Khuyến Nghị Hành Động Chiến Lược")
        top_3_tasks = roi_data.sort_values('Priority_Score', ascending=False).head(3)

        cols = st.columns(3)
        for index, (col, (_, row)) in enumerate(zip(cols, top_3_tasks.iterrows())):
            with col:
                st.info(f"**Ưu tiên #{index + 1}**")
                st.metric(
                    label=row['task_name'][:60] + ('…' if len(row['task_name']) > 60 else ''),
                    value=f"Điểm ưu tiên: {row['Priority_Score']:.1f}/100",
                    delta=f"{row['seniority']} Task",
                    delta_color="normal" if row['seniority'] == 'Senior' else "off",
                )
                st.caption(f"Tham khảo giá trị kinh tế tuyệt đối: ~{row['Adjusted_ROI']:,.0f} USD")

        st.markdown(
            """
            > 💡 **Phân tích Insight:** Các tác vụ của **Senior (Màu xanh)** mang lại điểm ưu tiên
            > cao không chỉ vì cắt giảm chi phí, mà vì tự động hóa chúng sẽ giải phóng thời gian
            > để chuyên gia tập trung vào R&D. Ngược lại, cẩn trọng khi tự động hóa 100% tác vụ
            > của **Junior (Màu cam)** vì có thể làm gãy lộ trình đào tạo nội bộ.
            >
            > ⚠️ **Lưu ý phương pháp luận:** Điểm ưu tiên (0-100) đã được chuẩn hóa để năng lực
            > công nghệ và mức ủng hộ của người lao động có trọng số ngang bằng với giá trị kinh tế —
            > tránh tình trạng các nghề lương cao tự động chiếm top dù năng lực tự động hóa thấp.
            > Cột "Tham khảo giá trị kinh tế tuyệt đối" chỉ mang tính minh họa quy mô USD, không dùng
            > để xếp hạng.
            """
        )
    else:
        st.warning("Không tìm thấy dữ liệu hợp lệ để tính toán ROI.")