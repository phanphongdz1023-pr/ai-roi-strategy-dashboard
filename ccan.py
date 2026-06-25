import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import textwrap  # Thư viện ép xuống dòng cho văn bản dài để đồ thị đẹp hơn

# ==========================================
# CẤU HÌNH TRANG & ĐỒ HỌA CHUNG
# ==========================================
st.set_page_config(page_title="AI Agent CS Analysis Dashboard", layout="wide")

st.title("📊 Phân Tích & Khuyến Nghị Ứng Dụng AI Agent Trong Ngành Khoa Học Máy Tính")
st.caption("Khung phân tích chiến lược cấp độ tác vụ dựa trên dữ liệu từ người lao động và chuyên gia")

# Cấu hình phong cách đồ thị đồng nhất, hiện đại
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'

# ==========================================
# 1. ĐỌC VÀ CHUẨN HÓA DỮ LIỆU (CÓ CACHE)
# ==========================================
@st.cache_data
def load_and_process_data():
    # Sử dụng chính xác đường dẫn tệp tuyệt đối trên máy của bạn
    df_metadata = pd.read_csv('domain_worker_metadata.csv')
    df_desires = pd.read_csv('domain_worker_desires.csv')
    df_task_statements = pd.read_csv('task_statement_with_metadata.csv')
    df_expert_capability = pd.read_csv('expert_rated_technological_capability.csv')

    # Chuẩn hóa cột lý do thành định dạng Boolean
    bool_cols = [col for col in df_desires.columns if 'Reasons for' in col]
    for col in bool_cols:
        df_desires[col] = df_desires[col].astype(str).str.strip().str.upper() == 'TRUE'
        
    return df_metadata, df_desires, df_task_statements, df_expert_capability

# Gọi hàm tải dữ liệu
df_metadata, df_desires, df_task_statements, df_expert_capability = load_and_process_data()


# ==========================================
# 2. KHỞI TẠO GIAO DIỆN 4 TABS CHIẾN LƯỢC
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 1. Điểm Mù Công Nghệ", 
    "👥 2. Đứt Gãy Thế Hệ", 
    "💰 3. Tối Ưu Hóa ROI", 
    "🛡️ 4. Khung Guardrails"
])

# ------------------------------------------
# TAB 1: ĐIỂM MÙ CÔNG NGHỆ
# ------------------------------------------
with tab1:
    st.header("🎯 Vấn đề 1: Điểm mù giữa năng lực AI và tâm lý kiểm soát")
    st.markdown("*Xác định các tác vụ AI có năng lực tự động hóa cao nhưng nhân viên phản kháng mạnh do nhu cầu kiểm soát.*")
    
    # Xử lý dữ liệu ma trận
    expert_cap = df_expert_capability.groupby('Task ID')['Automation Capacity Rating'].mean().reset_index()
    worker_ctrl = df_desires.groupby('Task ID')[['Automation Desire Rating', 'Reasons for Human Agency - Control', 'Reasons for Human Agency - Quality Oversight']].mean().reset_index()
    problem_1 = pd.merge(expert_cap, worker_ctrl, on='Task ID')
    problem_1 = pd.merge(problem_1, df_task_statements[['Task ID', 'Occupation (O*NET-SOC Title)', 'Task']], on='Task ID', how='left')
    
    # Lọc ra toàn bộ các tác vụ nằm trong "Điểm mù" và sắp xếp giảm dần theo năng lực AI
    blind_spots = problem_1[(problem_1['Automation Capacity Rating'] >= 4.0) & (problem_1['Automation Desire Rating'] <= 2.0)].sort_values(by='Automation Capacity Rating', ascending=False)
    
    col1, col2 = st.columns([1.1, 1])
    
    with col1:
        st.subheader("📋 Toàn bộ các tác vụ rơi vào vùng 'Điểm mù'")
        st.markdown("*(Dữ liệu tương tác hiển thị toàn bộ tác vụ thỏa mãn: Năng lực AI $\ge$ 4.0 và Mong muốn $\le$ 2.0)*")
        st.dataframe(
            blind_spots[['Occupation (O*NET-SOC Title)', 'Task', 'Automation Capacity Rating', 'Automation Desire Rating']], 
            use_container_width=True
        )
        
    with col2:
        st.subheader("📊 Biểu đồ trực quan ma trận Điểm Mù")
        fig, ax = plt.subplots(figsize=(9, 6.2))
        
        # Vẽ các chấm dữ liệu scatter
        sns.scatterplot(data=problem_1, x='Automation Capacity Rating', y='Automation Desire Rating', 
                        hue='Reasons for Human Agency - Control', size='Reasons for Human Agency - Quality Oversight',
                        palette='coolwarm', sizes=(30, 300), alpha=0.75, ax=ax)
        
        ax.axvline(x=3.0, color='gray', linestyle=':', alpha=0.4)
        ax.axhline(y=3.0, color='gray', linestyle=':', alpha=0.4)
        
        # Nổi bật vùng màu đỏ Điểm Mù
        ax.fill_between([4.0, 5.0], 0, 2.0, color='#ffb3b3', alpha=0.35, label='Vùng Điểm Mù Thực Tế')
        rect = plt.Rectangle((4.0, 0), 1.0, 2.0, linewidth=2.5, edgecolor='#cc0000', facecolor='none', linestyle='--')
        ax.add_patch(rect)
        
        ax.text(4.5, 1.0, 'VÙNG ĐIỂM MÙ\n(AI CỰC CAO / MONG MUỐN THẤP)', color='#990000', 
                weight='bold', fontsize=10, ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='none', alpha=0.75))
        
        ax.set_xlim(1.0, 5.2)
        ax.set_ylim(0, 5.2)
        ax.set_xlabel('Năng lực tự động hóa của AI (Chuyên gia chấm)', fontsize=10)
        ax.set_ylabel('Mong muốn tự động hóa (Nhân viên chấm)', fontsize=10)
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
        
        fig.tight_layout()
        st.pyplot(fig)
        
    st.markdown("### 🔍 Chi tiết nội dung công việc của các tác vụ vùng Điểm Mù:")
    with st.expander("✨ Bấm vào đây để mở rộng danh sách chi tiết từng tác vụ (Hỗ trợ đọc báo cáo/thuyết trình)"):
        if not blind_spots.empty:
            st.markdown(f"Hiện tại hệ thống phát hiện có **{len(blind_spots)}** tác vụ rơi vào vùng khủng hoảng tâm lý này:")
            count = 1
            for idx, row in blind_spots.iterrows():
                st.markdown(f"**{count}. Ngành nghề:** `{row['Occupation (O*NET-SOC Title)']}`")
                st.markdown(f"   * **Nội dung tác vụ:** {row['Task']}")
                st.markdown(f"   * ➔ *Đánh giá kỹ thuật:* Năng lực AI đạt **{row['Automation Capacity Rating']:.2f}/5.0** | Mức độ muốn tự động hóa của nhân viên chỉ đạt **{row['Automation Desire Rating']:.2f}/5.0**")
                st.markdown("<div style='border-bottom: 1px dashed #ccc; margin: 10px 0;'></div>", unsafe_allow_html=True)
                count += 1
        else:
            st.info("Không có tác vụ nào nằm trong bộ lọc Điểm Mù của tập dữ liệu hiện tại.")

    st.markdown("### 📑 Khuyến Nghị Chiến Lược Từ Ban Cố Vấn:")
    st.success("""
    **Mô Hình Triển Khai: Hợp Tác Nhân - Trí (Augmentation, không Replacement)**
    * **Tuyệt đối không áp dụng Full Automation:** Đối với danh sách nhóm tác vụ cụ thể ở trên, doanh nghiệp không nên loại bỏ con người ra khỏi quy trình vận hành dù công nghệ của Agent đã hoàn thiện 100%. 
    * **Giải pháp thiết kế giao diện AI tương tác:** Khi xây dựng hệ thống AI Agent, bắt buộc phải tích hợp tính năng giải thích thuật toán (`Explainable AI`). Agent phải hiển thị tường minh các bước suy luận, phân tích lý do đưa ra quyết định để giải tỏa tâm lý lo ngại về mất quyền kiểm soát (`Control`) và hỗ trợ con người dễ dàng thực hiện giám sát chất lượng (`Quality Oversight`).
    * **Giảm tải tâm lý bằng cơ chế phê duyệt:** Giao cho AI Agent làm phần việc 'bếp núc' tốn thời gian nhưng trao toàn quyền bấm nút 'Phê duyệt' (Sign-off) cuối cùng cho nhân viên viên chuyên trách.
    """)

# ------------------------------------------
# TAB 2: ĐỨT GÃY THẾ HỆ LẬP TRÌNH VIÊN (ĐÃ ĐƯỢC SẮP XẾP TĂNG DẦN THEO THÂM NIÊN)
# ------------------------------------------
with tab2:
    st.header("👥 Vấn đề 2: Nguy cơ đứt gãy thế hệ và phân hóa thâm niên")
    st.markdown("*Phân tích xu hướng lạm dụng AI cho việc viết mã nguồn thuần túy ở các kỹ sư trẻ ít kinh nghiệm.*")
    
    df_metadata['Use_AI_Daily_Coding'] = df_metadata['LLM Usage by Type - Coding'] == 'Daily'
    df_metadata['Use_AI_Daily_SysDesign'] = df_metadata['LLM Usage by Type - System Design'] == 'Daily'
    
    # 1. Nhóm dữ liệu theo kinh nghiệm ban đầu
    generation_gap = df_metadata.groupby('Experience')[['Use_AI_Daily_Coding', 'Use_AI_Daily_SysDesign']].mean() * 100
    
    # 🌟 2. CẢI TIẾN: Định nghĩa chính xác cấu trúc thâm niên tăng dần theo dòng thời gian
    experience_chronological_order = [
        'Less than 1 year',
        '1-2 year',
        '1-2 years',
        '3-5 years',
        '6-10 years',
        '10+ years',
        'More than 10 years'
    ]
    
    # Lọc và ép bảng dữ liệu sắp xếp theo đúng thứ tự logic trên
    valid_sort_order = [exp for exp in experience_chronological_order if exp in generation_gap.index]
    unmapped_elements = [exp for exp in generation_gap.index if exp not in valid_sort_order]
    generation_gap = generation_gap.reindex(valid_sort_order + unmapped_elements)
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("Bảng tỷ lệ % sử dụng AI hàng ngày theo nhóm thâm niên (Tăng dần)")
        st.dataframe(generation_gap.round(2), use_container_width=True)
        
    with col2:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        # Biểu đồ tự động vẽ theo thứ tự tăng dần đã được reindex ở trên
        generation_gap.plot(kind='bar', color=['#3498db', '#e74c3c'], width=0.6, ax=ax)
        
        ax.set_ylabel('Tỷ lệ % sử dụng hàng ngày', fontsize=10)
        ax.set_xlabel('Mức Độ Kinh Nghiệm (Thâm niên tăng dần ➔)', fontsize=10)
        plt.xticks(rotation=25, ha='right', fontsize=9)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.legend(["Sử dụng cho Coding", "Sử dụng cho System Design"], loc='upper right')
        
        # Thêm nhãn số trên đầu các cột cho rõ ràng
        for p in ax.patches:
            if p.get_height() > 0:
                ax.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='center', xytext=(0, 8), textcoords='offset points', fontsize=9, weight='bold', color='#2c3e50')
        ax.set_ylim(0, max(generation_gap.max()) * 1.15)
        
        fig.tight_layout()
        st.pyplot(fig)
        
    st.markdown("### 📑 Khuyến Nghị Chiến Lược Từ Ban Cố Vấn:")
    st.warning("""
    **Chiến Lược Quản Trị Nhân Sự & Phát Triển Năng Lực Nội Bộ**
    * **Thiết lập 'Vùng Không AI' (No-AI Zones) cho Junior:** Để ngăn chặn tình trạng kỹ sư trẻ bị rỗng kiến thức nền tảng, quy định trong 6 tháng đầu thử việc, Junior phải giải quyết các bài toán thuật toán cấu trúc dữ liệu hoặc thực hiện gỡ lỗi (`Debugging`) thủ công mà không sử dụng Copilot/ChatGPT.
    * **Tái đào tạo (Reskilling) định hướng Senior sớm:** Chuyển trọng tâm chương trình đào tạo sang: Kỹ nghệ câu lệnh chuyên sâu (`Prompt Engineering`), cách đọc hiểu kiến trúc của các mã nguồn lớn, và tư duy thiết kế hệ thống (`System Design`).
    * **Xây dựng mô hình Cố vấn Cộng tác (Mentorship):** Giao trách nhiệm cho các Senior giám sát và đánh giá cách Junior ứng dụng AI, đảm bảo nhân sự trẻ hiểu bản chất sâu xa của đoạn code do AI sinh ra.
    """)

# ------------------------------------------
# TAB 3: PHÂN BỔ NGÂN SÁCH - ROI AGENT
# ------------------------------------------
with tab3:
    st.header("💰 Vấn đề 3: Phân bổ ngân sách IT tối ưu hóa chỉ số ROI tự động hóa")
    st.markdown("*Lập bản đồ ưu tiên giải ngân dòng vốn vào các tác vụ Core, có tần suất lặp lại lớn thuộc các ngành nghề có quỹ lương cao.*")
    
    df_task_statements['ROI_Score'] = df_task_statements['Frequency'] * df_task_statements['Importance'] * df_task_statements['Occupation Mean Annual Wage']
    high_roi_agents = df_task_statements[df_task_statements['Task Type'] == 'Core'].sort_values(by='ROI_Score', ascending=False)
    
    st.subheader("Bảng phân tích thứ tự ưu tiên đầu tư tài nguyên")
    
    top_roi = high_roi_agents.head(7).copy()
    top_roi['Task_Wrapped'] = [textwrap.fill(text, width=45) for text in top_roi['Task']]
    
    col1, col2 = st.columns([1, 1.4])
    
    with col1:
        st.dataframe(high_roi_agents[['Occupation (O*NET-SOC Title)', 'Task', 'ROI_Score']].head(10), use_container_width=True)
        
    with col2:
        fig, ax = plt.subplots(figsize=(11, 6.5))
        sns.barplot(data=top_roi, x='ROI_Score', y='Task_Wrapped', palette='viridis', ax=ax)
        
        ax.set_xlabel('Điểm Số ROI Tổng Hợp', fontsize=10)
        ax.set_ylabel('Nội Dung Tác Vụ Cốt Lõi', fontsize=10)
        ax.tick_params(axis='y', labelsize=9.5)
        
        fig.tight_layout()
        st.pyplot(fig)
        
    st.markdown("### 📑 Khuyến Nghị Chiến Lược Từ Ban Cố Vấn:")
    st.info("""
    **Khung Kế Hoạch Giải Ngân Tài Chính Theo Tháp Ưu Tiên ROI (Quy Luật 70/30)**
    * **Tập trung 70% ngân sách vào Top 5 tác vụ đứng đầu:** Tránh dàn trải dòng vốn R&D cho các tác vụ phụ. Chỉ cần tự động hóa thành công một phần nhỏ các tác vụ cốt lõi tần suất cao của nhân sự lương cao sẽ đem lại giá trị tài chính thực tế cực lớn.
    * **Chiến lược Tự xây dựng hay Mua ngoài (Build vs Buy):** Đối với các tác vụ nằm ngoài Top 10 hoặc có điểm ROI tổng hợp thấp, nên tích hợp các công cụ SaaS thương mại sẵn có trên thị trường để tiết kiệm tài nguyên hệ thống.
    """)

# ------------------------------------------
# TAB 4: KHUNG GIỚI HẠN TỰ TRỊ (GUARDRAILS)
# ------------------------------------------
with tab4:
    st.header("🛡️ Vấn đề 4: Khung thiết lập giới hạn tự trị (Guardrails Architecture)")
    st.markdown("*Phân định ranh giới hoạt động của AI Agent dựa trên rủi ro không chắc chắn và tác động đạo đức.*")
    
    expert_unc = df_expert_capability.groupby('Task ID')['Involved Uncertainty'].mean().reset_index()
    worker_eth = df_desires.groupby('Task ID')['Reasons for Human Agency - Ethical'].mean().reset_index()
    problem_4 = pd.merge(expert_unc, worker_eth, on='Task ID')
    problem_4_visual = pd.merge(problem_4, df_task_statements[['Task ID', 'Importance']], on='Task ID', how='left')
    
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(data=problem_4_visual, x='Involved Uncertainty', y='Reasons for Human Agency - Ethical',
                    size='Importance', alpha=0.65, sizes=(50, 350), color='#9b59b6', ax=ax)
    
    ax.axhline(y=0.2, color='darkred', linestyle='--', alpha=0.4)
    ax.axvline(x=3.5, color='darkred', linestyle='--', alpha=0.4)
    
    ax.text(0.95, 0.85, 'VÙNG NGUY HIỂM:\nBắt buộc Human-in-the-loop', color='darkred', 
            weight='bold', fontsize=10, transform=ax.transAxes, ha='right',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='darkred', alpha=0.85))
            
    ax.text(0.05, 0.05, 'VÙNG AN TOÀN:\nAgent được phép tự trị', color='green', 
            weight='bold', fontsize=10, transform=ax.transAxes, ha='left',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='green', alpha=0.85))
    
    ax.set_xlabel('Mức Độ Không Chắc Chắn Của Tác Vụ (Involved Uncertainty)', fontsize=10)
    ax.set_ylabel('Tỷ Lệ Lo Ngại Về Đạo Đức Từ Người Lao Động', fontsize=10)
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    
    fig.tight_layout()
    st.pyplot(fig)
        
    st.markdown("### 📑 Khung Quy Định Vận Hành Hệ Thống (Governance Framework):")
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        st.error("""
        🔴 **GIỚI HẠN VÙNG NGUY HIỂM (Uncertainty > 3.5 HOẶC Ethical > 0.2)**
        * **Cơ chế chặn cứng mã nguồn (Hard Guardrails):** AI Agent chỉ được cấp quyền thu thập, xử lý thông tin và lập báo cáo để xem xét phương án. Hệ thống bắt buộc phải tạm dừng quy trình để chờ xác thực mã OTP hoặc chữ ký điện tử phê duyệt thủ công của con người (`Human-in-the-loop`).
        """)
        
    with col_rec2:
        st.success("""
        🟢 **ỦY QUYỀN VÙNG AN TOÀN (Uncertainty ≤ 3.5 VÀ Ethical ≤ 0.2)**
        * **Cơ chế tự trị hoàn toàn (Autonomous Mode):** Cấp quyền cho Agent tự động ra quyết định, tự vận hành theo lịch định sẵn (`Cron-job`) để tối ưu hóa thời gian giải phóng sức lao động. Hệ thống chỉ cần tự động ghi nhận nhật ký hoạt động (`Log file`) cuối ngày.
        """)