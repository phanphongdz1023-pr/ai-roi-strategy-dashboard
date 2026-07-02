import pandas as pd
import streamlit as st

# Chỉ giữ các nghề thuộc lĩnh vực Khoa học máy tính / CNTT
CS_OCCUPATIONS = [
    'Computer Hardware Engineers', 'Computer Network Architects',
    'Computer Network Support Specialists', 'Computer Programmers',
    'Computer Science Teachers, Postsecondary', 'Computer Systems Analysts',
    'Computer Systems Engineers/Architects', 'Computer User Support Specialists',
    'Computer and Information Research Scientists',
    'Computer and Information Systems Managers', 'Database Administrators',
    'Database Architects', 'Information Security Analysts',
    'Information Technology Project Managers',
    'Network and Computer Systems Administrators',
    'Software Quality Assurance Analysts and Testers', 'Web Administrators',
    'Web Developers', 'Data Warehousing Specialists',
]

# Bucket thâm niên: nhóm "Junior" gồm các mốc kinh nghiệm ngắn, "Senior" gồm các mốc dài
SENIOR_LEVELS = {'6-10 years', 'More than 10 years'}


def _bucket_seniority(experience: str) -> str:
    if pd.isna(experience):
        return 'Unknown'
    return 'Senior' if experience in SENIOR_LEVELS else 'Junior'


@st.cache_data  # Lưu cache để không phải load lại data mỗi lần người dùng click
def load_and_process_roi_data():
    """
    Tải 4 nguồn dữ liệu, kết hợp đúng cấp độ (grain) và tính toán chỉ số
    ROI điều chỉnh theo rủi ro (Adjusted_ROI) cho từng tác vụ Core.
    """
    try:
        # 1. Đọc dữ liệu — dùng đúng tên file/tên cột gốc
        task_df = pd.read_csv('task_statement_with_metadata.csv')
        worker_meta_df = pd.read_csv('domain_worker_metadata.csv')
        expert_df = pd.read_csv('expert_rated_technological_capability.csv')
        worker_desire_df = pd.read_csv('domain_worker_desires.csv')

        # 2. Lọc phạm vi: chỉ các nghề CNTT/KHMT, chỉ tác vụ Core
        #    (Task Type là cột chuẩn O*NET, giá trị 'Core' / 'Supplemental')
        task_df = task_df[task_df['Occupation (O*NET-SOC Title)'].isin(CS_OCCUPATIONS)]
        core_tasks = task_df[task_df['Task Type'] == 'Core'].copy()

        # 3. GỘP (AGGREGATE) TRƯỚC KHI MERGE — bắt buộc, vì expert_df và
        #    worker_desire_df là dữ liệu theo từng LƯỢT ĐÁNH GIÁ (nhiều
        #    chuyên gia / nhiều người lao động cùng chấm 1 Task ID).
        #    Không gộp trước sẽ gây fan-out khi inner join.
        expert_agg = (
            expert_df.groupby('Task ID')['Automation Capacity Rating']
            .mean()
            .reset_index()
            .rename(columns={'Automation Capacity Rating': 'expert_score'})
        )

        # 4. Gắn thâm niên (Experience) của người chấm vào từng lượt "desire":
        #    domain_worker_metadata KHÔNG có Task ID (bảng theo User),
        #    nên phải nối desire (có User ID + Task ID) với metadata qua User ID.
        desire_with_seniority = worker_desire_df.merge(
            worker_meta_df[['User ID', 'Experience']],
            on='User ID',
            how='left',
        )
        desire_with_seniority['seniority'] = desire_with_seniority['Experience'].apply(_bucket_seniority)

        # 5. Gộp theo Task ID: điểm ủng hộ trung bình + nhãn thâm niên đa số
        worker_agg = (
            desire_with_seniority.groupby('Task ID')
            .agg(
                worker_support=('Automation Desire Rating', 'mean'),
                seniority=('seniority', lambda s: s.mode().iloc[0] if not s.mode().empty else 'Unknown'),
            )
            .reset_index()
        )

        # 6. Merge dữ liệu đã gộp (1 dòng / Task ID) vào bảng tác vụ Core
        df_merged = core_tasks.merge(expert_agg, on='Task ID', how='inner')
        df_merged = df_merged.merge(worker_agg, on='Task ID', how='inner')

        if df_merged.empty:
            return None

        # 6b. Một số nghề KHÔNG có "Occupation Mean Annual Wage" trong chính
        #     nguồn O*NET gốc (ví dụ: Web Administrators, Information Technology
        #     Project Managers...) — đây là lỗ hổng dữ liệu nguồn, không phải lỗi
        #     merge. Nếu để NaN lọt xuống Base_ROI/Adjusted_ROI, Plotly sẽ crash
        #     ngay ở bước vẽ (size=NaN không hợp lệ). Loại các dòng thiếu dữ liệu
        #     cốt lõi và ghi nhận lại để hiển thị cảnh báo cho người dùng.
        required_cols = ['Occupation Mean Annual Wage', 'Frequency', 'expert_score', 'worker_support']
        before_occs = set(df_merged['Occupation (O*NET-SOC Title)'])
        df_merged = df_merged.dropna(subset=required_cols).copy()
        after_occs = set(df_merged['Occupation (O*NET-SOC Title)'])
        excluded_occs = sorted(before_occs - after_occs)
        if excluded_occs:
            st.warning(
                "Các nghề sau bị loại khỏi biểu đồ ROI vì thiếu dữ liệu lương "
                "(Occupation Mean Annual Wage) trong nguồn O*NET gốc: "
                + ", ".join(excluded_occs)
            )

        if df_merged.empty:
            return None

        # 7. Kỹ nghệ đặc trưng (Feature Engineering)
        #    Base ROI (ROI kinh tế thô, đơn vị USD) = Tần suất x Mức lương — vẫn
        #    giữ lại để tham khảo giá trị kinh tế tuyệt đối.
        df_merged['Base_ROI'] = df_merged['Frequency'] * df_merged['Occupation Mean Annual Wage']

        # Hệ số khả thi công nghệ (Alpha, thang 1-5 -> 0-1)
        df_merged['Tech_Feasibility_Alpha'] = df_merged['expert_score'] / 5.0

        # Hệ số ủng hộ của người lao động (Beta, thang 1-5 -> 0-1)
        df_merged['Worker_Support_Beta'] = df_merged['worker_support'] / 5.0

        # 7b. CHUẨN HÓA GIÁ TRỊ KINH TẾ (khắc phục vấn đề "lương áp đảo"):
        #     Salary dao động ~36.000-360.000 USD (chênh ~10 lần) trong khi Alpha,
        #     Beta chỉ nằm trong [0,1] (chênh tối đa ~6 lần và luôn <=1, nên không
        #     thể "đảo ngược" thứ hạng do lương áp đặt). Hệ quả: nhân trực tiếp
        #     Base_ROI (đơn vị USD) với Alpha, Beta khiến salary gần như quyết định
        #     toàn bộ thứ hạng, làm những tác vụ lương cao nhưng năng lực tự động
        #     hóa thấp (vd. Computer and Information Systems Managers) vẫn đứng đầu,
        #     mâu thuẫn với chính kết luận "cần giữ vai trò con người" ở Tab 1.
        #
        #     Cách sửa: min-max chuẩn hóa salary và frequency về [0,1] TRONG PHẠM VI
        #     tập dữ liệu đang xét, rồi mới kết hợp với Alpha, Beta. Khi đó cả 4 yếu
        #     tố (giá trị kinh tế, tần suất, năng lực công nghệ, mức ủng hộ) đóng góp
        #     công bằng vào điểm ưu tiên cuối cùng.
        def _minmax(s: pd.Series) -> pd.Series:
            lo, hi = s.min(), s.max()
            if hi == lo:
                return pd.Series(1.0, index=s.index)
            return (s - lo) / (hi - lo)

        df_merged['Salary_Index'] = _minmax(df_merged['Occupation Mean Annual Wage'])
        df_merged['Frequency_Index'] = _minmax(df_merged['Frequency'])

        # ĐIỂM ƯU TIÊN CHUẨN HÓA (0-100) — dùng TRUNG BÌNH CỘNG có trọng số bằng
        # nhau (25% mỗi yếu tố: giá trị lương, tần suất, năng lực công nghệ, mức
        # ủng hộ), thay vì nhân trực tiếp. Lý do: phép NHÂN khiến biến nào có phân
        # phối "gập ghềnh" hơn (ví dụ Frequency chỉ có 5 giá trị rời rạc 3-7) vô
        # tình chi phối kết quả sau chuẩn hóa, dù bản thân biến đó không quan trọng
        # hơn các biến còn lại. Trung bình cộng đảm bảo mỗi yếu tố đóng góp đúng
        # 25% bất kể hình dạng phân phối của nó.
        df_merged['Economic_Value_Index'] = (
            df_merged['Salary_Index'] + df_merged['Frequency_Index']
        ) / 2.0  # giữ lại cột này để tham khảo/hiển thị giá trị kinh tế riêng

        df_merged['Priority_Score'] = 100.0 * (
            0.25 * df_merged['Salary_Index']
            + 0.25 * df_merged['Frequency_Index']
            + 0.25 * df_merged['Tech_Feasibility_Alpha']
            + 0.25 * df_merged['Worker_Support_Beta']
        )

        # Vẫn giữ Adjusted_ROI (USD tuyệt đối) để hiển thị tham khảo trong hover,
        # nhưng KHÔNG dùng để xếp hạng/định kích thước bong bóng nữa.
        df_merged['Adjusted_ROI'] = (
            df_merged['Base_ROI']
            * df_merged['Tech_Feasibility_Alpha']
            * df_merged['Worker_Support_Beta']
        )

        # 8. Đổi tên cho khớp với những gì tab3_roi_view.py kỳ vọng
        #    (expert_score, worker_support, seniority đã có sẵn từ bước gộp ở trên)
        df_merged = df_merged.rename(columns={
            'Task': 'task_name',
            'Frequency': 'frequency',
            'Occupation Mean Annual Wage': 'salary',
        })

        df_merged = df_merged.sort_values(by='Priority_Score', ascending=False)

        return df_merged

    except Exception as e:
        st.error(f"Lỗi khi xử lý dữ liệu: {e}")
        return None